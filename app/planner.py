from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from app.palette import PaletteColor


Grid = list[list[PaletteColor | None]]
Point = tuple[int, int]


@dataclass(frozen=True)
class StrokeSegment:
    color: PaletteColor
    start: Point
    end: Point


@dataclass(frozen=True)
class FillRegion:
    color: PaletteColor
    outline: tuple[StrokeSegment, ...]
    fill_at: Point


@dataclass(frozen=True)
class DrawingPlan:
    strokes: tuple[StrokeSegment, ...]
    fills: tuple[FillRegion, ...]
    fill_enabled: bool

    @property
    def operation_count(self) -> int:
        fill_ops = sum(len(region.outline) + 1 for region in self.fills)
        return len(self.strokes) + fill_ops


@dataclass(frozen=True)
class Component:
    color: PaletteColor
    points: frozenset[Point]

    @property
    def area(self) -> int:
        return len(self.points)

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        xs = [point[0] for point in self.points]
        ys = [point[1] for point in self.points]
        return min(xs), min(ys), max(xs), max(ys)


def build_hybrid_plan(
    pixel_colors: Grid,
    *,
    fill_enabled: bool,
    fill_area_threshold: int = 36,
    min_component_area: int = 2,
) -> DrawingPlan:
    strokes: list[StrokeSegment] = []
    fills: list[FillRegion] = []

    for component in connected_components(pixel_colors):
        if component.area < min_component_area:
            continue
        if fill_enabled and component.area >= fill_area_threshold:
            fills.append(_component_to_fill_region(component))
        else:
            strokes.extend(_component_to_horizontal_strokes(component))

    return DrawingPlan(strokes=tuple(strokes), fills=tuple(fills), fill_enabled=fill_enabled)


def connected_components(pixel_colors: Grid) -> list[Component]:
    if not pixel_colors or not pixel_colors[0]:
        return []

    width = len(pixel_colors)
    height = len(pixel_colors[0])
    seen: set[Point] = set()
    components: list[Component] = []

    for x in range(width):
        for y in range(height):
            if (x, y) in seen:
                continue
            color = pixel_colors[x][y]
            if color is None:
                seen.add((x, y))
                continue
            components.append(_flood_component(pixel_colors, x, y, color, seen, width, height))

    return components


def _flood_component(
    pixel_colors: Grid,
    start_x: int,
    start_y: int,
    color: PaletteColor,
    seen: set[Point],
    width: int,
    height: int,
) -> Component:
    queue: deque[Point] = deque([(start_x, start_y)])
    points: set[Point] = set()
    seen.add((start_x, start_y))

    while queue:
        x, y = queue.popleft()
        points.add((x, y))

        for next_x, next_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if next_x < 0 or next_y < 0 or next_x >= width or next_y >= height:
                continue
            if (next_x, next_y) in seen:
                continue
            if pixel_colors[next_x][next_y] != color:
                continue
            seen.add((next_x, next_y))
            queue.append((next_x, next_y))

    return Component(color=color, points=frozenset(points))


def _component_to_horizontal_strokes(component: Component) -> list[StrokeSegment]:
    by_row: dict[int, list[int]] = {}
    for x, y in component.points:
        by_row.setdefault(y, []).append(x)

    strokes: list[StrokeSegment] = []
    for y, xs in by_row.items():
        sorted_xs = sorted(xs)
        start = previous = sorted_xs[0]
        for x in sorted_xs[1:]:
            if x == previous + 1:
                previous = x
                continue
            strokes.append(StrokeSegment(component.color, (start, y), (previous, y)))
            start = previous = x
        strokes.append(StrokeSegment(component.color, (start, y), (previous, y)))
    return strokes


def _component_to_fill_region(component: Component) -> FillRegion:
    min_x, min_y, max_x, max_y = component.bounds
    outline = (
        StrokeSegment(component.color, (min_x, min_y), (max_x, min_y)),
        StrokeSegment(component.color, (max_x, min_y), (max_x, max_y)),
        StrokeSegment(component.color, (max_x, max_y), (min_x, max_y)),
        StrokeSegment(component.color, (min_x, max_y), (min_x, min_y)),
    )
    return FillRegion(component.color, outline, ((min_x + max_x) // 2, (min_y + max_y) // 2))
