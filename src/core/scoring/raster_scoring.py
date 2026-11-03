from collections.abc import Sequence

from core.models.analysis_types import CheckOutcome, Verdict

# Ниже порога passed (0.5): элемент с провалом не может выглядеть «пригодным» по оценке.
_UNSUITABLE_SCORE_CAP = 0.49


def score_raster(outcomes: Sequence[CheckOutcome]) -> Verdict:
    """Вердикт и quality_score элемента по его проверкам.

    Не определённые проверки (passed и score None) не входят ни в вердикт, ни в среднее.
    Пригоден, только если все определённые проверки пройдены; при провале оценка
    ограничивается _UNSUITABLE_SCORE_CAP. Если определённых проверок нет, возвращает
    Verdict(None, None).
    """
    scores = [o.score for o in outcomes if o.score is not None]
    if not scores:
        return Verdict(suitable_for_ocr=None, quality_score=None)
    suitable = all(o.passed for o in outcomes if o.passed is not None)
    quality_score = sum(scores) / len(scores)
    if not suitable:
        quality_score = min(quality_score, _UNSUITABLE_SCORE_CAP)
    return Verdict(suitable_for_ocr=suitable, quality_score=quality_score)
