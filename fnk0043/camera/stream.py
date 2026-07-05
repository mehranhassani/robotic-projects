"""Optional Picamera2 MJPEG stream."""

from __future__ import annotations

import io
from threading import Condition

from fnk0043.config import use_mock_hardware


class CameraStream:
    def __init__(self, size: tuple[int, int] = (640, 480)):
        self._size = size
        self._camera = None
        self._streaming = False
        self._frame: bytes | None = None
        self._condition = Condition()

    @property
    def available(self) -> bool:
        return not use_mock_hardware()

    def start(self) -> None:
        if use_mock_hardware() or self._streaming:
            return
        from picamera2 import Picamera2
        from picamera2.encoders import JpegEncoder
        from picamera2.outputs import FileOutput

        class Buffer(io.BufferedIOBase):
            def __init__(self, parent: CameraStream):
                self._parent = parent

            def write(self, buf: bytes) -> int:
                with self._parent._condition:
                    self._parent._frame = buf
                    self._parent._condition.notify_all()
                return len(buf)

        self._camera = Picamera2()
        config = self._camera.create_video_configuration(main={"size": self._size})
        self._camera.configure(config)
        self._camera.start_recording(JpegEncoder(), FileOutput(Buffer(self)))
        self._streaming = True

    def stop(self) -> None:
        if self._camera and self._streaming:
            self._camera.stop_recording()
            self._camera.close()
        self._streaming = False
        self._camera = None

    def get_frame(self, timeout: float = 2.0) -> bytes | None:
        if use_mock_hardware():
            return _placeholder_jpeg()
        with self._condition:
            if not self._condition.wait(timeout):
                return None
            return self._frame

    def close(self) -> None:
        self.stop()


def _placeholder_jpeg() -> bytes:
    # Minimal 1x1 JPEG for mock mode
    return bytes.fromhex(
        "ffd8ffe000104a46494600010100000100010000ffdb004300"
        "080606070605080707070909080a0c140d0c0b0b0c1912130f"
        "141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c303134"
        "34341f27393d38323c2e333432ffdb0043010909090c0b0c18"
        "0d0d1832211c21323232323232323232323232323232323232"
        "32323232323232323232323232323232323232323232323232"
        "323232ffc0001108000100010301110002110003110001ffc4"
        "0014000100000000000000000000000000000008ffc4001410"
        "01000000000000000000000000000000ffda0008010100003f"
        "00d2cf20ffd9"
    )
