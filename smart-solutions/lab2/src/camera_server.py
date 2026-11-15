"""Local-only station camera page for Lab 2.

This process is intentionally separate from the public post-office service.
It never talks to the droplet, station job adapter, or robot.
"""

from __future__ import annotations

import argparse
import atexit
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask import Flask, Response, abort, jsonify, send_from_directory, stream_with_context

from .cameras import CameraSource, MockCamera, UsbCamera, UsbCameraConfig, XiaoCamera, XiaoCameraConfig
from .cameras.xiao_camera import XiaoUsbCamera, XiaoUsbCameraConfig

CAMERA_NAMES = ("table", "tool")
STATIC_DIR = Path(__file__).with_name("camera_static")


class CameraRegistry:
    """Own and expose the two station-local camera workers."""

    def __init__(self, sources: Mapping[str, CameraSource]) -> None:
        missing = set(CAMERA_NAMES) - set(sources)
        extra = set(sources) - set(CAMERA_NAMES)
        if missing or extra:
            raise ValueError(f"camera sources must be exactly {CAMERA_NAMES}")
        self.sources = dict(sources)

    def start_all(self) -> None:
        for source in self.sources.values():
            source.start()

    def stop_all(self) -> None:
        for source in self.sources.values():
            source.stop()

    def status(self) -> dict[str, dict[str, object]]:
        return {name: self.sources[name].status() for name in CAMERA_NAMES}


def _source_or_404(registry: CameraRegistry, name: str) -> CameraSource:
    source = registry.sources.get(name)
    if source is None:
        abort(404)
    return source


def create_camera_app(
    sources: Mapping[str, CameraSource], *, start_sources: bool = True
) -> Flask:
    app = Flask(__name__, static_folder=None)
    registry = CameraRegistry(sources)
    app.extensions["camera_registry"] = registry

    if start_sources:
        registry.start_all()

    @app.get("/")
    def index() -> Any:
        return send_from_directory(STATIC_DIR, "index.html")

    @app.get("/api/cameras")
    def camera_status() -> Any:
        return jsonify({"scope": "local_station_only", "cameras": registry.status()})

    @app.get("/snapshot/<name>.jpg")
    def snapshot(name: str) -> Any:
        source = _source_or_404(registry, name)
        frame = source.get_frame(timeout=1.0)
        if frame is None:
            return jsonify({"error": "camera_unavailable", "camera": name}), 503
        source.record_served(len(frame.jpeg))
        return Response(frame.jpeg, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})

    @app.get("/stream/<name>.mjpg")
    def stream(name: str) -> Any:
        source = _source_or_404(registry, name)
        initial = source.get_frame(timeout=1.0)
        if initial is None:
            return jsonify({"error": "camera_unavailable", "camera": name}), 503

        def frames():
            frame = initial
            while frame is not None:
                source.record_served(len(frame.jpeg))
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    + f"Content-Length: {len(frame.jpeg)}\r\n\r\n".encode("ascii")
                    + frame.jpeg
                    + b"\r\n"
                )
                frame = source.get_frame(after_counter=frame.counter, timeout=2.0)

        return Response(
            stream_with_context(frames()),
            mimetype="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-store"},
        )

    return app


def build_sources(args: argparse.Namespace) -> dict[str, CameraSource]:
    if args.mock:
        return {
            "table": MockCamera("table", target_fps=args.fps),
            "tool": MockCamera("tool", target_fps=args.fps),
        }
    try:
        usb_device: int | str = int(args.usb_device)
    except ValueError:
        usb_device = args.usb_device
    return {
        "table": UsbCamera(
            UsbCameraConfig(
                device=usb_device,
                capture_width=args.usb_capture_width,
                capture_height=args.usb_capture_height,
                stream_width=args.stream_width,
                stream_height=args.stream_height,
                target_fps=args.fps,
            )
        ),
        "tool": XiaoUsbCamera(XiaoUsbCameraConfig(port=args.xiao_port, target_fps=args.fps))
        if args.xiao_port
        else XiaoCamera(
            XiaoCameraConfig(
                snapshot_url=args.xiao_snapshot_url,
                expected_width=args.stream_width,
                expected_height=args.stream_height,
                target_fps=args.fps,
            )
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5002)
    parser.add_argument("--mock", action="store_true", help="use two synthetic cameras")
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--usb-device", default="0")
    parser.add_argument("--usb-capture-width", type=int, default=3840)
    parser.add_argument("--usb-capture-height", type=int, default=2160)
    parser.add_argument("--stream-width", type=int, default=1280)
    parser.add_argument("--stream-height", type=int, default=720)
    xiao = parser.add_mutually_exclusive_group()
    xiao.add_argument("--xiao-snapshot-url", default="")
    xiao.add_argument("--xiao-port", default="", help="XIAO over USB serial, e.g. COM5 (no Wi-Fi needed)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    app = create_camera_app(build_sources(args))
    registry: CameraRegistry = app.extensions["camera_registry"]
    atexit.register(registry.stop_all)
    try:
        app.run(host=args.host, port=args.port, threaded=True, debug=False, use_reloader=False)
    finally:
        registry.stop_all()


if __name__ == "__main__":
    main()
