import io

import pytest

from src.camera_server import build_sources, parse_args
from src.cameras.xiao_camera import XiaoUsbCamera, XiaoUsbCameraConfig

JPEG = b"\xff\xd8" + b"x" * 100 + b"\xff\xd9"


class FakePort:
    def __init__(self, reply: bytes) -> None:
        self.reply, self.written = io.BytesIO(reply), b""

    def reset_input_buffer(self):
        pass

    def write(self, data):
        self.written += data

    def readline(self):
        return self.reply.readline()

    def read(self, n):
        return self.reply.read(n)


def camera():
    return XiaoUsbCamera(XiaoUsbCameraConfig(port="COM5"))


def test_reads_one_jpeg_frame():
    port = FakePort(b"INFO x\nJPG %d\n" % len(JPEG) + JPEG)
    assert camera().capture_frame(port)[0] == JPEG
    assert port.written == b"c"


@pytest.mark.parametrize("reply,message", [
    (b"ERR camera busy\n", "busy"),
    (b"", "no answer"),
    (b"JPG 104\n" + JPEG[:-10], "incomplete"),
])
def test_bad_replies_raise(reply, message):
    with pytest.raises(RuntimeError, match=message):
        camera().capture_frame(FakePort(reply))


def test_cli_selects_usb_source():
    sources = build_sources(parse_args(["--xiao-port", "COM5"]))
    assert isinstance(sources["tool"], XiaoUsbCamera)
    with pytest.raises(SystemExit):
        parse_args(["--xiao-port", "COM5", "--xiao-snapshot-url", "http://x/snapshot.jpg"])
