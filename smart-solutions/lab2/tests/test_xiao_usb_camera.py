import io

import pytest

from src.camera_server import build_sources, parse_args
from src.cameras.xiao_camera import XiaoUsbCamera, XiaoUsbCameraConfig

JPEG = b"\xff\xd8" + b"x" * 100 + b"\xff\xd9"


class FakePort:
    """Answers each 'c' with the next reply, like the XIAO does."""

    def __init__(self, *replies: bytes) -> None:
        self.replies, self.reply, self.written = list(replies), io.BytesIO(), b""

    def reset_input_buffer(self):
        self.reply = io.BytesIO()

    def write(self, data):
        self.written += data
        self.reply = io.BytesIO(self.replies.pop(0) if self.replies else b"")

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
        camera().capture_frame(FakePort(reply, reply, reply))


def test_damaged_frame_is_skipped_on_the_same_port():
    good = b"JPG %d\n" % len(JPEG) + JPEG
    port = FakePort(b"JPG 104\n" + JPEG[:50], good)
    assert camera().capture_frame(port)[0] == JPEG
    assert port.written == b"cc"


def test_cli_selects_usb_source():
    sources = build_sources(parse_args(["--xiao-port", "COM5"]))
    assert isinstance(sources["tool"], XiaoUsbCamera)
    with pytest.raises(SystemExit):
        parse_args(["--xiao-port", "COM5", "--xiao-snapshot-url", "http://x/snapshot.jpg"])
