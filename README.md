# Gartic Phone Draw Bot

A small Windows desktop app that draws local or remote images into Gartic Phone by controlling the mouse.

The app is a rewrite of the original two-script bot into one clean CustomTkinter interface with preview, palette calibration, drawing-area setup, Start/Stop controls, and a reproducible Windows `.exe` build.

Original code by CowCoding0. Fork and improvements by DJ_Nic.

## Features

- One integrated desktop app for image loading, palette calibration, drawing-area setup, and drawing.
- Gartic Phone and Skribbl.io modes with separate saved calibration data.
- Local image and URL support.
- Game palette preview before drawing.
- Dot and line drawing modes.
- Gartic hybrid mode that reduces mouse spam with planned strokes and optional fill operations.
- Live delay slider to slow down clicks and drags while drawing.
- ETA display next to the progress bar while drawing.
- Optional start countdown so you can release the mouse before drawing begins.
- Persistent settings in `%APPDATA%/GarticPhoneDrawBot/config.json`.
- `Esc` and the Stop button abort drawing.
- GitHub Actions workflow for a portable Windows executable.

## Download

Open the latest GitHub Actions run for this repository and download the `GarticPhoneDrawBot-windows` artifact. It contains:

```text
GarticPhoneDrawBot.exe
```

Run the `.exe` on Windows. The app does not need an installer.

## Usage

1. Start `GarticPhoneDrawBot.exe`.
2. Choose `file` or `url`, then load an image.
3. Pick `gartic` or `skribbl`.
4. Click `Calibrate Palette`.
5. For Gartic Phone, click black, gray, and white when prompted. For Skribbl.io, click every color from left to right when prompted.
6. For Gartic hybrid mode, click `Calibrate Tools`, then click the brush and fill tools when prompted.
7. Click `Set Drawing Area`.
8. Click the top-left and bottom-right corners of the drawing area.
9. Pick detail level and drawing mode.
10. Keep `Countdown` enabled if you want a short 3-second safety pause before drawing.
11. Raise `Delay` if the game misses color changes or line mode drags toward the palette.
12. Click `Start Drawing`.
13. Watch the progress bar and ETA while the bot draws.
14. Press `Esc` or click `Stop` if you need to abort.

Palette and drawing-area settings are saved separately per game. You usually only need to recalibrate when the browser window, zoom, monitor, or game layout changes.

## Gartic Hybrid Mode

`hybrid` is the recommended Gartic mode. It plans fewer drawing operations by grouping connected pixels into longer strokes. Large color regions use a simple outline plus fill when the Gartic fill tool has been calibrated. If the fill tool is missing, hybrid mode falls back to brush-only strokes.

## Skribbl.io Mode

Skribbl.io uses its own palette and shortcuts. Calibrate the palette by clicking the visible color buttons from left to right. Before drawing starts, the app sends `B` once to select the brush tool.

## Development

Create a virtual environment, install dependencies, and start the app:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app
```

Run tests:

```powershell
pip install pytest
pytest
```

Build the portable executable locally:

```powershell
pyinstaller GarticPhoneDrawBot.spec --noconfirm --clean
```

The executable is written to:

```text
dist/GarticPhoneDrawBot.exe
```

## Project Structure

```text
app/
  config.py           AppData JSON config loading/saving
  drawing_bot.py      Mouse automation core
  image_processor.py  Image loading, resizing, and palette preview
  palette.py          Game palettes and calibration helpers
  ui.py               CustomTkinter desktop app
tests/                Unit tests for non-mouse logic
```

`DrawBot.py` and `GetColorPositions.py` remain as compatibility entry points. Both launch the new integrated app.

## Windows Notes

- Mouse automation may require running the app with the same privilege level as the browser.
- Browser zoom or Windows display scaling can change coordinates. Recalibrate when clicks land in the wrong place.
- Do not move the browser window after setting the drawing area.
- Keep the mouse free while drawing. The app intentionally controls it until drawing finishes or is stopped.
