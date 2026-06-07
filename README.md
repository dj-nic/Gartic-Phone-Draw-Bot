# Gartic Phone Draw Bot

A small Windows desktop app that draws local or remote images into Gartic Phone by controlling the mouse.

The app is a rewrite of the original two-script bot into one clean CustomTkinter interface with preview, palette calibration, drawing-area setup, Start/Stop controls, and a reproducible Windows `.exe` build.

Original code by CowCoding0. Fork and improvements by DJ_Nic.

## Features

- One integrated desktop app for image loading, palette calibration, drawing-area setup, and drawing.
- Local image and URL support.
- Gartic palette preview before drawing.
- Dot and line drawing modes.
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
3. Click `Calibrate Palette`.
4. In Gartic Phone, click the black, gray, and white color cells when prompted.
5. Click `Set Drawing Area`.
6. Click the top-left and bottom-right corners of the drawing area.
7. Pick detail level and drawing mode.
8. Keep `Countdown` enabled if you want a short 3-second safety pause before drawing.
9. Raise `Delay` if Gartic misses color changes or line mode drags toward the palette.
10. Click `Start Drawing`.
11. Watch the progress bar and ETA while the bot draws.
12. Press `Esc` or click `Stop` if you need to abort.

The palette and drawing-area settings are saved automatically, so you usually only need to recalibrate when the browser window, zoom, monitor, or Gartic layout changes.

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
  palette.py          Gartic palette and calibration helpers
  ui.py               CustomTkinter desktop app
tests/                Unit tests for non-mouse logic
```

`DrawBot.py` and `GetColorPositions.py` remain as compatibility entry points. Both launch the new integrated app.

## Windows Notes

- Mouse automation may require running the app with the same privilege level as the browser.
- Browser zoom or Windows display scaling can change coordinates. Recalibrate when clicks land in the wrong place.
- Do not move the browser window after setting the drawing area.
- Keep the mouse free while drawing. The app intentionally controls it until drawing finishes or is stopped.
