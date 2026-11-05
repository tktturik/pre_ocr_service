import math

import numpy as np

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints

# Блок крупнее глифа и межстрочья: внутри почти всегда есть участок без текста.
_BLOCK = 32
# Меньше блоков перцентиль по ним ничего не говорит о странице.
_MIN_BLOCKS = 16
# Потолок затрат на огромных растрах: сетка блоков прореживается равномерно.
_MAX_BLOCKS = 4096
# Самые тихие блоки (поля, межстрочье) не зависят от маски чернил, а на шумной
# странице маска засорена точками; 10-й перцентиль не берёт блоки с глифами.
_QUIET_PERCENTILE = 10
# Контраст не выше одного уровня серого: делить на него бессмысленно.
_MIN_CONTRAST = 1.0
# Перевод MAD в σ для нормального закона.
_MAD_TO_SIGMA = 1.4826


def _block_grid(gray: np.ndarray) -> np.ndarray:
    """Блоки _BLOCK x _BLOCK серого растра формы (строки, столбцы, _BLOCK, _BLOCK).

    Неполные блоки у края отбрасываются, при избытке блоков берётся каждый
    `step`-й по строкам и столбцам.
    """
    rows = gray.shape[0] // _BLOCK
    cols = gray.shape[1] // _BLOCK
    cropped = gray[: rows * _BLOCK, : cols * _BLOCK]
    blocks = cropped.reshape(rows, _BLOCK, cols, _BLOCK).transpose(0, 2, 1, 3)
    if rows * cols > _MAX_BLOCKS:
        step = math.ceil(math.sqrt(rows * cols / _MAX_BLOCKS))
        blocks = blocks[::step, ::step]
    return blocks


def _block_sigmas(blocks: np.ndarray) -> np.ndarray:
    """σ шума по каждому блоку: MAD разностей соседних пикселей по x и y."""
    signed = blocks.astype(np.int16)
    dx = (signed[..., :, 1:] - signed[..., :, :-1]).reshape(-1, _BLOCK * (_BLOCK - 1))
    dy = (signed[..., 1:, :] - signed[..., :-1, :]).reshape(-1, _BLOCK * (_BLOCK - 1))
    diffs = np.concatenate([dx, dy], axis=1)
    center = np.median(diffs, axis=1, keepdims=True)
    mad = np.median(np.abs(diffs - center), axis=1)
    # Разность двух независимых пикселей имеет дисперсию 2σ².
    return _MAD_TO_SIGMA * mad / math.sqrt(2.0)


class NoiseCheck(Check):
    """Шум серого растра относительно контраста текста."""

    name = "noise"
    points = ScorePoints(bad=0.177, passed=0.11, good=0.0566)

    def measure(self, ctx: RasterContext) -> float | None:
        """Отношение σ шума к контрасту `фон − чернила`, меньше — лучше.

        σ — 10-й перцентиль по блокам 32 px оценки `1.4826 · MAD / √2`
        разностей соседних пикселей внутри блока. Деление на контраст в уровнях
        серого оставляет значение неизменным при выцветании страницы: шум и
        контраст масштабируются одинаково. Возвращает None, если на странице
        нет чернил, контраст не выше одного уровня или блоков меньше 16.
        """
        ink_level = ctx.ink_level
        if ctx.ink_mask is None or ink_level is None:
            return None
        contrast = ctx.background_level - ink_level
        if contrast <= _MIN_CONTRAST:
            return None
        blocks = _block_grid(ctx.gray)
        if blocks.shape[0] * blocks.shape[1] < _MIN_BLOCKS:
            return None
        sigmas = _block_sigmas(blocks)
        sigma = float(np.percentile(sigmas, _QUIET_PERCENTILE))
        return sigma / contrast


CHECK = NoiseCheck()
