from app.drawing_bot import DrawRequest, DrawingBot
from app.palette import PaletteColor, ScreenPosition


def test_skribbl_mode_selects_brush_before_drawing(monkeypatch):
    pressed_keys: list[str] = []
    mouse_events: list[str] = []
    color = PaletteColor("Black", (0, 0, 0), ScreenPosition(10, 20))
    request = DrawRequest(
        pixel_colors=[[color]],
        palette=(color,),
        top_left=(100, 100),
        bottom_right=(101, 101),
        mode="dot",
        game_mode="skribbl",
    )
    bot = DrawingBot()
    bot.set_delay_ms(0)

    monkeypatch.setattr("app.drawing_bot.keyboard.press_and_release", lambda key: pressed_keys.append(key))
    monkeypatch.setattr("app.drawing_bot.mouse.move", lambda *args, **kwargs: mouse_events.append("move"))
    monkeypatch.setattr("app.drawing_bot.mouse.click", lambda *args, **kwargs: mouse_events.append("click"))

    bot.draw(request)

    assert pressed_keys == ["b"]
    assert "click" in mouse_events


def test_line_mode_drags_between_run_points(monkeypatch):
    mouse_events: list[str] = []
    color = PaletteColor("Black", (0, 0, 0), ScreenPosition(10, 20))
    request = DrawRequest(
        pixel_colors=[[color, color, color]],
        palette=(color,),
        top_left=(100, 100),
        bottom_right=(110, 130),
        mode="line",
    )
    bot = DrawingBot()
    bot.set_delay_ms(0)

    monkeypatch.setattr("app.drawing_bot.mouse.move", lambda *args, **kwargs: mouse_events.append("move"))
    monkeypatch.setattr("app.drawing_bot.mouse.click", lambda *args, **kwargs: mouse_events.append("click"))
    monkeypatch.setattr("app.drawing_bot.mouse.hold", lambda *args, **kwargs: mouse_events.append("hold"))
    monkeypatch.setattr("app.drawing_bot.mouse.release", lambda *args, **kwargs: mouse_events.append("release"))

    bot.draw(request)

    assert "hold" in mouse_events
    assert "release" in mouse_events
    assert mouse_events.index("hold") < mouse_events.index("release")


def test_hybrid_path_draws_with_single_hold_release(monkeypatch):
    mouse_events: list[str] = []
    color = PaletteColor("Black", (0, 0, 0), ScreenPosition(10, 20))
    request = DrawRequest(
        pixel_colors=[[color, color, color]],
        palette=(color,),
        top_left=(100, 100),
        bottom_right=(110, 130),
        mode="hybrid",
        tool_positions={"brush": (20, 20)},
    )
    bot = DrawingBot()
    bot.set_delay_ms(0)

    monkeypatch.setattr("app.drawing_bot.mouse.move", lambda *args, **kwargs: mouse_events.append("move"))
    monkeypatch.setattr("app.drawing_bot.mouse.click", lambda *args, **kwargs: mouse_events.append("click"))
    monkeypatch.setattr("app.drawing_bot.mouse.hold", lambda *args, **kwargs: mouse_events.append("hold"))
    monkeypatch.setattr("app.drawing_bot.mouse.release", lambda *args, **kwargs: mouse_events.append("release"))

    bot.draw(request)

    assert mouse_events.count("hold") == 1
    assert mouse_events.count("release") == 1
