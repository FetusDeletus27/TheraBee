from __future__ import annotations

import pytest

from therabee_safety import (
    Classification,
    InMemoryLockStorage,
    RecommendedAction,
    SafetyEngine,
    ScanRequest,
    keyword_scan,
)


def request(message: str, subject: str = "synthetic-user") -> ScanRequest:
    return ScanRequest(subject_id=subject, session_id="synthetic-session", message=message)


@pytest.mark.parametrize("text", [
    "I want to die", "I am planning to hurt myself", "I took too many pills",
    "I want to harm someone", "goodbye forever",
])
def test_positive_keyword_hits(text: str) -> None:
    assert keyword_scan(text) is not None


@pytest.mark.parametrize("text", [
    "It's not like I'm gonna kill myself", "I'm not suicidal or anything",
    "kill myself lol", "I don't actually want to kill myself",
])
def test_negated_or_dismissed_phrases_are_not_hits(text: str) -> None:
    assert keyword_scan(text) is None


def test_keyword_hit_is_stored_and_recommends_but_performs_no_action() -> None:
    storage = InMemoryLockStorage()
    decision = SafetyEngine(storage).evaluate(request("I want to die"))
    assert decision.signal_detected
    assert decision.recommended_action is RecommendedAction.SHOW_RESOURCES_AND_RESTRICT_FLOW
    assert decision.action_performed is False
    assert storage.get("synthetic-user") is not None
    assert storage.get("synthetic-user").message_excerpt == "I want to die"


def test_already_locked_short_circuits_scanning() -> None:
    storage = InMemoryLockStorage()
    engine = SafetyEngine(storage)
    engine.evaluate(request("I want to die"))
    second = engine.evaluate(request("ordinary follow-up"))
    assert second.signal_detected and second.already_locked


class StubClassifier:
    def __init__(self, result: Classification | None = None, error: Exception | None = None) -> None:
        self.result, self.error, self.calls = result, error, 0

    def classify(self, message: str) -> Classification:
        self.calls += 1
        if self.error:
            raise self.error
        assert self.result is not None
        return self.result


def test_classifier_hit_is_stored() -> None:
    classifier = StubClassifier(Classification(True, "current intent"))
    storage = InMemoryLockStorage()
    decision = SafetyEngine(storage, classifier).evaluate(request("A subtle synthetic statement long enough."))
    assert decision.signal_detected and decision.classifier_attempted
    assert decision.reason == "classifier: current intent"
    assert storage.get("synthetic-user") is not None


def test_classifier_error_fails_open_and_is_visible() -> None:
    classifier = StubClassifier(error=RuntimeError("synthetic outage"))
    decision = SafetyEngine(InMemoryLockStorage(), classifier).evaluate(
        request("A neutral synthetic statement long enough.")
    )
    assert not decision.signal_detected
    assert decision.classifier_attempted
    assert "RuntimeError" in decision.classifier_error
    assert decision.recommended_action is RecommendedAction.CONTINUE


@pytest.mark.parametrize("text", ["x" * 20, "  " + "x" * 20 + "  "])
def test_classifier_not_called_at_original_exclusive_length_threshold(text: str) -> None:
    classifier = StubClassifier(Classification(True, "should not run"))
    decision = SafetyEngine(InMemoryLockStorage(), classifier).evaluate(request(text))
    assert classifier.calls == 0
    assert not decision.classifier_attempted


def test_classifier_called_above_threshold() -> None:
    classifier = StubClassifier(Classification(False))
    SafetyEngine(InMemoryLockStorage(), classifier).evaluate(request("x" * 21))
    assert classifier.calls == 1


def test_storage_remove_behavior() -> None:
    storage = InMemoryLockStorage()
    SafetyEngine(storage).evaluate(request("I want to die"))
    assert storage.remove("synthetic-user") is True
    assert storage.remove("synthetic-user") is False
    assert storage.get("synthetic-user") is None


class FailingStorage:
    def __init__(self, fail_on: str) -> None:
        self.fail_on = fail_on

    def get(self, subject_id: str):
        if self.fail_on == "get":
            raise OSError("synthetic read failure")
        return None

    def put(self, record):
        if self.fail_on == "put":
            raise OSError("synthetic write failure")

    def remove(self, subject_id: str) -> bool:
        raise OSError("synthetic remove failure")


@pytest.mark.parametrize("operation,message", [("get", "hello"), ("put", "I want to die")])
def test_storage_failures_propagate(operation: str, message: str) -> None:
    with pytest.raises(OSError, match="synthetic"):
        SafetyEngine(FailingStorage(operation)).evaluate(request(message))
