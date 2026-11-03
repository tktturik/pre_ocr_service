import io
from collections.abc import Iterator

import numpy as np
from PIL import Image

from core.errors import DocumentUnreadableError, TooManyPixelsError
from core.loaders.base_loader import Loader
from core.models.analysis_types import AnalysisLimits
from core.models.raster_types import Raster, Unit

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"


class ImageLoader(Loader):
    """Загрузчик PNG и JPEG: отдаёт файл одним серым растром."""

    def matches(self, head: bytes) -> bool:
        """Проверяет сигнатуру PNG или JPEG по первым байтам."""
        return head.startswith((PNG_SIGNATURE, JPEG_SIGNATURE))

    def units(self, data: bytes, limits: AnalysisLimits) -> Iterator[Unit]:
        """Отдаёт один серый растр index=1.

        Ошибки: TooManyPixelsError, если размер по заголовку больше лимита;
        DocumentUnreadableError, если тело не декодируется.
        """
        with _open_image(data) as image:
            _check_pixels(image, limits.max_raster_pixels)
            gray = _decode_gray(image)
        yield Raster(index=1, pixels=gray)


def _open_image(data: bytes) -> Image.Image:
    # Image.open читает только заголовок, пиксели декодируются позже.
    try:
        return Image.open(io.BytesIO(data))
    except Image.DecompressionBombError as exc:
        raise TooManyPixelsError() from exc
    except OSError as exc:
        raise DocumentUnreadableError() from exc


def _check_pixels(image: Image.Image, max_pixels: int) -> None:
    width, height = image.size
    if width * height > max_pixels:
        raise TooManyPixelsError()


def _decode_gray(image: Image.Image) -> np.ndarray:
    try:
        return np.asarray(image.convert("L"), dtype=np.uint8)
    except (OSError, SyntaxError, ValueError) as exc:
        raise DocumentUnreadableError() from exc


LOADER = ImageLoader()
