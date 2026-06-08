import json

from app.config import AppConfig, ConfigStore, DrawingBoundary, GameConfig, active_game_config


def test_config_store_returns_defaults_for_missing_file(tmp_path):
    config = ConfigStore(tmp_path / "missing.json").load()

    assert config.detail_level == 9
    assert config.draw_delay_ms == 25
    assert config.start_countdown_seconds == 3
    assert config.draw_mode == "line"
    assert config.game_mode == "gartic"
    assert active_game_config(config).drawing_boundary.top_left is None


def test_config_store_returns_defaults_for_invalid_json(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{broken", encoding="utf-8")

    config = ConfigStore(path).load()

    assert config.detail_level == 9


def test_config_store_round_trips_config(tmp_path):
    path = tmp_path / "config.json"
    store = ConfigStore(path)
    expected = AppConfig(
        game_mode="skribbl",
        game_configs={
            "gartic": GameConfig(
                palette_positions={"Black": {"x": 10, "y": 20}},
                drawing_boundary=DrawingBoundary((1, 2), (3, 4)),
            ),
            "skribbl": GameConfig(
                palette_positions={"White": {"x": 100, "y": 200}},
                drawing_boundary=DrawingBoundary((5, 6), (7, 8)),
            ),
        },
        detail_level=6,
        draw_delay_ms=80,
        start_countdown_seconds=0,
        draw_mode="dot",
        image_source_mode="url",
    )

    store.save(expected)
    actual = store.load()

    assert actual.game_mode == "skribbl"
    assert actual.game_configs["gartic"].palette_positions == {"Black": {"x": 10, "y": 20}}
    assert actual.game_configs["gartic"].drawing_boundary.top_left == (1, 2)
    assert actual.game_configs["skribbl"].palette_positions == {"White": {"x": 100, "y": 200}}
    assert active_game_config(actual).drawing_boundary.bottom_right == (7, 8)
    assert actual.detail_level == 6
    assert actual.draw_delay_ms == 80
    assert actual.start_countdown_seconds == 0
    assert actual.draw_mode == "dot"
    assert actual.image_source_mode == "url"


def test_config_store_migrates_legacy_gartic_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "palette_positions": {"Black": {"x": 10, "y": 20}},
                "drawing_boundary": {"top_left": [1, 2], "bottom_right": [3, 4]},
            }
        ),
        encoding="utf-8",
    )

    config = ConfigStore(path).load()

    assert config.game_mode == "gartic"
    assert config.game_configs["gartic"].palette_positions == {"Black": {"x": 10, "y": 20}}
    assert config.game_configs["gartic"].drawing_boundary.top_left == (1, 2)
    assert config.game_configs["skribbl"].palette_positions == {}
