from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
import keyboard
import mouse
from PIL import Image

from app.config import AppConfig, ConfigStore
from app.drawing_bot import DrawRequest, DrawingBot
from app.image_processor import ImageProcessor, QuantizedImage
from app.palette import ScreenPosition, build_palette_positions, palette_from_config, palette_to_config


class GarticDrawBotApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Gartic Phone Draw Bot")
        self.geometry("1040x720")
        self.minsize(940, 640)

        self.store = ConfigStore()
        self.config_model = self.store.load()
        self.palette = palette_from_config(self.config_model.palette_positions)
        self.processor = ImageProcessor(self.palette)
        self.bot = DrawingBot(self._post_status, self._post_progress)
        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.loaded_image: Image.Image | None = None
        self.quantized_image: QuantizedImage | None = None
        self.selected_file: Path | None = None
        self.draw_thread: threading.Thread | None = None
        self.preview_photo: ctk.CTkImage | None = None

        self._build_ui()
        self._load_config_to_ui()
        keyboard.add_hotkey("esc", self.stop_drawing)
        self.after(100, self._drain_messages)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, width=340)
        left.grid(row=0, column=0, sticky="nsw", padx=16, pady=16)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left, text="Gartic Phone Draw Bot", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 8)
        )

        self.source_mode = ctk.StringVar(value="file")
        ctk.CTkSegmentedButton(
            left,
            values=["file", "url"],
            variable=self.source_mode,
            command=lambda _: self._sync_source_controls(),
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=8)

        self.file_button = ctk.CTkButton(left, text="Choose Image", command=self.choose_file)
        self.file_button.grid(row=2, column=0, sticky="ew", padx=16, pady=6)
        self.url_entry = ctk.CTkEntry(left, placeholder_text="https://example.com/image.png")
        self.url_entry.grid(row=3, column=0, sticky="ew", padx=16, pady=6)
        ctk.CTkButton(left, text="Load Image", command=self.load_image).grid(row=4, column=0, sticky="ew", padx=16, pady=6)

        self.detail_slider = ctk.CTkSlider(left, from_=1, to=10, number_of_steps=9, command=self._on_detail_change)
        self.detail_label = ctk.CTkLabel(left, text="Detail: 9")
        self.detail_label.grid(row=5, column=0, sticky="w", padx=16, pady=(18, 2))
        self.detail_slider.grid(row=6, column=0, sticky="ew", padx=16, pady=4)

        self.draw_mode = ctk.StringVar(value="line")
        ctk.CTkSegmentedButton(left, values=["line", "dot"], variable=self.draw_mode).grid(
            row=7, column=0, sticky="ew", padx=16, pady=12
        )

        ctk.CTkButton(left, text="Calibrate Palette", command=self.calibrate_palette).grid(
            row=8, column=0, sticky="ew", padx=16, pady=6
        )
        ctk.CTkButton(left, text="Test Palette", command=self.test_palette).grid(
            row=9, column=0, sticky="ew", padx=16, pady=6
        )
        ctk.CTkButton(left, text="Set Drawing Area", command=self.set_drawing_area).grid(
            row=10, column=0, sticky="ew", padx=16, pady=6
        )

        ctk.CTkButton(left, text="Start Drawing", fg_color="#2e7d32", command=self.start_drawing).grid(
            row=11, column=0, sticky="ew", padx=16, pady=(18, 6)
        )
        ctk.CTkButton(left, text="Stop", fg_color="#b3261e", command=self.stop_drawing).grid(
            row=12, column=0, sticky="ew", padx=16, pady=6
        )

        self.status_label = ctk.CTkLabel(left, text="Ready", anchor="w", wraplength=290)
        self.status_label.grid(row=13, column=0, sticky="ew", padx=16, pady=(18, 6))
        self.progress = ctk.CTkProgressBar(left)
        self.progress.grid(row=14, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.progress.set(0)

        ctk.CTkLabel(right, text="Preview", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 8)
        )
        self.preview_label = ctk.CTkLabel(right, text="Load an image to see the Gartic palette preview.")
        self.preview_label.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        self.info_label = ctk.CTkLabel(right, text="", anchor="w")
        self.info_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))

        self._sync_source_controls()

    def _load_config_to_ui(self) -> None:
        self.source_mode.set(self.config_model.image_source_mode)
        self.draw_mode.set(self.config_model.draw_mode)
        self.detail_slider.set(self.config_model.detail_level)
        self._on_detail_change(self.config_model.detail_level)
        self._sync_source_controls()

    def choose_file(self) -> None:
        filename = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All files", "*.*")]
        )
        if filename:
            self.selected_file = Path(filename)
            self.file_button.configure(text=self.selected_file.name)
            self.load_image()

    def load_image(self) -> None:
        try:
            if self.source_mode.get() == "url":
                self.loaded_image = self.processor.load_url(self.url_entry.get().strip())
            else:
                if self.selected_file is None:
                    self._set_status("Choose an image file first.")
                    return
                self.loaded_image = self.processor.load_file(self.selected_file)
            self._refresh_preview()
            self._save_preferences()
        except Exception as exc:
            self._set_status(f"Image load failed: {exc}")

    def calibrate_palette(self) -> None:
        threading.Thread(target=self._calibrate_palette_worker, daemon=True).start()

    def test_palette(self) -> None:
        threading.Thread(target=self._test_palette_worker, daemon=True).start()

    def set_drawing_area(self) -> None:
        threading.Thread(target=self._drawing_area_worker, daemon=True).start()

    def start_drawing(self) -> None:
        if self.draw_thread and self.draw_thread.is_alive():
            self._set_status("Drawing is already running.")
            return
        if self.quantized_image is None:
            self._set_status("Load an image first.")
            return
        if not self.config_model.drawing_boundary.is_ready:
            self._set_status("Set the drawing area first.")
            return

        request = DrawRequest(
            pixel_colors=self.quantized_image.pixel_colors,
            palette=self.palette,
            top_left=self.config_model.drawing_boundary.top_left or (0, 0),
            bottom_right=self.config_model.drawing_boundary.bottom_right or (0, 0),
            mode=self.draw_mode.get(),
        )
        self._save_preferences()
        self.draw_thread = threading.Thread(target=self._run_draw, args=(request,), daemon=True)
        self.draw_thread.start()

    def stop_drawing(self) -> None:
        self.bot.stop()

    def _refresh_preview(self) -> None:
        if self.loaded_image is None:
            return
        self.processor = ImageProcessor(self.palette)
        self.quantized_image = self.processor.quantize(self.loaded_image, int(self.detail_slider.get()))
        self.preview_photo = ctk.CTkImage(
            light_image=self.quantized_image.preview,
            dark_image=self.quantized_image.preview,
            size=(360, 360),
        )
        self.preview_label.configure(image=self.preview_photo, text="")
        self.info_label.configure(
            text=f"Source: {self.loaded_image.width}x{self.loaded_image.height} | "
            f"Draw grid: {len(self.quantized_image.pixel_colors)}x{len(self.quantized_image.pixel_colors[0])}"
        )
        self._set_status("Preview ready.")

    def _calibrate_palette_worker(self) -> None:
        try:
            self._post_status("Click black color.")
            mouse.wait(mouse.LEFT, mouse.DOWN)
            black = mouse.get_position()
            self._post_status("Click gray color.")
            mouse.wait(mouse.LEFT, mouse.DOWN)
            gray = mouse.get_position()
            self._post_status("Click white color.")
            mouse.wait(mouse.LEFT, mouse.DOWN)
            white = mouse.get_position()

            self.palette = build_palette_positions(
                ScreenPosition(*black),
                ScreenPosition(*gray),
                ScreenPosition(*white),
            )
            self.config_model.palette_positions = palette_to_config(self.palette)
            self.store.save(self.config_model)
            self._post_status("Palette calibrated and saved.")
            if self.loaded_image is not None:
                self.messages.put(("refresh_preview", None))
        except Exception as exc:
            self._post_status(f"Calibration failed: {exc}")

    def _test_palette_worker(self) -> None:
        try:
            missing = [color.name for color in self.palette if color.position is None]
            if missing:
                self._post_status("Calibrate the palette first.")
                return
            for color in self.palette:
                if color.position is None:
                    continue
                mouse.move(color.position.x, color.position.y, duration=0)
                mouse.click()
                mouse.move(color.position.x + 220, color.position.y, duration=0)
                mouse.click()
            self._post_status("Palette test complete.")
        except Exception as exc:
            self._post_status(f"Palette test failed: {exc}")

    def _drawing_area_worker(self) -> None:
        try:
            self._post_status("Click top-left drawing corner.")
            mouse.wait(mouse.LEFT, mouse.DOWN)
            top_left = mouse.get_position()
            self._post_status("Click bottom-right drawing corner.")
            mouse.wait(mouse.LEFT, mouse.DOWN)
            bottom_right = mouse.get_position()
            self.config_model.drawing_boundary.top_left = (int(top_left[0]), int(top_left[1]))
            self.config_model.drawing_boundary.bottom_right = (int(bottom_right[0]), int(bottom_right[1]))
            self.store.save(self.config_model)
            self._post_status("Drawing area saved.")
        except Exception as exc:
            self._post_status(f"Drawing area failed: {exc}")

    def _run_draw(self, request: DrawRequest) -> None:
        try:
            self._post_status("Drawing started. Press Esc to stop.")
            self.bot.draw(request)
        except Exception as exc:
            self._post_status(f"Drawing failed: {exc}")

    def _on_detail_change(self, value: float | int) -> None:
        self.detail_label.configure(text=f"Detail: {int(float(value))}")
        if self.loaded_image is not None:
            self._refresh_preview()

    def _sync_source_controls(self) -> None:
        if self.source_mode.get() == "url":
            self.url_entry.configure(state="normal")
            self.file_button.configure(state="disabled")
        else:
            self.url_entry.configure(state="disabled")
            self.file_button.configure(state="normal")

    def _save_preferences(self) -> None:
        self.config_model.detail_level = int(self.detail_slider.get())
        self.config_model.draw_mode = self.draw_mode.get()
        self.config_model.image_source_mode = self.source_mode.get()
        self.store.save(self.config_model)

    def _post_status(self, message: str) -> None:
        self.messages.put(("status", message))

    def _post_progress(self, done: int, total: int) -> None:
        self.messages.put(("progress", (done, total)))

    def _set_status(self, message: str) -> None:
        self.status_label.configure(text=message)

    def _drain_messages(self) -> None:
        while True:
            try:
                kind, payload = self.messages.get_nowait()
            except queue.Empty:
                break

            if kind == "status":
                self._set_status(str(payload))
            elif kind == "progress":
                done, total = payload
                self.progress.set(done / total if total else 0)
            elif kind == "refresh_preview":
                self._refresh_preview()
        self.after(100, self._drain_messages)


def main() -> None:
    app = GarticDrawBotApp()
    app.mainloop()
