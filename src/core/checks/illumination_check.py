import cv2
import numpy as np

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints

# Длинная сторона сетки: тень плавная, детали глифов для неё лишние.
_GRID = 32
# Три прохода хватает, чтобы заливки и прочие выбросы перестали тянуть поверхность.
_FIT_PASSES = 3
# Доля медианы фона: заливки таблиц резкие и дают остаток выше, плавная тень ниже.
_OUTLIER_SHARE = 0.1
# Меньше инлайеров квадратике из шести коэффициентов доверять нельзя.
_MIN_FIT_CELLS = 12
# Клетка считается текстовой, если чернила занимают хотя бы эту долю её площади.
_TEXT_CELL_SHARE = 0.02


def _design_matrix(height: int, width: int) -> np.ndarray:
    """Матрица квадратичной поверхности по клеткам сетки, координаты в 0..1."""
    xs, ys = np.meshgrid(np.linspace(0.0, 1.0, width), np.linspace(0.0, 1.0, height))
    x = xs.ravel()
    y = ys.ravel()
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], axis=1)


def _fit_surface(design: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Гладкая поверхность по значениям клеток с отбросом выбросов."""
    limit = _OUTLIER_SHARE * float(np.median(values))
    coeffs = np.linalg.lstsq(design, values, rcond=None)[0]
    for _ in range(_FIT_PASSES):
        inliers = np.abs(design @ coeffs - values) <= limit
        if inliers.sum() < _MIN_FIT_CELLS:
            break
        coeffs = np.linalg.lstsq(design[inliers], values[inliers], rcond=None)[0]
    return design @ coeffs


def _to_grid(image: np.ndarray, height: int, width: int) -> np.ndarray:
    """Уменьшает изображение до сетки усреднением по площади."""
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


class IlluminationCheck(Check):
    """Неравномерность освещения: перепад гладкого фона под текстом."""

    name = "illumination"
    points = ScorePoints(bad=0.6, passed=0.46, good=0.3)

    def measure(self, ctx: RasterContext) -> float | None:
        """Перепад `1 − min/max` гладкой поверхности фона по клеткам с текстом.

        Поверхность квадратичная, подогнанная устойчиво, без выбросов вроде
        заливок. Возвращает None, если на странице нет чернил или текстовых
        клеток.
        """
        ink_mask = ctx.ink_mask
        if ink_mask is None:
            return None
        background = ctx.background
        scale = min(1.0, _GRID / max(background.shape))
        height = max(1, round(background.shape[0] * scale))
        width = max(1, round(background.shape[1] * scale))
        grid = _to_grid(background, height, width).ravel()
        ink_share = _to_grid(ink_mask.astype(np.float32) / 255.0, height, width)
        text_cells = ink_share.ravel() >= _TEXT_CELL_SHARE
        if not text_cells.any():
            return None
        surface = _fit_surface(_design_matrix(height, width), grid)
        text_surface = np.maximum(surface[text_cells], 1.0)
        return float(1.0 - text_surface.min() / text_surface.max())


CHECK = IlluminationCheck()
