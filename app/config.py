from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


APP_NAME = "GarticPhoneDrawBot"


@dataclass
class DrawingBoundary:
    top_left: tuple[int, int] | None = None
    bottom_right: tuple[int, int] | None = None

    @property
    def is_ready(self) -> bool:
        return self.top_left is not None and self.bottom_right is not None


@dataclass
class AppConfig:
    palette_positions: dict[str, dict[str, int]] = field(default_factory=dict)
    drawing_boundary: DrawingBoundary = field(default_factory=DrawingBoundary)
    detail_level: int = 9
    draw_delay_ms: int = 25
    start_countdown_seconds: int = 3
    draw_mode: str = "line"
    image_source_mode: str = "file"


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_config_path()

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AppConfig()

        boundary = payload.get("drawing_boundary") or {}
        return AppConfig(
            palette_positions=dict(payload.get("palette_positions") or {}),
            drawing_boundary=DrawingBoundary(
                top_left=_tuple_or_none(boundary.get("top_left")),
                bottom_right=_tuple_or_none(boundary.get("bottom_right")),
            ),
            detail_level=_clamp_int(payload.get("detail_level"), 1, 10, 9),
            draw_delay_ms=_clamp_int(payload.get("draw_delay_ms"), 0, 250, 25),
            start_countdown_seconds=_clamp_int(payload.get("start_countdown_seconds"), 0, 10, 3),
            draw_mode=payload.get("draw_mode") if payload.get("draw_mode") in {"dot", "line"} else "line",
            image_source_mode=(
                payload.get("image_source_mode")
                if payload.get("image_source_mode") in {"file", "url"}
                else "file"
            ),
        )

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")


def default_config_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME / "config.json"
    return Path.home() / f".{APP_NAME}" / "config.json"


def _tuple_or_none(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        return int(value[0]), int(value[1])
    except (TypeError, ValueError):
        return None


def _clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))
