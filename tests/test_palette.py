from app.palette import GARTIC_PALETTE, ScreenPosition, build_palette_positions, closest_color


def test_closest_color_matches_exact_palette_value():
    assert closest_color((255, 0, 19)).name == "Red"


def test_closest_color_matches_nearby_palette_value():
    assert closest_color((3, 5, 4)).name == "Black"


def test_build_palette_positions_uses_three_column_grid():
    palette = build_palette_positions(
        ScreenPosition(10, 20),
        ScreenPosition(30, 20),
        ScreenPosition(10, 50),
    )

    assert len(palette) == len(GARTIC_PALETTE)
    assert palette[0].position == ScreenPosition(10, 20)
    assert palette[1].position == ScreenPosition(30, 20)
    assert palette[2].position == ScreenPosition(50, 20)
    assert palette[3].position == ScreenPosition(10, 50)
