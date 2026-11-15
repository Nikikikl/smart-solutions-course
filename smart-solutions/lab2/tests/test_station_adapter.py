import json
import sqlite3

from src.e2e_demo import run_demo
from src.executor import MockLetterExecutor, MockPickPlaceExecutor
from src.models import AtomPickPlaceJob, StationResult, parse_atom_message
from src.serial_transport import process_lines
from src.station_adapter import StationAdapter
from src.station_store import StationJobStore


def atom_payload(job_id="job-1", letter="A", session="post-office", seq=1, **extra):
    payload = {
        "letter": letter,
        "session": session,
        "seq": seq,
        "atom_sent_ms": 1234,
        "job_id": job_id,
    }
    payload.update(extra)
    return payload


def pick_place_payload(
    job_id="job-pick-1",
    routine="source_to_finished",
    session="post-office",
    seq=2,
    **extra,
):
    payload = {
        "job": "pick_place",
        "routine": routine,
        "session": session,
        "seq": seq,
        "atom_sent_ms": 1234,
        "job_id": job_id,
    }
    payload.update(extra)
    return payload


def decode(line):
    return json.loads(line)["post_office_result"]


def make_adapter(tmp_path, *, executor=None, pick_place_executor=None, enabled=True):
    selected = executor or MockLetterExecutor()
    return (
        StationAdapter(
            StationJobStore(tmp_path / "station.sqlite3"),
            executor=selected,
            pick_place_executor=pick_place_executor,
            local_execution_enabled=enabled,
        ),
        selected,
    )


def test_valid_pick_place_message_uses_software_mock(tmp_path):
    pick_executor = MockPickPlaceExecutor()
    adapter, _ = make_adapter(tmp_path, pick_place_executor=pick_executor)
    result = decode(adapter.handle_line(json.dumps(pick_place_payload())))
    assert result == {"id": "job-pick-1", "status": "done"}
    assert [job.routine for job in pick_executor.calls] == ["source_to_finished"]
    assert pick_executor.hardware_used is False


def test_invalid_pick_place_routine_is_refused(tmp_path):
    pick_executor = MockPickPlaceExecutor()
    adapter, _ = make_adapter(tmp_path, pick_place_executor=pick_executor)
    result = decode(adapter.handle_line(json.dumps(pick_place_payload(routine="other"))))
    assert result["reason"] == "invalid_routine"
    assert pick_executor.calls == []


def test_malformed_pick_place_serial_job_is_refused(tmp_path):
    adapter, _ = make_adapter(tmp_path)
    payload = pick_place_payload()
    payload.pop("routine")
    result = decode(adapter.handle_line(json.dumps(payload)))
    assert result["reason"] == "invalid_routine"


def test_pick_place_coordinates_are_refused(tmp_path):
    pick_executor = MockPickPlaceExecutor()
    adapter, _ = make_adapter(tmp_path, pick_place_executor=pick_executor)
    result = decode(adapter.handle_line(json.dumps(pick_place_payload(x=10))))
    assert result["reason"] == "invalid_message"
    assert pick_executor.calls == []


def test_unknown_serial_job_is_refused(tmp_path):
    adapter, _ = make_adapter(tmp_path)
    result = decode(
        adapter.handle_line(json.dumps(pick_place_payload(job="move_robot")))
    )
    assert result["reason"] == "unknown_job"


def test_valid_letter_message_is_accepted(tmp_path):
    adapter, executor = make_adapter(tmp_path)
    result = decode(adapter.handle_line(json.dumps(atom_payload())))
    assert result == {"id": "job-1", "status": "done"}
    assert [job.letter for job in executor.calls] == ["A"]


def test_invalid_json_is_refused(tmp_path):
    adapter, _ = make_adapter(tmp_path)
    result = decode(adapter.handle_line("{not-json"))
    assert result == {"id": "", "status": "refused", "reason": "invalid_message"}


def test_missing_job_id_is_refused(tmp_path):
    adapter, _ = make_adapter(tmp_path)
    payload = atom_payload()
    payload.pop("job_id")
    result = decode(adapter.handle_line(json.dumps(payload)))
    assert result["status"] == "refused"
    assert result["reason"] == "invalid_message"


def test_invalid_letter_is_refused(tmp_path):
    adapter, executor = make_adapter(tmp_path)
    result = decode(adapter.handle_line(json.dumps(atom_payload(letter="AB"))))
    assert result == {"id": "job-1", "status": "refused", "reason": "invalid_letter"}
    assert executor.calls == []


def test_catalog_has_every_letter_lab1_can_draw():
    from src.executor import Lab1LetterCatalog

    catalog = Lab1LetterCatalog()
    assert all(catalog.supports(chr(c)) for c in range(ord("A"), ord("Z") + 1))
    assert not Lab1LetterCatalog(font_path=None).supports("C")   # letters.json alone: A, L, N


def test_direct_motion_fields_are_refused(tmp_path):
    adapter, executor = make_adapter(tmp_path)
    result = decode(adapter.handle_line(json.dumps(atom_payload(x=10, speed=20))))
    assert result == {"id": "job-1", "status": "refused", "reason": "invalid_message"}
    assert executor.calls == []


def test_duplicate_job_id_returns_same_terminal_result(tmp_path):
    adapter, executor = make_adapter(tmp_path)
    line = json.dumps(atom_payload())
    first = adapter.handle_line(line)
    second = adapter.handle_line(line)
    assert second == first
    assert len(executor.calls) == 1


def test_conflicting_reuse_of_job_id_is_refused(tmp_path):
    adapter, executor = make_adapter(tmp_path)
    assert decode(adapter.handle_line(json.dumps(atom_payload(letter="A"))))["status"] == "done"
    conflict = decode(adapter.handle_line(json.dumps(atom_payload(letter="L"))))
    assert conflict["reason"] == "duplicate_conflict"
    assert len(executor.calls) == 1


def test_session_seq_duplicate_does_not_reexecute(tmp_path):
    adapter, executor = make_adapter(tmp_path)
    adapter.handle_line(json.dumps(atom_payload(job_id="job-1")))
    duplicate = decode(adapter.handle_line(json.dumps(atom_payload(job_id="job-2"))))
    assert duplicate == {
        "id": "job-2",
        "status": "refused",
        "reason": "duplicate_conflict",
    }
    assert len(executor.calls) == 1


def test_mock_executor_success_becomes_done(tmp_path):
    adapter, _ = make_adapter(tmp_path, executor=MockLetterExecutor())
    assert decode(adapter.handle_line(json.dumps(atom_payload())))["status"] == "done"


def test_mock_executor_refusal_is_stable(tmp_path):
    executor = MockLetterExecutor(refusals={"A": "robot_not_enabled"})
    adapter, _ = make_adapter(tmp_path, executor=executor)
    result = decode(adapter.handle_line(json.dumps(atom_payload())))
    assert result["status"] == "refused"
    assert result["reason"] == "robot_not_enabled"


def test_executor_failure_becomes_stable_refusal(tmp_path):
    adapter, _ = make_adapter(tmp_path, executor=MockLetterExecutor(failures={"A"}))
    result = decode(adapter.handle_line(json.dumps(atom_payload())))
    assert result["reason"] == "execution_failed"
    assert decode(adapter.handle_line(json.dumps(atom_payload()))) == result


def test_restart_persistence_prevents_terminal_replay(tmp_path):
    database = tmp_path / "station.sqlite3"
    first_executor = MockLetterExecutor()
    first = StationAdapter(
        StationJobStore(database), executor=first_executor, local_execution_enabled=True
    )
    line = json.dumps(atom_payload())
    expected = first.handle_line(line)

    second_executor = MockLetterExecutor()
    restarted = StationAdapter(
        StationJobStore(database), executor=second_executor, local_execution_enabled=True
    )
    assert restarted.handle_line(line) == expected
    assert len(first_executor.calls) == 1
    assert second_executor.calls == []


def test_duplicate_pick_place_is_not_executed_twice(tmp_path):
    pick_executor = MockPickPlaceExecutor()
    adapter, _ = make_adapter(tmp_path, pick_place_executor=pick_executor)
    line = json.dumps(pick_place_payload())
    assert adapter.handle_line(line) == adapter.handle_line(line)
    assert len(pick_executor.calls) == 1


def test_pick_place_terminal_result_survives_restart(tmp_path):
    database = tmp_path / "station.sqlite3"
    line = json.dumps(pick_place_payload())
    first_executor = MockPickPlaceExecutor()
    first = StationAdapter(
        StationJobStore(database),
        pick_place_executor=first_executor,
        local_execution_enabled=True,
    )
    expected = first.handle_line(line)
    restarted_executor = MockPickPlaceExecutor()
    restarted = StationAdapter(
        StationJobStore(database),
        pick_place_executor=restarted_executor,
        local_execution_enabled=True,
    )
    assert restarted.handle_line(line) == expected
    assert len(first_executor.calls) == 1
    assert restarted_executor.calls == []


def test_pick_place_restart_ambiguity_refuses_replay(tmp_path):
    database = tmp_path / "station.sqlite3"
    job = parse_atom_message(pick_place_payload())
    assert isinstance(job, AtomPickPlaceJob)
    assert StationJobStore(database).claim(job).action == "execute"
    pick_executor = MockPickPlaceExecutor()
    restarted = StationAdapter(
        StationJobStore(database),
        pick_place_executor=pick_executor,
        local_execution_enabled=True,
    )
    result = decode(restarted.handle_line(json.dumps(pick_place_payload())))
    assert result["reason"] == "ambiguous_after_restart"
    assert pick_executor.calls == []


def test_existing_letter_store_is_migrated_without_replay(tmp_path):
    database = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TABLE station_jobs (
                job_id TEXT PRIMARY KEY,
                letter TEXT NOT NULL,
                session TEXT NOT NULL,
                seq INTEGER NOT NULL,
                atom_sent_ms INTEGER,
                state TEXT NOT NULL,
                reason TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(session, seq)
            );
            INSERT INTO station_jobs VALUES
                ('legacy-job', 'A', 'post-office', 1, 1234, 'done', NULL, 'old');
            """
        )
    store = StationJobStore(database)
    job = parse_atom_message(atom_payload(job_id="legacy-job"))
    decision = store.claim(job)
    assert decision.action == "cached"
    assert decision.result == StationResult("legacy-job", "done")


def test_ambiguous_in_progress_job_is_refused_after_restart(tmp_path):
    database = tmp_path / "station.sqlite3"
    job = parse_atom_message(atom_payload())
    assert StationJobStore(database).claim(job).action == "execute"

    executor = MockLetterExecutor()
    restarted = StationAdapter(
        StationJobStore(database), executor=executor, local_execution_enabled=True
    )
    result = decode(restarted.handle_line(json.dumps(atom_payload())))
    assert result["reason"] == "ambiguous_after_restart"
    assert executor.calls == []


def test_malformed_serial_line_does_not_stop_processing(tmp_path):
    adapter, executor = make_adapter(tmp_path)
    emitted = []
    process_lines(
        [b"{broken\n", (json.dumps(atom_payload()) + "\n").encode()],
        adapter,
        emit=emitted.append,
        log=lambda _: None,
    )
    assert decode(emitted[0])["reason"] == "invalid_message"
    assert json.loads(emitted[1]) == {"station_ack": {"id": atom_payload()["job_id"]}}
    assert decode(emitted[2])["status"] == "done"
    assert len(executor.calls) == 1


def test_ack_precedes_result_and_resent_job_runs_once(tmp_path):
    """The Atom resends until it sees station_ack; a resend must not run twice."""
    adapter, executor = make_adapter(tmp_path)
    line = (json.dumps(atom_payload()) + "\n").encode()
    emitted = []
    process_lines([line, line], adapter, emit=emitted.append, log=lambda _: None)
    job_id = atom_payload()["job_id"]
    acks = [json.loads(e) for e in emitted if "station_ack" in e]
    results = [decode(e) for e in emitted if "station_ack" not in e]
    assert acks == [{"station_ack": {"id": job_id}}] * 2
    assert json.loads(emitted[0]) == {"station_ack": {"id": job_id}}
    assert [r["status"] for r in results] == ["done", "done"]
    assert len(executor.calls) == 1


def test_no_ack_for_corrupted_job_line(tmp_path):
    """Bytes dropped by USB CDC give invalid JSON or ids: never acknowledged."""
    adapter, executor = make_adapter(tmp_path)
    corrupted = '{"letter":"A","session":"post-officeeq":tom_sent_ms":198896,"job_id":"0303ab"}'
    emitted = []
    process_lines([corrupted], adapter, emit=emitted.append, log=lambda _: None)
    assert all("station_ack" not in e for e in emitted)
    assert executor.calls == []


def test_default_mode_does_not_call_executor_or_mg400(tmp_path):
    executor = MockLetterExecutor()
    adapter, _ = make_adapter(tmp_path, executor=executor, enabled=False)
    result = decode(adapter.handle_line(json.dumps(atom_payload())))
    assert result["reason"] == "robot_not_enabled"
    assert executor.calls == []


def test_default_mode_does_not_run_pick_place_mock(tmp_path):
    pick_executor = MockPickPlaceExecutor()
    adapter, _ = make_adapter(
        tmp_path, pick_place_executor=pick_executor, enabled=False
    )
    result = decode(adapter.handle_line(json.dumps(pick_place_payload())))
    assert result["reason"] == "robot_not_enabled"
    assert pick_executor.calls == []


def test_result_json_contains_stable_job_id(tmp_path):
    adapter, _ = make_adapter(tmp_path)
    result = decode(adapter.handle_line(json.dumps(atom_payload(job_id="stable-123"))))
    assert result["id"] == "stable-123"


def test_second_job_is_refused_while_first_is_in_progress(tmp_path):
    store = StationJobStore(tmp_path / "station.sqlite3")
    assert store.claim(parse_atom_message(atom_payload(job_id="job-1"))).action == "execute"
    adapter = StationAdapter(store, executor=MockLetterExecutor(), local_execution_enabled=True)
    result = decode(
        adapter.handle_line(json.dumps(atom_payload(job_id="job-2", session="other", seq=2)))
    )
    assert result["reason"] == "executor_busy"


def test_result_model_matches_firmware_envelope():
    line = StationResult("stable-id", "refused", "execution_failed").to_json_line()
    assert decode(line) == {
        "id": "stable-id",
        "status": "refused",
        "reason": "execution_failed",
    }


def test_end_to_end_post_office_station_demo(tmp_path):
    result = run_demo(tmp_path)
    for job_type in ("letter", "pick_place"):
        job = result[job_type]
        assert job["station_result"]["id"] == job["job_id"]
        assert job["station_result"]["status"] == "done"
        assert job["server_status"] == "done"
        assert job["hardware_used"] is False
    assert result["hardware_used"] is False
    assert result["mock_pick_place_calls"] == 1
