from __future__ import annotations

import ctypes
import threading
import time
from dataclasses import dataclass
from typing import Callable

import keyboard
import mouse

from app.palette import PaletteColor


StatusCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class DrawRequest:
    pixel_colors: list[list[PaletteColor | None]]
    palette: tuple[PaletteColor, ...]
    top_left: tuple[int, int]
    bottom_right: tuple[int, int]
    mode: str
    game_mode: str = "gartic"


class DrawingBot:
    def __init__(
        self,
        status_callback: StatusCallback | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self._stop_event = threading.Event()
        self._delay_lock = threading.Lock()
        self._delay_ms = 5
        self._status_callback = status_callback or (lambda message: None)
        self._progress_callback = progress_callback or (lambda done, total: None)
        self._scaling_factor = _windows_scaling_factor()

    def set_delay_ms(self, delay_ms: int) -> None:
        with self._delay_lock:
            self._delay_ms = max(0, min(100, int(delay_ms)))

    @property
    def is_stopped(self) -> bool:
        return self._stop_event.is_set()

    def stop(self) -> None:
        self._stop_event.set()
        self._status_callback("Stopping...")

    def reset(self) -> None:
        self._stop_event.clear()

    def draw(self, request: DrawRequest) -> None:
        self.reset()
        _validate_request(request)
        if request.game_mode == "skribbl":
            keyboard.press_and_release("b")
            self._sleep(multiplier=2)
        if request.mode == "dot":
            self._draw_dots(request)
        else:
            self._draw_lines(request)

        if self._stop_event.is_set():
            self._status_callback("Drawing stopped.")
        else:
            self._status_callback("Drawing complete.")

    def _draw_dots(self, request: DrawRequest) -> None:
        width, height, x_step, y_step = _drawing_geometry(request)
        total = width * height
        done = 0
        last_color_name = ""

        for x in range(width):
            for y in range(height):
                if self._stop_event.is_set():
                    return

                color = request.pixel_colors[x][y]
                done += 1
                if color is None:
                    self._report_progress(done, total)
                    continue

                if color.name != last_color_name:
                    self._select_color(color)
                    last_color_name = color.name

                mouse.move(request.top_left[0] + x_step * x, request.top_left[1] + y_step * y, duration=0)
                mouse.click()
                self._progress_callback(done, total)
                self._sleep()

    def _draw_lines(self, request: DrawRequest) -> None:
        width, height, x_step, y_step = _drawing_geometry(request)
        total = width * height
        done = 0

        for x in range(width):
            y = 0
            while y < height:
                if self._stop_event.is_set():
                    return

                color = request.pixel_colors[x][y]
                if color is None:
                    y += 1
                    done += 1
                    self._report_progress(done, total)
                    continue

                start_y = y
                while y + 1 < height and request.pixel_colors[x][y + 1] == color:
                    y += 1

                self._draw_segment(request, color, x, start_y, y, x_step, y_step)
                done += y - start_y + 1
                self._progress_callback(done, total)
                y += 1

    def _draw_segment(
        self,
        request: DrawRequest,
        color: PaletteColor,
        x: int,
        start_y: int,
        end_y: int,
        x_step: float,
        y_step: float,
    ) -> None:
        self._select_color(color)
        start = (request.top_left[0] + x_step * x, request.top_left[1] + y_step * start_y)
        end = (request.top_left[0] + x_step * x, request.top_left[1] + y_step * end_y)
        mouse.move(start[0], start[1], duration=0)
        self._sleep()
        mouse.hold()
        self._sleep()
        mouse.move(end[0], end[1], duration=0)
        self._sleep()
        mouse.release()
        self._sleep()

    def _select_color(self, color: PaletteColor) -> None:
        if color.position is None:
            raise ValueError(f"Missing screen position for palette color: {color.name}")
        mouse.move(
            color.position.x / self._scaling_factor,
            color.position.y / self._scaling_factor,
            duration=0,
        )
        mouse.click()
        self._sleep(multiplier=2)

    def _sleep(self, multiplier: float = 1.0) -> None:
        delay = self._current_delay_seconds() * multiplier
        if delay > 0:
            time.sleep(delay)

    def _current_delay_seconds(self) -> float:
        with self._delay_lock:
            return self._delay_ms / 1000

    def _report_progress(self, done: int, total: int) -> None:
        if done >= total or done % 50 == 0:
            self._progress_callback(done, total)


def _validate_request(request: DrawRequest) -> None:
    if not request.pixel_colors or not request.pixel_colors[0]:
        raise ValueError("No quantized image is loaded.")
    if any(color.position is None for color in request.palette):
        raise ValueError("Palette is not calibrated yet.")
    if request.mode not in {"dot", "line"}:
        raise ValueError("Draw mode must be 'dot' or 'line'.")


def _drawing_geometry(request: DrawRequest) -> tuple[int, int, float, float]:
    width = len(request.pixel_colors)
    height = len(request.pixel_colors[0])
    draw_width = abs(request.bottom_right[0] - request.top_left[0])
    draw_height = abs(request.bottom_right[1] - request.top_left[1])
    return width, height, draw_width / max(width, 1), draw_height / max(height, 1)


def _windows_scaling_factor() -> float:
    try:
        return ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    except Exception:
        return 1.0
