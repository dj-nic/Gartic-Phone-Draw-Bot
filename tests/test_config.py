from app.config import AppConfig, ConfigStore, DrawingBoundary


def test_config_store_returns_defaults_for_missing_file(tmp_path):
    config = ConfigStore(tmp_path / "missing.json").load()

    assert config.detail_level == 9
    assert config.draw_mode == "line"
    assert config.drawing_boundary.top_left is None


def test_config_store_returns_defaults_for_invalid_json(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{broken", encoding="utf-8")

    config = ConfigStore(path).load()

    assert config.detail_level == 9


def test_config_store_round_trips_config(tmp_path):
    path = tmp_path / "config.json"
    store = ConfigStore(path)
    expected = AppConfig(
        palette_positions={"Black": {"x": 10, "y": 20}},
        drawing_boundary=DrawingBoundary((1, 2), (3, 4)),
        detail_level=6,
        draw_mode="dot",
        image_source_mode="url",
    )

    store.save(expected)
    actual = store.load()

    assert actual.palette_positions == expected.palette_positions
    assert actual.drawing_boundary.top_left == (1, 2)
    assert actual.drawing_boundary.bottom_right == (3, 4)
    assert actual.detail_level == 6
    assert actual.draw_mode == "dot"
    assert actual.image_source_mode == "url"
