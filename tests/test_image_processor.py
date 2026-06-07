from PIL import Image
import pytest

from app.image_processor import ImageProcessor


def test_quantize_creates_preview_and_skips_white_pixels():
    image = Image.new("RGBA", (2, 2), (255, 255, 255, 255))
    image.putpixel((0, 0), (250, 5, 20, 255))

    result = ImageProcessor().quantize(image, detail_level=10, pixel_count=2)

    assert result.preview.size == (360, 360)
    assert result.pixel_colors[0][0].name == "Red"
    assert result.pixel_colors[1][1] is None


def test_load_file_raises_for_missing_image(tmp_path):
    with pytest.raises(FileNotFoundError):
        ImageProcessor().load_file(tmp_path / "missing.png")
