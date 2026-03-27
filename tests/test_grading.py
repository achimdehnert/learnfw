"""Tests for iil_learnfw.grading module (ADR-150)."""

import pytest


class TestKeywordFallback:
    """Test KeywordFallback grading backend."""

    def setup_method(self):
        from iil_learnfw.grading.keyword import KeywordFallback
        self.grader = KeywordFallback()

    def test_should_score_100_when_all_keywords_present(self):
        questions = [{"question": "Was ist KI?", "expected": "Künstliche Intelligenz", "keywords": ["künstliche", "intelligenz"]}]
        answers = ["Künstliche Intelligenz ist ein Teilgebiet der Informatik"]
        results = self.grader.grade(questions, answers)
        assert len(results) == 1
        assert results[0].score == 100

    def test_should_score_50_when_half_keywords_present(self):
        questions = [{"question": "Test", "expected": "A B", "keywords": ["alpha", "beta"]}]
        answers = ["alpha ist richtig"]
        results = self.grader.grade(questions, answers)
        assert results[0].score == 50

    def test_should_score_0_when_empty_answer(self):
        questions = [{"question": "Test", "expected": "answer", "keywords": ["key"]}]
        answers = [""]
        results = self.grader.grade(questions, answers)
        assert results[0].score == 0
        assert "Keine Antwort" in results[0].feedback

    def test_should_score_50_when_no_keywords_defined(self):
        questions = [{"question": "Test", "expected": "answer"}]
        answers = ["some answer"]
        results = self.grader.grade(questions, answers)
        assert results[0].score == 50

    def test_should_handle_multiple_questions(self):
        questions = [
            {"question": "Q1", "expected": "A1", "keywords": ["alpha"]},
            {"question": "Q2", "expected": "A2", "keywords": ["beta"]},
        ]
        answers = ["alpha here", "nothing here"]
        results = self.grader.grade(questions, answers)
        assert len(results) == 2
        assert results[0].score == 100
        assert results[1].score == 0


class TestLLMGrading:
    """Test LLMGrading backend (without actual API calls)."""

    def test_should_fallback_to_keywords_when_no_api_key(self):
        from iil_learnfw.grading.llm import LLMGrading
        grader = LLMGrading(api_key="")
        questions = [{"question": "Test", "expected": "A", "keywords": ["key"]}]
        answers = ["key is present"]
        results = grader.grade(questions, answers)
        assert len(results) == 1
        assert results[0].score == 100

    def test_should_expose_grade_answers_convenience(self):
        from iil_learnfw.grading.llm import grade_answers
        questions = [{"question": "Test", "expected": "A", "keywords": ["key"]}]
        answers = ["key"]
        results = grade_answers(questions, answers)
        assert len(results) == 1


class TestGradingImports:
    """Test that grading module imports work."""

    def test_should_import_from_package(self):
        from iil_learnfw.grading import (
            GradingBackend,
            GradingResult,
            KeywordFallback,
            LLMGrading,
        )
        assert GradingBackend is not None
        assert GradingResult is not None
        assert KeywordFallback is not None
        assert LLMGrading is not None

    def test_grading_result_is_frozen_dataclass(self):
        from iil_learnfw.grading import GradingResult
        r = GradingResult(score=85, feedback="Good")
        assert r.score == 85
        assert r.feedback == "Good"
        with pytest.raises(AttributeError):
            r.score = 90  # frozen
