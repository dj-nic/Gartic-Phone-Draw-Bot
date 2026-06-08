from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class ScreenPosition:
    x: int
    y: int


@dataclass(frozen=True)
class PaletteColor:
    name: str
    rgb: tuple[int, int, int]
    position: ScreenPosition | None = None

    def with_position(self, x: int, y: int) -> "PaletteColor":
        return PaletteColor(self.name, self.rgb, ScreenPosition(int(x), int(y)))


GARTIC_PALETTE: tuple[PaletteColor, ...] = (
    PaletteColor("Black", (0, 0, 0)),
    PaletteColor("Gray", (102, 102, 102)),
    PaletteColor("Blue", (0, 80, 205)),
    PaletteColor("White", (255, 255, 255)),
    PaletteColor("Light Gray", (170, 170, 170)),
    PaletteColor("Light Blue", (38, 201, 201)),
    PaletteColor("Green", (1, 116, 32)),
    PaletteColor("Brown", (105, 21, 6)),
    PaletteColor("Light Brown", (150, 65, 18)),
    PaletteColor("Light Green", (17, 176, 60)),
    PaletteColor("Red", (255, 0, 19)),
    PaletteColor("Orange", (255, 120, 41)),
    PaletteColor("Ugly Brown", (176, 112, 28)),
    PaletteColor("Purple", (153, 0, 78)),
    PaletteColor("Skin Color", (203, 90, 87)),
    PaletteColor("Yellow", (255, 193, 38)),
    PaletteColor("Pink", (255, 0, 143)),
    PaletteColor("Light Pink", (254, 175, 168)),
)

SKRIBBL_PALETTE: tuple[PaletteColor, ...] = (
    PaletteColor("White", (255, 255, 255)),
    PaletteColor("Light Gray", (193, 193, 193)),
    PaletteColor("Red", (239, 19, 11)),
    PaletteColor("Orange", (255, 113, 0)),
    PaletteColor("Yellow", (255, 228, 0)),
    PaletteColor("Green", (0, 204, 0)),
    PaletteColor("Mint", (0, 255, 145)),
    PaletteColor("Skyblue", (0, 178, 255)),
    PaletteColor("Seablue", (0, 86, 158)),
    PaletteColor("Pruple", (163, 0, 186)),
    PaletteColor("Pink", (223, 105, 167)),
    PaletteColor("Beige", (255, 172, 142)),
    PaletteColor("Borwn", (160, 82, 45)),
    PaletteColor("Black", (0, 0, 0)),
    PaletteColor("Gray", (76, 76, 76)),
    PaletteColor("Dark Red", (116, 11, 7)),
    PaletteColor("Dark Orange", (194, 56, 0)),
    PaletteColor("Dark Yellow", (232, 162, 0)),
    PaletteColor("Dark Green", (0, 85, 16)),
    PaletteColor("Dark mint", (0, 178, 93)),
    PaletteColor("Dark Skyblue", (0, 86, 158)),
    PaletteColor("Dark Seablue", (35, 31, 211)),
    PaletteColor("Dark Purple", (14, 8, 101)),
    PaletteColor("Dark Pink", (167, 85, 116)),
    PaletteColor("Dark Beige", (204, 119, 77)),
    PaletteColor("Dark Brown", (99, 48, 13)),
)

GAME_PALETTES: dict[str, tuple[PaletteColor, ...]] = {
    "gartic": GARTIC_PALETTE,
    "skribbl": SKRIBBL_PALETTE,
}


def closest_color(rgb: tuple[int, int, int], palette: tuple[PaletteColor, ...] = GARTIC_PALETTE) -> PaletteColor:
    return min(palette, key=lambda color: color_distance(rgb, color.rgb))


def color_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
    return sqrt(
        pow(left[0] - right[0], 2)
        + pow(left[1] - right[1], 2)
        + pow(left[2] - right[2], 2)
    )


def build_palette_positions(
    black_position: ScreenPosition,
    gray_position: ScreenPosition,
    white_position: ScreenPosition,
    palette: tuple[PaletteColor, ...] = GARTIC_PALETTE,
) -> tuple[PaletteColor, ...]:
    x_offset = abs(black_position.x - gray_position.x)
    y_offset_step = abs(black_position.y - white_position.y)
    positioned: list[PaletteColor] = []
    row_offset = 0

    for index, color in enumerate(palette):
        column = index % 3
        x = black_position.x + x_offset * column
        y = black_position.y + row_offset
        positioned.append(color.with_position(x, y))

        if column == 2:
            row_offset += y_offset_step

    return tuple(positioned)


def build_palette_from_clicks(
    positions: list[ScreenPosition],
    palette: tuple[PaletteColor, ...],
) -> tuple[PaletteColor, ...]:
    if len(positions) != len(palette):
        raise ValueError(f"Expected {len(palette)} color positions, got {len(positions)}.")
    return tuple(color.with_position(position.x, position.y) for color, position in zip(palette, positions))


def palette_from_config(
    positions: dict[str, dict[str, int]],
    palette: tuple[PaletteColor, ...] = GARTIC_PALETTE,
) -> tuple[PaletteColor, ...]:
    result: list[PaletteColor] = []
    for color in palette:
        position = positions.get(color.name)
        if position is None:
            result.append(color)
        else:
            result.append(color.with_position(position["x"], position["y"]))
    return tuple(result)


def palette_to_config(palette: tuple[PaletteColor, ...]) -> dict[str, dict[str, int]]:
    return {
        color.name: {"x": color.position.x, "y": color.position.y}
        for color in palette
        if color.position is not None
    }
