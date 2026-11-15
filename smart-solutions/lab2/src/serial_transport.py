"""Reconnectable newline-delimited JSON transport for one Atom USB owner."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from typing import BinaryIO, TYPE_CHECKING

if TYPE_CHECKING:
    from .station_adapter import StationAdapter


def process_lines(
    lines: Iterable[str | bytes],
    adapter: "StationAdapter",
    *,
    emit: Callable[[str], None],
    log: Callable[[str], None] = print,
) -> None:
    """Process independent lines; one malformed line cannot stop the stream."""
    for raw in lines:
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        text = text.strip()
        if not text:
            continue
        if text.startswith("# "):
            log("[atom-log] " + text[2:])
            continue
        # Receipt first, so the Atom stops resending while a job executes.
        ack = adapter.ack_line(text)
        if ack is not None:
            emit(ack)
        try:
            result = adapter.handle_line(text)
        except Exception as exc:
            log("[station] line processing failed: " + type(exc).__name__)
            continue
        # Keep transport writes outside the parsing guard: a lost serial port
        # must escape to run_serial_forever so it can close and reconnect.
        emit(result)


def _open_serial(port: str, baud: int) -> BinaryIO:
    import serial

    stream = serial.serial_for_url(port, baud, timeout=0.2, do_not_open=True)
    stream.dtr = False
    stream.rts = False
    stream.open()
    return stream


def run_serial_forever(
    port: str,
    baud: int,
    adapter: "StationAdapter",
    *,
    log: Callable[[str], None] = print,
    reconnect_delay: float = 1.0,
) -> None:
    """Own one serial port, reconnect after loss, and emit result JSON lines."""
    import serial

    while True:
        try:
            stream = _open_serial(port, baud)
        except serial.SerialException as exc:
            log(f"[usb] {port} unavailable ({exc}); retrying")
            time.sleep(reconnect_delay)
            continue
        log(f"[usb] {port} open at {baud} baud")

        def lines():
            while True:
                yield stream.readline()

        def emit(result: str) -> None:
            stream.write((result + "\n").encode("utf-8"))
            stream.flush()

        try:
            process_lines(lines(), adapter, emit=emit, log=log)
        except serial.SerialException as exc:
            log(f"[usb] port lost ({exc}); reconnecting")
        finally:
            stream.close()
        time.sleep(reconnect_delay)
