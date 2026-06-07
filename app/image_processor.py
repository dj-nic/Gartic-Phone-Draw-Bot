from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image

from app.palette import GARTIC_PALETTE, PaletteColor, closest_color


@dataclass(frozen=True)
class QuantizedImage:
    original: Image.Image
    preview: Image.Image
    pixel_colors: list[list[PaletteColor | None]]


class ImageProcessor:
    def __init__(self, palette: tuple[PaletteColor, ...] = GARTIC_PALETTE) -> None:
        self.palette = palette

    def load_file(self, path: str | Path) -> Image.Image:
        return Image.open(path).convert("RGBA")

    def load_url(self, url: str, timeout: int = 15) -> Image.Image:
        request = Request(url, headers={"User-Agent": "GarticPhoneDrawBot/2.0"})
        try:
            with urlopen(request, timeout=timeout) as response:
                return Image.open(BytesIO(response.read())).convert("RGBA")
        except (HTTPError, URLError) as exc:
            raise ValueError(f"Could not load image URL: {exc}") from exc

    def quantize(self, image: Image.Image, detail_level: int, pixel_count: int = 200) -> QuantizedImage:
        detail = 10 - max(1, min(10, int(detail_level))) + 1
        size = max(1, int(pixel_count / detail))
        original = image.convert("RGBA")
        resized = original.resize((size, size), Image.Resampling.LANCZOS)
        source = resized.load()
        preview = Image.new("RGBA", resized.size, (255, 255, 255, 0))
        preview_pixels = preview.load()
        pixel_colors: list[list[PaletteColor | None]] = []

        for x in range(resized.width):
            column: list[PaletteColor | None] = []
            for y in range(resized.height):
                r, g, b, alpha = source[x, y]
                if alpha == 0:
                    column.append(None)
                    preview_pixels[x, y] = (255, 255, 255, 0)
                    continue

                color = closest_color((r, g, b), self.palette)
                if color.name == "White":
                    column.append(None)
                    preview_pixels[x, y] = (255, 255, 255, 255)
                    continue

                column.append(color)
                preview_pixels[x, y] = (*color.rgb, 255)
            pixel_colors.append(column)

        scaled_preview = preview.resize((360, 360), Image.Resampling.NEAREST)
        return QuantizedImage(original=original, preview=scaled_preview, pixel_colors=pixel_colors)
