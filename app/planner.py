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
class StrokePath:
    color: PaletteColor
    points: tuple[Point, ...]


@dataclass(frozen=True)
class FillRegion:
    color: PaletteColor
    outline: tuple[StrokeSegment, ...]
    fill_at: Point


@dataclass(frozen=True)
class DrawingPlan:
    strokes: tuple[StrokeSegment, ...]
    paths: tuple[StrokePath, ...]
    fills: tuple[FillRegion, ...]
    fill_enabled: bool
    unsafe_fill_skips: int = 0

    @property
    def operation_count(self) -> int:
        fill_ops = sum(len(region.outline) + 1 for region in self.fills)
        return len(self.strokes) + len(self.paths) + fill_ops


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
    fill_area_threshold: int = 64,
    min_component_area: int = 2,
) -> DrawingPlan:
    strokes: list[StrokeSegment] = []
    paths: list[StrokePath] = []
    fills: list[FillRegion] = []
    unsafe_fill_skips = 0

    for component in connected_components(pixel_colors):
        if component.area < min_component_area:
            continue
        if fill_enabled and _is_safe_fill_component(component, fill_area_threshold):
            fills.append(_component_to_fill_region(component))
        else:
            if fill_enabled and component.area >= fill_area_threshold:
                unsafe_fill_skips += 1
            if _should_draw_as_natural_path(component):
                paths.extend(_component_to_natural_paths(component))
            else:
                paths.extend(_component_to_serpentine_paths(component))

    return DrawingPlan(
        strokes=tuple(strokes),
        paths=tuple(paths),
        fills=tuple(fills),
        fill_enabled=fill_enabled,
        unsafe_fill_skips=unsafe_fill_skips,
    )


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


def _component_to_serpentine_paths(component: Component) -> list[StrokePath]:
    by_row: dict[int, list[int]] = {}
    for x, y in component.points:
        by_row.setdefault(y, []).append(x)

    paths: list[StrokePath] = []
    current_path: list[Point] = []
    previous_row: int | None = None
    previous_end: Point | None = None
    reverse = False

    for y in sorted(by_row):
        runs = _row_runs(sorted(by_row[y]))
        if reverse:
            runs = [(end, start) for start, end in reversed(runs)]

        for start, end in runs:
            run_start = (start, y)
            run_end = (end, y)
            can_connect = (
                previous_row is not None
                and previous_end is not None
                and y == previous_row + 1
                and min(start, end) <= previous_end[0] <= max(start, end)
            )
            if not current_path or not can_connect:
                if len(current_path) >= 2:
                    paths.append(StrokePath(component.color, tuple(current_path)))
                current_path = [run_start]
            elif current_path[-1] != run_start:
                current_path.append(run_start)

            if run_end != current_path[-1]:
                current_path.append(run_end)
            previous_row = y
            previous_end = run_end

        reverse = not reverse

    if len(current_path) >= 2:
        paths.append(StrokePath(component.color, tuple(current_path)))

    return paths


def _should_draw_as_natural_path(component: Component) -> bool:
    min_x, min_y, max_x, max_y = component.bounds
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    if width < 3 or height < 3:
        return False

    density = component.area / (width * height)
    perimeter_hint = max(1, 2 * (width + height))
    return density <= 0.65 or component.area <= perimeter_hint * 2


def _component_to_natural_paths(component: Component) -> list[StrokePath]:
    unvisited = set(component.points)
    paths: list[StrokePath] = []

    while unvisited:
        start = _natural_path_start(unvisited)
        path = [start]
        unvisited.remove(start)
        previous_direction: tuple[int, int] | None = None

        while True:
            next_point = _next_natural_neighbor(path[-1], unvisited, previous_direction)
            if next_point is None:
                break
            previous_direction = (next_point[0] - path[-1][0], next_point[1] - path[-1][1])
            path.append(next_point)
            unvisited.remove(next_point)

        if len(path) > 2 and path[0] in _neighbors8(path[-1]):
            path.append(path[0])

        if len(path) == 1:
            paths.append(StrokePath(component.color, (path[0],)))
        else:
            paths.append(StrokePath(component.color, _simplify_path(path)))

    return paths


def _natural_path_start(points: set[Point]) -> Point:
    endpoints = [point for point in points if _neighbor_count(point, points) <= 1]
    if endpoints:
        return min(endpoints, key=lambda point: (point[1], point[0]))
    return min(points, key=lambda point: (point[1], point[0]))


def _neighbor_count(point: Point, points: set[Point]) -> int:
    return sum(1 for neighbor in _neighbors8(point) if neighbor in points)


def _next_natural_neighbor(
    point: Point,
    candidates: set[Point],
    previous_direction: tuple[int, int] | None,
) -> Point | None:
    neighbors = [neighbor for neighbor in _neighbors8(point) if neighbor in candidates]
    if not neighbors:
        return None
    if previous_direction is None:
        return min(neighbors, key=lambda neighbor: (neighbor[1], neighbor[0]))

    def score(neighbor: Point) -> tuple[int, int, int, int]:
        direction = (neighbor[0] - point[0], neighbor[1] - point[1])
        turn_cost = abs(direction[0] - previous_direction[0]) + abs(direction[1] - previous_direction[1])
        diagonal_cost = 1 if direction[0] and direction[1] else 0
        onward = -_neighbor_count(neighbor, candidates)
        return turn_cost, diagonal_cost, onward, neighbor[1] * 10000 + neighbor[0]

    return min(neighbors, key=score)


def _neighbors8(point: Point) -> tuple[Point, ...]:
    x, y = point
    return (
        (x - 1, y - 1),
        (x, y - 1),
        (x + 1, y - 1),
        (x - 1, y),
        (x + 1, y),
        (x - 1, y + 1),
        (x, y + 1),
        (x + 1, y + 1),
    )


def _simplify_path(points: list[Point]) -> tuple[Point, ...]:
    if len(points) <= 2:
        return tuple(points)

    simplified = [points[0]]
    previous_direction = _point_direction(points[0], points[1])
    for index in range(1, len(points) - 1):
        direction = _point_direction(points[index], points[index + 1])
        if direction != previous_direction:
            simplified.append(points[index])
            previous_direction = direction
    simplified.append(points[-1])
    return tuple(simplified)


def _point_direction(start: Point, end: Point) -> tuple[int, int]:
    return _sign(end[0] - start[0]), _sign(end[1] - start[1])


def _sign(value: int) -> int:
    if value < 0:
        return -1
    if value > 0:
        return 1
    return 0


def _row_runs(xs: list[int]) -> list[tuple[int, int]]:
    if not xs:
        return []
    runs: list[tuple[int, int]] = []
    start = previous = xs[0]
    for x in xs[1:]:
        if x == previous + 1:
            previous = x
            continue
        runs.append((start, previous))
        start = previous = x
    runs.append((start, previous))
    return runs


def _is_safe_fill_component(component: Component, fill_area_threshold: int) -> bool:
    if component.area < fill_area_threshold:
        return False
    min_x, min_y, max_x, max_y = component.bounds
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    if width < 5 or height < 5:
        return False

    bbox_area = width * height
    density = component.area / bbox_area
    if density < 0.92:
        return False

    for x in range(min_x, max_x + 1):
        if (x, min_y) not in component.points or (x, max_y) not in component.points:
            return False
    for y in range(min_y, max_y + 1):
        if (min_x, y) not in component.points or (max_x, y) not in component.points:
            return False
    return True


def _component_to_fill_region(component: Component) -> FillRegion:
    min_x, min_y, max_x, max_y = component.bounds
    outline = (
        StrokeSegment(component.color, (min_x, min_y), (max_x, min_y)),
        StrokeSegment(component.color, (max_x, min_y), (max_x, max_y)),
        StrokeSegment(component.color, (max_x, max_y), (min_x, max_y)),
        StrokeSegment(component.color, (min_x, max_y), (min_x, min_y)),
    )
    return FillRegion(component.color, outline, ((min_x + max_x) // 2, (min_y + max_y) // 2))
