"""Atom serial message -> validated high-level executor -> Atom result."""

from __future__ import annotations

import argparse
import json
from contextlib import ExitStack
from pathlib import Path
import sys

import requests

from .executor import (
    Lab1LetterCatalog,
    LetterExecutor,
    MockLetterExecutor,
    MockPickPlaceExecutor,
    PickPlaceExecutor,
)
from .lab1_letter_executor import Lab1LetterExecutor
from .models import (
    AtomLetterJob,
    MessageValidationError,
    StationResult,
    parse_atom_message,
    parse_json_line,
)
from .serial_transport import run_serial_forever
from .station_process_lock import StationLockError, StationProcessLock
from .station_store import StationJobStore


DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "station_jobs.sqlite3"


class StationAdapter:
    def __init__(
        self,
        store: StationJobStore,
        *,
        executor: LetterExecutor | None = None,
        pick_place_executor: PickPlaceExecutor | None = None,
        catalog: Lab1LetterCatalog | None = None,
        local_execution_enabled: bool = False,
        use_lab1_letter_identity: bool = False,
        live_letter_integration: bool = False,
    ) -> None:
        if type(live_letter_integration) is not bool:
            raise ValueError("live letter integration must be explicitly boolean")
        if live_letter_integration:
            if type(executor) is not Lab1LetterExecutor:
                raise ValueError("live letter integration requires Lab1LetterExecutor")
        elif isinstance(executor, Lab1LetterExecutor):
            raise ValueError("Lab1LetterExecutor requires explicit live letter integration")
        self.store = store
        self.executor = executor or MockLetterExecutor()
        self.pick_place_executor = pick_place_executor or MockPickPlaceExecutor()
        self.catalog = catalog or Lab1LetterCatalog()
        self.local_execution_enabled = local_execution_enabled
        self.use_lab1_letter_identity = use_lab1_letter_identity
        self.live_letter_integration = live_letter_integration

    @staticmethod
    def ack_line(line: str | bytes) -> str | None:
        """Delivery receipt for a well-formed job line, sent before execution.

        The Atom resends a job until it sees this receipt (USB CDC on the
        ESP32-S3 can drop bytes). Repeats are safe: the store deduplicates by
        job_id, so a resent job never runs twice.
        """
        try:
            payload, _ = parse_json_line(line)
            job = parse_atom_message(payload)
        except MessageValidationError:
            return None
        return json.dumps({"station_ack": {"id": job.job_id}}, separators=(",", ":"))

    def handle_line(self, line: str | bytes) -> str:
        try:
            payload, _ = parse_json_line(line)
            job = parse_atom_message(payload)
        except MessageValidationError as error:
            return StationResult(error.job_id, "refused", error.reason).to_json_line()

        if isinstance(job, AtomLetterJob):
            if self.live_letter_integration:
                return self._handle_live_letter(job.for_lab1())
            if isinstance(self.executor, Lab1LetterExecutor):
                return StationResult(job.job_id, "refused", "robot_not_enabled").to_json_line()
        if self.use_lab1_letter_identity and isinstance(job, AtomLetterJob):
            job = job.for_lab1()
        decision = self.store.claim(job)
        if decision.action != "execute":
            assert decision.result is not None
            return decision.result.to_json_line()

        if not self.local_execution_enabled:
            result = StationResult(job.job_id, "refused", "robot_not_enabled")
        elif isinstance(job, AtomLetterJob):
            if not self.executor.ready:
                result = StationResult(job.job_id, "refused", "robot_not_enabled")
            elif not self.catalog.supports(job.letter):
                result = StationResult(job.job_id, "refused", "invalid_letter")
            else:
                try:
                    outcome = self.executor.execute_letter(
                        job.letter,
                        job.job_id,
                        session=job.session,
                        seq=job.seq,
                        atom_sent_ms=job.atom_sent_ms,
                    )
                    result = StationResult(job.job_id, outcome.status, outcome.reason)
                except Exception:
                    result = StationResult(job.job_id, "refused", "execution_failed")
        else:
            if not self.pick_place_executor.ready:
                result = StationResult(job.job_id, "refused", "robot_not_enabled")
            else:
                try:
                    outcome = self.pick_place_executor.execute_pick_place(
                        job.routine,
                        job.job_id,
                        session=job.session,
                        seq=job.seq,
                        atom_sent_ms=job.atom_sent_ms,
                    )
                    result = StationResult(job.job_id, outcome.status, outcome.reason)
                except Exception:
                    result = StationResult(job.job_id, "refused", "execution_failed")

        self.store.finish(result)
        return result.to_json_line()

    def _handle_live_letter(self, job: AtomLetterJob) -> str:
        # Recheck the executor boundary in case a caller replaced it after setup.
        if type(self.executor) is not Lab1LetterExecutor:
            return StationResult(job.job_id, "refused", "robot_not_enabled").to_json_line()
        decision = self.store.lookup_live(job)
        if decision is not None:
            assert decision.result is not None
            return decision.result.to_json_line()

        # Reject known non-moving requests without acquiring a live interlock.
        try:
            if self.local_execution_enabled is not True or self.executor.ready is not True:
                return StationResult(job.job_id, "refused", "robot_not_enabled").to_json_line()
            if not self.catalog.supports(job.letter):
                return StationResult(job.job_id, "refused", "invalid_letter").to_json_line()
        except Exception:
            return StationResult(job.job_id, "refused", "execution_failed").to_json_line()

        # claim_live commits and checks the interlock before granting execution.
        decision = self.store.claim_live(job, local_execution_enabled=self.local_execution_enabled)
        if decision.action != "execute":
            assert decision.result is not None
            return decision.result.to_json_line()

        completion_confirmed = False
        try:
            outcome = self.executor.execute_letter(
                job.letter, job.job_id, session=job.session, seq=job.seq,
                atom_sent_ms=job.atom_sent_ms,
            )
            completion_confirmed = (
                outcome.completion_confirmed is True
                and outcome.status == "done" and outcome.reason is None
            )
        except Exception:
            pass
        result = (StationResult(job.job_id, "done") if completion_confirmed
                  else StationResult(job.job_id, "refused", "execution_failed"))
        # Storage errors escape: no terminal answer is emitted before commit.
        self.store.finish(result, completion_confirmed=completion_confirmed)
        return result.to_json_line()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="Atom USB port, for example COM4")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--database", default=str(DEFAULT_DB))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--allow-mock-jobs",
        action="store_true",
        help="allow only the software mock executor; this never enables MG400",
    )
    mode.add_argument(
        "--allow-live-letter", action="store_true",
        help="allow letters through local Lab 1 only, with both operator confirmations",
    )
    parser.add_argument(
        "--confirm-local-safety", action="store_true",
        help="operator is present at the e-stop; robot and calibrated air-test path are locally checked",
    )
    parser.add_argument(
        "--confirm-exclusive-control", action="store_true",
        help="operator has stopped all other command sources; this is not an automatic ownership check",
    )
    parser.add_argument("--lab1-url", default="http://127.0.0.1:5000",
                        help="local Lab 1 endpoint, restricted to http://127.0.0.1:<port>")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    live = args.allow_live_letter is True
    if live and (args.confirm_local_safety is not True or args.confirm_exclusive_control is not True):
        print("[station] live letter requires local safety and exclusive-control confirmations",
              file=sys.stderr)
        return 2
    try:
        # Acquire before SQLite migration/recovery; hold through the entire USB loop.
        with StationProcessLock(args.database) as process_lock, ExitStack() as resources:
            store = StationJobStore(process_lock.database_path)
            if live:
                if store.interlock_job_id() is not None:
                    print("[station] live interlock held; local safety review required", file=sys.stderr)
                    return 1
                session = resources.enter_context(requests.Session())
                executor = Lab1LetterExecutor(args.lab1_url, transport=session)
                print("[station] live LETTER only; operator confirmations do not enforce global MG400 ownership")
            else:
                executor = MockLetterExecutor()
            adapter = StationAdapter(
                store, executor=executor,
                pick_place_executor=MockPickPlaceExecutor(ready=not live),
                local_execution_enabled=live or args.allow_mock_jobs,
                live_letter_integration=live,
            )
            run_serial_forever(args.port, args.baud, adapter)
    except StationLockError:
        print("[station] database process lock unavailable; startup refused", file=sys.stderr)
        return 1
    except ValueError:
        print("[station] invalid local station configuration; startup refused", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
