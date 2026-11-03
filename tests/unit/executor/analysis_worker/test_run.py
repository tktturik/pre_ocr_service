from core.models.analysis_types import AnalysisRequest
from executor.analysis_worker import AnalysisWorker


def test_run_png_returns_single_item_with_outcome(
    png_worker: AnalysisWorker, png_request: AnalysisRequest
) -> None:
    """PNG с проверкой constant даёт один элемент index=1 с исходом и вердиктом."""
    result = png_worker.run(png_request)

    assert result.processing_time_ms >= 0
    assert [item.index for item in result.items] == [1]
    item = result.items[0]
    assert item.verdict.suitable_for_ocr is True
    assert [(c.name, c.passed) for c in item.checks] == [("constant", True)]


def test_run_broken_unit_is_failed_and_neighbours_scored(
    broken_unit_worker: AnalysisWorker, fake_request: AnalysisRequest
) -> None:
    """UnitError даёт Verdict(False, 0.0) без проверок, соседние растры посчитаны."""
    items = broken_unit_worker.run(fake_request).items

    assert [item.index for item in items] == [1, 2, 3]
    assert (items[1].verdict.suitable_for_ocr, items[1].verdict.quality_score) == (
        False,
        0.0,
    )
    assert items[1].checks == ()
    assert len(items[0].checks) == 1
    assert len(items[2].checks) == 1


def test_run_raising_check_scored_zero_and_others_computed(
    mixed_worker: AnalysisWorker, mixed_request: AnalysisRequest
) -> None:
    """Упавшая проверка получает passed=False, score=0.0, constant считается."""
    outcomes = {c.name: c for c in mixed_worker.run(mixed_request).items[0].checks}

    assert (outcomes["raising"].passed, outcomes["raising"].score) == (False, 0.0)
    assert outcomes["constant"].passed is True
