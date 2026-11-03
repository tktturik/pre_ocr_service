from collections.abc import Sequence

from core.models.analysis_types import ItemResult, Verdict

# Документ с непригодным элементом не получает оценку выше этого значения (как у растра)
_FAIL_CEILING = 0.49


def score_document(items: Sequence[ItemResult]) -> Verdict:
    """Вердикт и оценка документа по его элементам.

    Элементы с вердиктом «не определено» не входят ни в вердикт, ни в среднее.
    Документ пригоден, если пригодны все определённые элементы. Оценка — среднее
    их скоров; при непригодности она не выше _FAIL_CEILING. Если определённых
    элементов нет, итог «не определено».
    """
    verdicts = [
        item.verdict for item in items if item.verdict.suitable_for_ocr is not None
    ]
    if not verdicts:
        return Verdict(suitable_for_ocr=None, quality_score=None)
    scores = [v.quality_score for v in verdicts if v.quality_score is not None]
    suitable = all(v.suitable_for_ocr for v in verdicts)
    mean = sum(scores) / len(scores)
    return Verdict(
        suitable_for_ocr=suitable,
        quality_score=mean if suitable else min(mean, _FAIL_CEILING),
    )
