from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class Raster:
    """Серый растр одной единицы документа (uint8, 2D); не покидает воркер."""

    index: int
    pixels: np.ndarray


@dataclass(frozen=True, slots=True)
class UnitError:
    """Единица документа, которую не удалось отрендерить или декодировать."""

    index: int
    reason: str


Unit = Raster | UnitError
