"""Фикстуры тестов document_scoring."""

import pytest

from core.models.analysis_types import ItemResult, Verdict

DocumentCase = tuple[tuple[ItemResult, ...], Verdict]


@pytest.fixture(
    params=[
        pytest.param(
            (
                (
                    ItemResult(1, Verdict(True, 0.9), checks=()),
                    ItemResult(2, Verdict(True, 0.7), checks=()),
                ),
                Verdict(True, 0.8),
            ),
            id="all_suitable",
        ),
        pytest.param(
            (
                (
                    ItemResult(1, Verdict(True, 1.0), checks=()),
                    ItemResult(2, Verdict(True, 1.0), checks=()),
                    ItemResult(3, Verdict(False, 0.4), checks=()),
                ),
                Verdict(False, 0.49),
            ),
            id="one_unsuitable_capped",
        ),
    ]
)
def document_case(request: pytest.FixtureRequest) -> DocumentCase:
    """Элементы документа и ожидаемый вердикт по ним."""
    return request.param
