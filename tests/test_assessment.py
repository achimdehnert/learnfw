"""Tests for iil-learnfw assessment models and scoring service."""

import pytest
from django.contrib.auth import get_user_model

from iil_learnfw.models import (
    Answer,
    Attempt,
    Chapter,
    Course,
    Question,
    Quiz,
)
from iil_learnfw.services.scoring_service import (
    can_retry,
    finish_attempt,
    submit_answer,
)

User = get_user_model()


@pytest.fixture
def course():
    return Course.objects.create(title="Test Course", slug="test-assess")


@pytest.fixture
def chapter(course):
    return Chapter.objects.create(course=course, title="Chapter 1")


@pytest.fixture
def quiz(course):
    return Quiz.objects.create(course=course, title="Final Quiz", passing_score=60)


@pytest.fixture
def questions_with_answers(quiz):
    q1 = Question.objects.create(
        quiz=quiz, question_type="single_choice",
        text="What is 2+2?", points=10, ordering=0,
    )
    Answer.objects.create(question=q1, text="3", is_correct=False, ordering=0)
    correct_a1 = Answer.objects.create(
        question=q1, text="4", is_correct=True, ordering=1,
    )

    q2 = Question.objects.create(
        quiz=quiz, question_type="single_choice",
        text="Capital of Germany?", points=10, ordering=1,
    )
    Answer.objects.create(question=q2, text="Munich", is_correct=False, ordering=0)
    correct_a2 = Answer.objects.create(
        question=q2, text="Berlin", is_correct=True, ordering=1,
    )
    return [(q1, correct_a1), (q2, correct_a2)]


@pytest.fixture
def user():
    return User.objects.create_user(username="quiztaker", password="test")


@pytest.mark.django_db
class TestQuizModel:
    """Quiz model tests."""

    def test_should_create_quiz(self, quiz):
        assert quiz.pk is not None
        assert quiz.passing_score == 60
        assert quiz.max_attempts == 0

    def test_should_create_question_with_answers(self, questions_with_answers):
        q1, correct = questions_with_answers[0]
        assert q1.answers.count() == 2
        assert correct.is_correct is True


@pytest.mark.django_db
class TestScoringService:
    """Scoring service tests."""

    def test_should_score_perfect_attempt(self, user, quiz, questions_with_answers):
        attempt = Attempt.objects.create(user=user, quiz=quiz)
        for question, correct_answer in questions_with_answers:
            submit_answer(attempt.pk, question.pk, correct_answer.pk)

        result = finish_attempt(attempt.pk)
        assert result.passed is True
        assert result.score == 100
        assert result.completed_at is not None

    def test_should_fail_attempt_with_wrong_answers(self, user, quiz, questions_with_answers):
        attempt = Attempt.objects.create(user=user, quiz=quiz)
        for question, correct_answer in questions_with_answers:
            wrong = question.answers.filter(is_correct=False).first()
            submit_answer(attempt.pk, question.pk, wrong.pk)

        result = finish_attempt(attempt.pk)
        assert result.passed is False
        assert result.score == 0

    def test_should_allow_unlimited_retries(self, user, quiz):
        assert quiz.max_attempts == 0
        assert can_retry(user, quiz.pk) is True

    def test_should_limit_retries(self, user, quiz, questions_with_answers):
        quiz.max_attempts = 1
        quiz.save()

        attempt = Attempt.objects.create(user=user, quiz=quiz)
        finish_attempt(attempt.pk)

        assert can_retry(user, quiz.pk) is False
