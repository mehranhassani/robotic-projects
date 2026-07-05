"""WS2812 / SPI LED strip wrapper with graceful fallback."""

from __future__ import annotations

from enum import Enum

from fnk0043.config import HardwareConfig, use_mock_hardware


class LedMode(str, Enum):
    OFF = "off"
    MANUAL = "manual"
    POLICE = "police"
    FOLLOW = "follow"
    BREATHING = "breathing"
    RAINBOW = "rainbow"


class LedStrip:
    LED_COUNT = 8

    def __init__(self, config: HardwareConfig):
        self._config = config
        self._mode = LedMode.OFF
        self._strip = None
        self._supported = False
        if not use_mock_hardware():
            self._init_hardware()

    def _init_hardware(self) -> None:
        try:
            if self._config.connect_version == 1 and self._config.pi_version == 1:
                from rpi_ws281x import PixelStrip, Color

                self._strip = PixelStrip(self.LED_COUNT, 18, 800000, 10, False, 255, 0)
                self._strip.begin()
                self._supported = True
            elif self._config.connect_version == 2:
                # Freenove ships spi_ledpixel in their repo; optional on Pi
                try:
                    from fnk0043.vendor.spi_ledpixel import Freenove_SPI_LedPixel

                    self._strip = Freenove_SPI_LedPixel(self.LED_COUNT, 255, "GRB")
                    self._supported = True
                except ImportError:
                    pass
        except Exception:
            self._supported = False

    @property
    def supported(self) -> bool:
        return self._supported or use_mock_hardware()

    @property
    def mode(self) -> LedMode:
        return self._mode

    def set_mode(self, mode: LedMode) -> None:
        self._mode = mode
        if mode == LedMode.OFF:
            self.clear()

    def set_pixel_mask(self, index_mask: int, r: int, g: int, b: int) -> None:
        if not self.supported:
            return
        if use_mock_hardware():
            return
        for i in range(self.LED_COUNT):
            if index_mask & (1 << i):
                self._set_pixel(i, r, g, b)
        self._show()

    def clear(self) -> None:
        if not self.supported or use_mock_hardware():
            return
        for i in range(self.LED_COUNT):
            self._set_pixel(i, 0, 0, 0)
        self._show()

    def _set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        if hasattr(self._strip, "set_led_rgb_data"):
            self._strip.set_led_rgb_data(index, (r, g, b))
        elif hasattr(self._strip, "setPixelColor"):
            from rpi_ws281x import Color

            self._strip.setPixelColor(index, Color(r, g, b))

    def _show(self) -> None:
        if hasattr(self._strip, "show"):
            self._strip.show()

    def close(self) -> None:
        self.clear()
