from collections.abc import Callable

from core.checks.raster_context import RasterContext
from core.checks.sharpness_check import SharpnessCheck
from core.scoring.check_scoring import score_value


def test_measure_stronger_blur_lowers_score(
    make_ctx: Callable[..., RasterContext],
) -> None:
    """Рост sigma размытия увеличивает значение и монотонно снижает скор."""
    check = SharpnessCheck()

    sharp, soft, blurry = (check.measure(make_ctx(sigma=s)) for s in (1, 3, 5))

    assert sharp is not None
    assert soft is not None
    assert blurry is not None
    assert sharp < soft < blurry
    scores = [score_value(v, SharpnessCheck.points) for v in (sharp, soft, blurry)]
    assert scores[0] >= scores[1] >= scores[2]
    assert scores[0] > scores[2]
