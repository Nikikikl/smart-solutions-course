"""Configurable XIAO ESP32S3 Sense JPEG snapshot client."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable
from urllib.request import Request, urlopen

from .base import CameraSource


@dataclass(frozen=True)
class XiaoCameraConfig:
    snapshot_url: str = ""
    expected_width: int = 0
    expected_height: int = 0
    target_fps: float = 5.0
    request_timeout_s: float = 2.0
    retry_interval_s: float = 2.0
    max_frame_bytes: int = 5_000_000


class XiaoCamera(CameraSource):
    def __init__(
        self,
        config: XiaoCameraConfig,
        *,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        super().__init__(
            "tool",
            target_fps=config.target_fps,
            retry_interval_s=config.retry_interval_s,
        )
        self.config = config
        self._opener = opener

    def open_source(self) -> object:
        if not self.config.snapshot_url:
            raise RuntimeError("XIAO snapshot URL is not configured")
        if not self.config.snapshot_url.startswith(("http://", "https://")):
            raise RuntimeError("XIAO snapshot URL must use HTTP or HTTPS")
        return self

    def capture_frame(self, resource: object) -> tuple[bytes, int, int]:
        request = Request(
            self.config.snapshot_url,
            headers={"Accept": "image/jpeg", "User-Agent": "lab2-local-station/1"},
        )
        response = self._opener(request, timeout=self.config.request_timeout_s)
        try:
            data = response.read(self.config.max_frame_bytes + 1)
        finally:
            close = getattr(response, "close", None)
            if close is not None:
                close()
        if len(data) > self.config.max_frame_bytes:
            raise RuntimeError("XIAO JPEG exceeds configured size limit")
        if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
            raise RuntimeError("XIAO response is not a complete JPEG")
        return data, self.config.expected_width, self.config.expected_height

    def close_source(self, resource: object) -> None:
        return None

    def configuration(self) -> dict[str, object]:
        values = asdict(self.config)
        # A future deployment URL may contain credentials or private query
        # parameters, so status responses expose only whether it is present.
        values.pop("snapshot_url")
        values["snapshot_url_configured"] = bool(self.config.snapshot_url)
        return {"backend": "xiao-http-snapshot", **values}


@dataclass(frozen=True)
class XiaoUsbCameraConfig:
    port: str = ""
    baud: int = 115200
    target_fps: float = 5.0
    read_timeout_s: float = 0.5  # a 13-40 kB frame arrives in <0.1 s; a lost byte must not stall 3 s
    retry_interval_s: float = 0.5
    max_frame_bytes: int = 5_000_000


class XiaoUsbCamera(CameraSource):
    """XIAO over USB serial: 'c' -> "JPG <len>\n" + JPEG (firmware-xiao-camera serviceSerialCommands).

    For a station PC without Wi-Fi. The port has one owner: the 3D hub tool camera
    uses the same protocol, so only one of them may run at a time.
    """

    def __init__(self, config: XiaoUsbCameraConfig, *, serial_module: Any = None) -> None:
        super().__init__("tool", target_fps=config.target_fps, retry_interval_s=config.retry_interval_s)
        self.config = config
        self._serial = serial_module

    def open_source(self) -> object:
        if not self.config.port:
            raise RuntimeError("XIAO USB port is not configured")
        serial = self._serial
        if serial is None:
            import serial  # pyserial
        port = serial.Serial()
        port.port, port.baudrate, port.timeout = self.config.port, self.config.baud, self.config.read_timeout_s
        port.dtr = False  # DTR/RTS toggling resets the ESP32-S3
        port.rts = False
        port.open()
        port.reset_input_buffer()
        return port

    def capture_frame(self, resource: object) -> tuple[bytes, int, int]:
        # A damaged frame is skipped and the next one asked for on the same open
        # port; only repeated failures reach the worker, which reopens the port.
        for attempt in range(3):
            try:
                return self._one_frame(resource)
            except RuntimeError:
                if attempt == 2:
                    raise
        raise AssertionError("unreachable")

    def _one_frame(self, port) -> tuple[bytes, int, int]:
        port.reset_input_buffer()
        port.write(b"c")
        while True:
            line = port.readline().decode("ascii", errors="replace").strip()
            if not line:
                raise RuntimeError("no answer from XIAO")
            if line.startswith("ERR"):
                raise RuntimeError(f"XIAO: {line}")
            if line.startswith("JPG "):
                size = int(line.split()[1])
                break
        if not 0 < size <= self.config.max_frame_bytes:
            raise RuntimeError("XIAO JPEG size out of range")
        data = port.read(size)
        if len(data) != size or not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
            raise RuntimeError("XIAO JPEG incomplete")
        return data, 0, 0

    def close_source(self, resource: object) -> None:
        resource.close()

    def configuration(self) -> dict[str, object]:
        return {"backend": "xiao-usb-serial", **asdict(self.config)}
