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
    def ink_mask(self) -> np.ndarray | None:
        """
        Маска чернил uint8 (0/255): меньший по площади класс Otsu;
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
        if self.ink_mask is None:
            return None
        count, _, stats, _ = cv2.connectedComponentsWithStats(
            self.ink_mask, connectivity=8
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
        heights = stats[
            stats[:, cv2.CC_STAT_AREA] >= _MIN_COMPONENT_AREA, cv2.CC_STAT_HEIGHT
        ]
        if heights.size == 0:
            return None
        for _ in range(_TRIM_PASSES):
            median = np.median(heights)
            kept = heights[
                (heights >= _TRIM_LOW * median) & (heights <= _TRIM_HIGH * median)
            ]
            if kept.size == 0:
                break
            heights = kept
        return float(np.median(heights))

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
