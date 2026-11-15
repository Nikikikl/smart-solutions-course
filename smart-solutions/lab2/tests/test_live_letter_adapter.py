import json
import socket
import sqlite3
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

from src.executor import ExecutionOutcome, MockLetterExecutor, MockPickPlaceExecutor
from src.lab1_letter_executor import Lab1LetterExecutor
from src.models import AtomLetterJob, StationResult, lab1_letter_identity
from src.serial_transport import process_lines
from src.station_adapter import StationAdapter
from src.station_store import StationJobStore


def message(job_id="job-1", **changes):
    payload = dict(letter="A", session="post-office", seq=1, atom_sent_ms=1234, job_id=job_id)
    payload.update(changes)
    return json.dumps(payload)


def decode(line):
    return json.loads(line)["post_office_result"]


def row(store, job_id="job-1"):
    with sqlite3.connect(store.path) as connection:
        connection.row_factory = sqlite3.Row
        found = connection.execute("SELECT * FROM station_jobs WHERE job_id=?", (job_id,)).fetchone()
        return None if found is None else dict(found)


class FakeHTTP:
    """Synthetic responses only; each POST observes the committed SQLite guard."""

    def __init__(self, store, statuses=("started", "completed")):
        self.store = store
        self.statuses = list(statuses)
        self.calls = []
        self.trust_env = True
        self.proxies = {}
        self.auth = None
        self.now = 0.0
        self.on_post = lambda: None

    def mount(self, prefix, adapter):
        assert prefix == "http://" and adapter.max_retries.total == 0

    def sleep(self, duration):
        self.now += duration

    def request(self, method, url, **kwargs):
        self.calls.append(method)
        assert url.startswith("http://127.0.0.1:5000/api/letter")
        assert kwargs["allow_redirects"] is False and self.trust_env is False
        if method == "POST":
            payload = kwargs["json"]
            saved = row(self.store, self.job_id)
            assert saved["state"] == "in_progress"
            assert saved["may_move"] == saved["interlock_held"] == 1
            assert (saved["session"], saved["seq"]) == lab1_letter_identity(self.job_id)
            assert (payload["session"], payload["seq"]) == lab1_letter_identity(self.job_id)
            self.on_post()
            code, body = 202, dict(accepted=True, duplicate=False, dry_run=False,
                                   robot_started=True, letter=payload["letter"], seq=0)
        else:
            assert method == "GET"
            assert kwargs["params"] == dict(zip(("session", "seq"), lab1_letter_identity(self.job_id)))
            state = self.statuses.pop(0)
            if isinstance(state, Exception):
                raise state
            if isinstance(state, tuple):
                code, body = state
            else:
                code, body = 200, dict(ok=True, execution_mode="execute", dry_run=False,
                                       session=lab1_letter_identity(self.job_id)[0], seq=0,
                                       execution_status=state, error=None)

        def read():
            if isinstance(body, Exception):
                raise body
            return body

        return SimpleNamespace(status_code=code, json=read, close=lambda: None)


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    deny = mock.Mock(side_effect=AssertionError("real network is forbidden"))
    monkeypatch.setattr(requests.sessions.Session, "request", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    yield
    deny.assert_not_called()


@pytest.fixture
def store(tmp_path):
    return StationJobStore(tmp_path / "station.sqlite3")


def live_adapter(store, *, statuses=("started", "completed"), job_id="job-1", **changes):
    http = FakeHTTP(store, statuses)
    http.job_id = job_id
    executor = Lab1LetterExecutor("http://127.0.0.1:5000", transport=http,
                                 monotonic=lambda: http.now, sleep=http.sleep,
                                 completion_timeout=1.0)
    options = dict(executor=executor, local_execution_enabled=True, live_letter_integration=True)
    options.update(changes)
    return StationAdapter(store, **options), http


def test_claim_post_get_finish_order_and_confirmed_success(store, monkeypatch):
    adapter, http = live_adapter(store)
    finish = store.finish

    def record_finish(result, *, completion_confirmed=False):
        assert http.calls == ["POST", "GET", "GET"]
        assert completion_confirmed is True and result.status == "done"
        assert row(store)["state"] == "in_progress" and store.interlock_job_id() == "job-1"
        finish(result, completion_confirmed=completion_confirmed)

    monkeypatch.setattr(store, "finish", record_finish)
    assert decode(adapter.handle_line(message())) == dict(id="job-1", status="done")
    assert row(store)["state"] == "done" and row(store)["interlock_held"] == 0


@pytest.mark.parametrize("statuses", [
    ["failed"], [requests.Timeout()], [requests.ConnectionError()], [(404, {})], [(503, {})],
    [(200, ValueError("synthetic malformed JSON"))], [(200, [])], ["unknown"],
    ["started"] * 4,
    [(200, dict(ok=True, execution_mode="dry-run", dry_run=True))],
])
def test_failure_keeps_interlock_and_replay_never_posts_again(store, statuses):
    adapter, http = live_adapter(store, statuses=statuses)
    result = adapter.handle_line(message())
    assert decode(result) == dict(id="job-1", status="refused", reason="execution_failed")
    assert row(store)["state"] == "refused" and store.interlock_job_id() == "job-1"
    assert http.calls.count("POST") == 1
    assert adapter.handle_line(message()) == result
    blocked = decode(adapter.handle_line(message("job-2")))
    assert blocked["reason"] == "executor_busy" and http.calls.count("POST") == 1
    restarted = StationJobStore(store.path)
    second, unused = live_adapter(restarted)
    assert second.handle_line(message()) == result
    assert unused.calls == [] and restarted.interlock_job_id() == "job-1"


@pytest.mark.parametrize("incident", ["exception", "unconfirmed_done"])
def test_executor_exception_or_unconfirmed_done_is_persisted_refusal(store, monkeypatch, incident):
    adapter, http = live_adapter(store)

    def execute(*args, **kwargs):
        assert store.interlock_job_id() == "job-1"
        if incident == "exception":
            raise RuntimeError("synthetic executor failure")
        return ExecutionOutcome.done()

    monkeypatch.setattr(adapter.executor, "execute_letter", execute)
    assert decode(adapter.handle_line(message()))["reason"] == "execution_failed"
    assert store.get("job-1") == StationResult("job-1", "refused", "execution_failed")
    assert store.interlock_job_id() == "job-1" and http.calls == []


def test_success_replay_after_atom_replacement_and_restart_even_when_disabled(store):
    adapter, http = live_adapter(store)
    result = adapter.handle_line(message())
    changed = json.loads(message())
    changed.update(session="replacement-atom", seq=999, atom_sent_ms=1)
    assert adapter.handle_line(json.dumps(changed)) == result
    restarted = StationJobStore(store.path)
    second, unused = live_adapter(restarted, local_execution_enabled=False)
    assert second.handle_line(json.dumps(changed)) == result
    assert unused.calls == [] and http.calls.count("POST") == 1
    changed["letter"] = "L"
    assert decode(second.handle_line(json.dumps(changed)))["reason"] == "duplicate_conflict"


def test_restart_with_unfinished_job_refuses_without_post_and_keeps_lock(store):
    job = AtomLetterJob("A", "original", 1, "job-1").for_lab1()
    assert store.claim_live(job, local_execution_enabled=True).action == "execute"
    restarted = StationJobStore(store.path)
    adapter, http = live_adapter(restarted)
    assert decode(adapter.handle_line(message()))["reason"] == "ambiguous_after_restart"
    assert http.calls == [] and restarted.interlock_job_id() == "job-1"


def test_different_job_ids_with_same_atom_sequence_execute_under_distinct_keys(store):
    first, http1 = live_adapter(store)
    second, http2 = live_adapter(store, job_id="job-2")
    assert decode(first.handle_line(message()))["status"] == "done"
    assert decode(second.handle_line(message("job-2")))["status"] == "done"
    assert row(store)["session"] != row(store, "job-2")["session"]
    assert http1.calls.count("POST") == http2.calls.count("POST") == 1


def test_competing_request_cannot_post_while_first_sequence_is_active(store):
    adapter, http = live_adapter(store)
    contender, other = live_adapter(store, job_id="job-2")
    http.on_post = lambda: assert_busy(contender.handle_line(message("job-2")))
    assert decode(adapter.handle_line(message()))["status"] == "done"
    assert other.calls == [] and row(store, "job-2") is None


def assert_busy(line):
    assert decode(line)["reason"] == "executor_busy"


@pytest.mark.parametrize("gate", ["disabled", "not_ready", "unsupported"])
def test_admission_checks_do_not_create_interlock_or_post(store, monkeypatch, gate):
    adapter, http = live_adapter(store, local_execution_enabled=gate != "disabled")
    if gate == "not_ready":
        monkeypatch.setattr(Lab1LetterExecutor, "ready", property(lambda self: False))
    if gate == "unsupported":
        monkeypatch.setattr(adapter.catalog, "supports", lambda letter: False)
    result = decode(adapter.handle_line(message()))
    assert result["reason"] == ("invalid_letter" if gate == "unsupported" else "robot_not_enabled")
    assert row(store) is None and store.interlock_job_id() is None and http.calls == []


@pytest.mark.parametrize("operation", ["lookup_live", "claim_live"])
def test_sqlite_error_before_execution_never_posts(store, monkeypatch, operation):
    adapter, http = live_adapter(store)
    monkeypatch.setattr(store, operation, mock.Mock(side_effect=sqlite3.OperationalError("synthetic error")))
    with pytest.raises(sqlite3.OperationalError):
        adapter.handle_line(message())
    assert http.calls == [] and row(store) is None


def test_finish_transaction_error_emits_no_done_and_restart_does_not_repeat(store):
    adapter, http = live_adapter(store)
    with sqlite3.connect(store.path) as connection:
        connection.execute("""CREATE TRIGGER fail_finish BEFORE UPDATE OF state ON station_jobs
                              WHEN NEW.state='done' BEGIN SELECT RAISE(ABORT, 'synthetic fault'); END""")
    emitted = []
    process_lines([message()], adapter, emit=emitted.append, log=lambda value: None)
    assert emitted == ['{"station_ack":{"id":"job-1"}}'] and row(store)["state"] == "in_progress"
    assert store.interlock_job_id() == "job-1" and http.calls.count("POST") == 1
    second, unused = live_adapter(StationJobStore(store.path))
    assert decode(second.handle_line(message()))["reason"] == "ambiguous_after_restart"
    assert unused.calls == [] and store.interlock_job_id() == "job-1"


def test_recovery_failure_stops_before_adapter_or_http(store):
    job = AtomLetterJob("A", "original", 1, "job-1").for_lab1()
    store.claim_live(job, local_execution_enabled=True)
    with sqlite3.connect(store.path) as connection:
        connection.execute("""CREATE TRIGGER fail_recovery BEFORE UPDATE OF state ON station_jobs
                              BEGIN SELECT RAISE(ABORT, 'synthetic fault'); END""")
    with pytest.raises(sqlite3.DatabaseError):
        live_adapter(StationJobStore(store.path))
    assert store.interlock_job_id() == "job-1"


def test_mock_cannot_enable_live_and_live_executor_requires_explicit_mode(store):
    with pytest.raises(ValueError):
        StationAdapter(store, executor=MockLetterExecutor(), live_letter_integration=True)
    adapter, http = live_adapter(store)
    with pytest.raises(ValueError):
        StationAdapter(store, executor=adapter.executor, local_execution_enabled=True)
    adapter.executor = MockLetterExecutor()
    assert decode(adapter.handle_line(message()))["reason"] == "robot_not_enabled"
    assert adapter.executor.calls == [] and http.calls == []
    assert row(store) is None


def test_mock_terminal_done_cannot_be_replayed_as_live_completion(store):
    mock_adapter = StationAdapter(store, local_execution_enabled=True)
    assert decode(mock_adapter.handle_line(message()))["status"] == "done"
    adapter, http = live_adapter(store)
    assert decode(adapter.handle_line(message()))["reason"] == "duplicate_conflict"
    assert http.calls == [] and row(store)["may_move"] == 0


def test_default_adapter_cannot_use_http_executor_inserted_after_setup(store):
    live, http = live_adapter(store)
    adapter = StationAdapter(store, local_execution_enabled=True)
    adapter.executor = live.executor
    assert decode(adapter.handle_line(message()))["reason"] == "robot_not_enabled"
    assert http.calls == [] and row(store) is None


def test_invalid_wire_letter_never_claims_or_posts(store):
    adapter, http = live_adapter(store)
    assert decode(adapter.handle_line(message(letter="AB")))["reason"] == "invalid_letter"
    assert http.calls == [] and row(store) is None


@pytest.mark.parametrize("allow_mock", [False, True])
def test_cli_only_constructs_mock_executor_and_never_live_http(store, monkeypatch, allow_mock):
    import src.station_adapter as module

    def serial_stub(port, baud, adapter):
        assert type(adapter.executor) is MockLetterExecutor
        assert adapter.live_letter_integration is False
        result = decode(adapter.handle_line(message()))
        assert result["status"] == ("done" if allow_mock else "refused")

    monkeypatch.setattr(module, "parse_args", lambda: SimpleNamespace(
        database=store.path, port="synthetic-not-a-device", baud=115200, allow_mock_jobs=allow_mock,
        allow_live_letter=False, confirm_local_safety=False, confirm_exclusive_control=False,
        lab1_url="http://127.0.0.1:5000"))
    monkeypatch.setattr(module, "run_serial_forever", serial_stub)
    assert module.main() == 0


def test_pick_place_keeps_software_mock_path_in_live_letter_adapter(store):
    adapter, http = live_adapter(store)
    payload = json.loads(message())
    payload.pop("letter")
    payload.update(job="pick_place", routine="source_to_finished")
    assert decode(adapter.handle_line(json.dumps(payload)))["status"] == "done"
    assert type(adapter.pick_place_executor) is MockPickPlaceExecutor
    assert adapter.pick_place_executor.hardware_used is False
    assert row(store)["may_move"] == row(store)["interlock_held"] == 0
    assert http.calls == []
