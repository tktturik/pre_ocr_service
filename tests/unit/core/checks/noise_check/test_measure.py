from collections.abc import Callable

from core.checks.noise_check import NoiseCheck
from core.checks.raster_context import RasterContext
from core.scoring.check_scoring import score_value

# Почему 15%: значение - отношение шума к контрасту текста; выцветание
# пропорционально масштабирует оба, но округление до uint8 и обрезка 0..255
# вносят небольшую погрешность, которую допускаем.
FADE_TOLERANCE = 0.15


def test_noise_grows_with_sigma_and_score_does_not_rise(
    make_noisy_ctx: Callable[..., RasterContext],
) -> None:
    """Рост sigma строго увеличивает значение и не повышает скор."""
    check = NoiseCheck()

    low = check.measure(make_noisy_ctx(5))
    mid = check.measure(make_noisy_ctx(20))
    high = check.measure(make_noisy_ctx(40))
    assert low is not None and mid is not None and high is not None
    assert low < mid < high
    assert score_value(low, check.points) >= score_value(high, check.points)


def test_noise_is_stable_under_fade(
    make_noisy_ctx: Callable[..., RasterContext],
) -> None:
    """Выцветание той же страницы меняет значение не более чем на допуск."""
    check = NoiseCheck()

    base = check.measure(make_noisy_ctx(20))
    faded = check.measure(make_noisy_ctx(20, fade=0.5))

    assert base is not None and faded is not None
    assert abs(faded - base) / base <= FADE_TOLERANCE
