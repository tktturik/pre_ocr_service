from functools import cached_property

import cv2
import numpy as np

from core.models.raster_types import Raster

_BACKGROUND_SIDE = 384  # длинная сторона уменьшенной копии для оценки фона
_BACKGROUND_BLOCK = 16  # сторона блока на уменьшенной копии
_BACKGROUND_PERCENTILE = 90
_MIN_INK_CONTRAST = 0.05  # минимальный разрыв средних нормализованных классов Otsu
_MIN_COMPONENT_AREA = 4  # меньшие компоненты считаются шумом
_TRIM_LOW = 0.3  # доли медианы высоты, за которыми компонента отсекается
_TRIM_HIGH = 3.0
_TRIM_PASSES = 2
_MIN_LETTERS = 20  # меньше буквенных компонент — маски чернил нет


def _letter_ids(stats: np.ndarray) -> np.ndarray:
    """Индексы строк stats: площадь не меньше минимума и высота после отсева."""
    ids = np.flatnonzero(stats[:, cv2.CC_STAT_AREA] >= _MIN_COMPONENT_AREA)
    heights = stats[ids, cv2.CC_STAT_HEIGHT]
    for _ in range(_TRIM_PASSES):
        if ids.size == 0:
            break
        median = np.median(heights)
        keep = (heights >= _TRIM_LOW * median) & (heights <= _TRIM_HIGH * median)
        if not keep.any():
            break
        ids = ids[keep]
        heights = heights[keep]
    return ids


class RasterContext:
    """Ленивый общий контекст растра: каждая величина считается при первом обращении.

    Используется только проверками. Пиксели не изменяются.
    """

    def __init__(self, raster: Raster) -> None:
        self._raster = raster

    @cached_property
    def gray(self) -> np.ndarray:
        """Серый растр uint8 (2D), как отдал загрузчик."""
        return self._raster.pixels

    @cached_property
    def background(self) -> np.ndarray:
        """
        Карта фона float32 размера растра:
        перцентиль яркости по блокам уменьшенной копии.
        """
        height, width = self.gray.shape
        scale = min(1.0, _BACKGROUND_SIDE / max(height, width))
        small = cv2.resize(
            self.gray,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
        pad_y = -small.shape[0] % _BACKGROUND_BLOCK
        pad_x = -small.shape[1] % _BACKGROUND_BLOCK
        padded = np.pad(small, ((0, pad_y), (0, pad_x)), mode="edge")
        blocks = padded.reshape(
            padded.shape[0] // _BACKGROUND_BLOCK,
            _BACKGROUND_BLOCK,
            padded.shape[1] // _BACKGROUND_BLOCK,
            _BACKGROUND_BLOCK,
        )
        grid = np.percentile(blocks, _BACKGROUND_PERCENTILE, axis=(1, 3)).astype(
            np.float32
        )
        stretched = cv2.resize(grid, (width, height), interpolation=cv2.INTER_LINEAR)
        return np.maximum(stretched, 1.0)

    @cached_property
    def normalized(self) -> np.ndarray:
        """Яркость, поделённая на фон, float32 в диапазоне 0..1."""
        return np.clip(self.gray / self.background, 0.0, 1.0).astype(np.float32)

    @cached_property
    def _otsu_mask(self) -> np.ndarray | None:
        """
        Маска uint8 (0/255): меньший по площади класс Otsu;
        None, если чернил нет.
        """
        levels = (self.normalized * 255).astype(np.uint8)
        threshold, _ = cv2.threshold(
            levels, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        dark = levels <= threshold
        bright = ~dark
        if not dark.any() or not bright.any():
            return None
        ink = dark if dark.sum() <= bright.sum() else bright
        contrast = abs(
            float(self.normalized[dark].mean()) - float(self.normalized[bright].mean())
        )
        if contrast < _MIN_INK_CONTRAST:
            return None
        return ink.astype(np.uint8) * 255

    @cached_property
    def components(self) -> np.ndarray | None:
        """
        Статистика связных компонент чернил (left, top, width, height, area);
        None, если их нет.
        """
        if self._otsu_mask is None:
            return None
        count, _, stats, _ = cv2.connectedComponentsWithStats(
            self._otsu_mask, connectivity=8
        )
        if count <= 1:
            return None
        return stats[1:]

    @cached_property
    def text_height(self) -> float | None:
        """
        Медиана высот компонент после двухпроходного отсечения мелких и крупных;
        None без чернил.
        """
        if self.components is None:
            return None
        stats = self.components
        ids = _letter_ids(stats)
        if ids.size == 0:
            return None
        return float(np.median(stats[ids, cv2.CC_STAT_HEIGHT]))

    @cached_property
    def ink_mask(self) -> np.ndarray | None:
        """
        Маска чернил uint8 (0/255) только из буквенных компонент маски Otsu
        (площадь и высота как у `text_height`); None, если маски Otsu нет
        или буквенных компонент меньше `_MIN_LETTERS`.
        """
        if self._otsu_mask is None:
            return None
        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            self._otsu_mask, connectivity=8
        )
        ids = _letter_ids(stats[1:])
        if ids.size < _MIN_LETTERS:
            return None
        is_letter = np.zeros(count, dtype=bool)
        is_letter[ids + 1] = True
        return is_letter[labels.astype(np.intp)].astype(np.uint8) * 255

    @cached_property
    def ink_level(self) -> float | None:
        """Медианная яркость серого под маской чернил (0..255); None без чернил."""
        if self.ink_mask is None:
            return None
        return float(np.median(self.gray[self.ink_mask > 0]))

    @cached_property
    def background_level(self) -> float:
        """Медианная яркость фона (0..255)."""
        return float(np.median(self.background))
