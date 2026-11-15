"""Post-office latency series: N letter jobs, user click -> robot's first movement.

The click time is when this script sends the job to the public post office (the same
request the user page makes). The first movement comes from src.motion_watch, which
must run alongside and append to --motion-csv; both clocks are this PC's wall clock.
Rows are appended to docs/latency_poll_fast.csv or docs/latency_poll_slow.csv.

    python -m src.motion_watch --out data/motion_events.csv        # in another window
    python -m src.latency_series --interval-ms 1000 --out docs/latency_poll_fast.csv

Credentials come from the git-ignored .env (POST_OFFICE_URL / _USER / _PASSWORD).
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LAB2 = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


class PostOffice:
    def __init__(self, url: str, user: str, password: str) -> None:
        self.url = url.rstrip("/")
        self.auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()

    def call(self, path: str, body: dict | None = None) -> dict:
        request = urllib.request.Request(
            self.url + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Authorization": self.auth, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)


def iso(epoch_s: float) -> str:
    return datetime.fromtimestamp(epoch_s, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def first_movement_after(motion_csv: Path, after_ms: float) -> tuple[str, float] | None:
    if not motion_csv.is_file():
        return None
    with motion_csv.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            t = float(row["first_movement_epoch_ms"])
            if t > after_ms:
                return row["first_movement_iso"], t
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--interval-ms", type=int, required=True, help="Atom polling interval set on its page")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--first-trial", type=int, default=1, help="continue a series after a stop")
    parser.add_argument("--letters", default="LAB")
    parser.add_argument("--motion-csv", type=Path, default=LAB2 / "data" / "motion_events.csv")
    parser.add_argument("--job-timeout-s", type=float, default=120.0)
    args = parser.parse_args(argv)

    env = load_env(LAB2 / ".env")
    office = PostOffice(env["POST_OFFICE_URL"], env["POST_OFFICE_USER"], env["POST_OFFICE_PASSWORD"])
    new_file = not args.out.is_file() or args.out.stat().st_size == 0
    with args.out.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["trial", "polling_interval_ms", "job_id", "user_button_timestamp",
                             "robot_first_movement_timestamp", "latency_ms", "result", "note"])
        for trial in range(args.first_trial, args.first_trial + args.trials):
            letter = args.letters[(trial - 1) % len(args.letters)]
            clicked = time.time()
            job = office.call("/api/jobs", {"job": "letter", "arg": {"letter": letter}, "ttl_seconds": 60})
            deadline = time.time() + args.job_timeout_s
            while job["status"] in ("queued", "claimed") and time.time() < deadline:
                time.sleep(0.5)
                job = office.call(f"/api/jobs/{job['id']}")
            moved = first_movement_after(args.motion_csv, clicked * 1000)
            latency = round(moved[1] - clicked * 1000) if moved else ""
            writer.writerow([trial, args.interval_ms, job["id"], iso(clicked),
                             moved[0] if moved else "", latency, job["status"],
                             f"letter {letter}" + ("" if moved else "; no movement seen")])
            handle.flush()
            print(f"{trial:2d} {letter} {job['status']:8s} latency_ms={latency}", flush=True)
            time.sleep(2.0)   # the arm is at rest again before the next click
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
