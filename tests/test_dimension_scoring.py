"""Tests for dimension-based assessment scoring (ADR-150)."""

import pytest

from iil_learnfw.services.dimension_scoring import (
    _risk_level,
    calculate_dimension_score,
)


class TestRiskLevel:
    def test_low(self):
        assert _risk_level(0.75) == "low"
        assert _risk_level(1.0) == "low"

    def test_medium(self):
        assert _risk_level(0.5) == "medium"
        assert _risk_level(0.74) == "medium"

    def test_high(self):
        assert _risk_level(0.25) == "high"
        assert _risk_level(0.49) == "high"

    def test_critical(self):
        assert _risk_level(0.0) == "critical"
        assert _risk_level(0.24) == "critical"


class TestCalculateDimensionScore:
    def test_empty_responses(self):
        assert calculate_dimension_score([]) == []

    def test_single_dimension_max_score(self):
        responses = [
            {"dimension": "strategy", "value": "5", "weight": 1.0},
        ]
        results = calculate_dimension_score(responses)
        assert len(results) == 1
        assert results[0].dimension == "strategy"
        assert results[0].raw_score == 100.0
        assert results[0].risk_level == "low"

    def test_single_dimension_min_score(self):
        responses = [
            {"dimension": "strategy", "value": "1", "weight": 1.0},
        ]
        results = calculate_dimension_score(responses)
        assert len(results) == 1
        assert results[0].raw_score == 20.0
        assert results[0].risk_level == "critical"

    def test_multiple_dimensions_sorted(self):
        responses = [
            {"dimension": "strategy", "value": "5", "weight": 1.0},
            {"dimension": "governance", "value": "1", "weight": 1.0},
        ]
        results = calculate_dimension_score(responses)
        assert len(results) == 2
        assert results[0].dimension == "governance"
        assert results[1].dimension == "strategy"

    def test_weighted_scoring(self):
        responses = [
            {"dimension": "tech", "value": "5", "weight": 2.0},
            {"dimension": "tech", "value": "1", "weight": 1.0},
        ]
        results = calculate_dimension_score(responses)
        assert len(results) == 1
        # (5/5*2 + 1/5*1) / 3 = (2 + 0.2) / 3 = 0.7333
        assert round(results[0].raw_score) == 73

    def test_default_weight(self):
        responses = [
            {"dimension": "people", "value": "3"},
        ]
        results = calculate_dimension_score(responses)
        assert len(results) == 1
        assert results[0].raw_score == 60.0

    def test_invalid_value_skipped(self):
        responses = [
            {"dimension": "x", "value": "abc", "weight": 1.0},
        ]
        assert calculate_dimension_score(responses) == []

    def test_missing_dimension_skipped(self):
        responses = [
            {"value": "3", "weight": 1.0},
        ]
        assert calculate_dimension_score(responses) == []

    def test_score_result_is_frozen(self):
        responses = [
            {"dimension": "d", "value": "3", "weight": 1.0},
        ]
        result = calculate_dimension_score(responses)[0]
        with pytest.raises(AttributeError):
            result.dimension = "other"
