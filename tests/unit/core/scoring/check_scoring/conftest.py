"""Фикстуры тестов check_scoring."""

import pytest

from core.models.analysis_types import ScorePoints


@pytest.fixture
def score_points() -> ScorePoints:
    """Опорные точки шкалы: bad < passed < good."""
    return ScorePoints(bad=0.0, passed=5.0, good=10.0)


@pytest.fixture
def check_name() -> str:
    """Имя проверки для результата."""
    return "fake_check"


@pytest.fixture
def reverse_score_points() -> ScorePoints:
    """Опорные точки обратной шкалы: bad > passed > good."""
    return ScorePoints(bad=10.0, passed=5.0, good=0.0)
