from app.palette import PaletteColor
from app.planner import build_hybrid_plan, connected_components


BLACK = PaletteColor("Black", (0, 0, 0))
RED = PaletteColor("Red", (255, 0, 0))


def test_connected_components_groups_same_neighbor_colors():
    grid = [
        [BLACK, BLACK, None],
        [None, BLACK, RED],
        [RED, None, RED],
    ]

    components = connected_components(grid)

    assert sorted(component.area for component in components) == [1, 2, 3]


def test_hybrid_plan_uses_fill_for_large_components_when_enabled():
    grid = [[BLACK for _ in range(8)] for _ in range(8)]

    plan = build_hybrid_plan(grid, fill_enabled=True, fill_area_threshold=10)

    assert len(plan.fills) == 1
    assert len(plan.strokes) == 0
    assert len(plan.paths) == 0
    assert plan.operation_count == 5


def test_hybrid_plan_falls_back_to_strokes_without_fill():
    grid = [[BLACK for _ in range(8)] for _ in range(8)]

    plan = build_hybrid_plan(grid, fill_enabled=False, fill_area_threshold=10)

    assert len(plan.fills) == 0
    assert len(plan.paths) == 1
    assert plan.operation_count == 1


def test_hybrid_plan_reduces_operations_compared_to_dot_mode():
    grid = [[BLACK for _ in range(8)] for _ in range(8)]

    plan = build_hybrid_plan(grid, fill_enabled=True, fill_area_threshold=10)

    assert plan.operation_count < 64


def test_hybrid_plan_skips_fill_for_unsafe_sparse_shape():
    grid = [[None for _ in range(8)] for _ in range(8)]
    for index in range(8):
        grid[index][0] = BLACK
        grid[0][index] = BLACK

    plan = build_hybrid_plan(grid, fill_enabled=True, fill_area_threshold=4)

    assert len(plan.fills) == 0
    assert plan.unsafe_fill_skips == 1
    assert len(plan.paths) == 1
