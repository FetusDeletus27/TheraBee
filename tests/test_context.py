"""Synthetic contract tests, not a live-model or clinical accuracy evaluation."""

import json

import pytest

from therabee_safety import (
    Classification, InMemoryLockStorage, JsonCallableClassifier,
    RecommendedAction, SafetyEngine, ScanRequest,
)
from therabee_safety.classifier import CLASSIFIER_PROMPT


def make_request(message: str, history: tuple[str, ...] = ()) -> ScanRequest:
    return ScanRequest("synthetic-user", "synthetic-session", message, history)


@pytest.mark.parametrize("history,message,crisis", [
    (("I have a plan to end my life tonight.",), "Tonight.", True),
    (("When will you finish your homework?",), "Tonight.", False),
    (("I have been thinking about ending my life.",), "I still mean it.", True),
    (("Are you leaving the board game?",), "I'm done.", False),
    (("We are analyzing a fictional character in class.",),
     "The character says there is nothing left for them.", False),
    (("I felt hopeless years ago, but I feel safe now.",),
     "That was back then.", False),
])
def test_ambiguous_examples_forward_context_and_use_provider_result(
    history: tuple[str, ...], message: str, crisis: bool
) -> None:
    prompts = []

    def caller(prompt: str) -> str:
        prompts.append(prompt)
        return json.dumps({"crisis": crisis, "reason": "synthetic assessment"})

    storage = InMemoryLockStorage()
    decision = SafetyEngine(storage, JsonCallableClassifier(caller)).evaluate(
        make_request(message, history)
    )
    assert len(prompts) == 1
    assert json.loads(prompts[0][len(CLASSIFIER_PROMPT):]) == {
        "prior_user_messages": list(history), "current_message": message,
    }
    assert decision.classifier_attempted
    assert decision.classifier_error is None
    assert decision.signal_detected is crisis
    assert decision.action_performed is False
    record = storage.get("synthetic-user")
    if crisis:
        assert record is not None
        assert record.message_excerpt == message
        assert decision.recommended_action is RecommendedAction.SHOW_RESOURCES_AND_RESTRICT_FLOW
    else:
        assert record is None
        assert decision.recommended_action is RecommendedAction.CONTINUE


@pytest.mark.parametrize("message,history", [
    ("Tonight.", ()), ("Tonight.", ("   ",)),
    ("Tonight.", ("Dropped old context", "", "", "", "", "", "")),
    ("Tonight.", (" " * 500 + "Truncated context",)),
    ("   ", ("Prior synthetic context",)),
])
def test_empty_or_context_free_short_messages_do_not_call_provider(message, history) -> None:
    def caller(_: str) -> str:
        pytest.fail("provider should not be called")

    decision = SafetyEngine(InMemoryLockStorage(), JsonCallableClassifier(caller)).evaluate(
        make_request(message, history)
    )
    assert not decision.classifier_attempted


def test_legacy_classifier_keeps_single_message_contract_and_threshold() -> None:
    class LegacyClassifier:
        def __init__(self):
            self.messages = []

        def classify(self, message):
            self.messages.append(message)
            return Classification(False)

    classifier = LegacyClassifier()
    engine = SafetyEngine(InMemoryLockStorage(), classifier)
    history = ("Prior synthetic context",)
    short = engine.evaluate(make_request("Tonight.", history))
    long = engine.evaluate(make_request("An ordinary message long enough.", history))
    assert not short.classifier_attempted
    assert long.classifier_attempted
    assert classifier.messages == ["An ordinary message long enough."]


@pytest.mark.parametrize("response,error", [
    ('{}', "ValueError"), ('{"crisis":', "JSONDecodeError"),
])
def test_contextual_invalid_response_preserves_error_reporting(response, error) -> None:
    storage = InMemoryLockStorage()
    decision = SafetyEngine(storage, JsonCallableClassifier(lambda _: response)).evaluate(
        make_request("Tonight.", ("Prior synthetic context",))
    )
    assert decision.classifier_attempted
    assert decision.classifier_error == error
    assert not decision.signal_detected
    assert storage.get("synthetic-user") is None


def test_contextual_provider_timeout_is_visible_without_sensitive_details() -> None:
    def caller(_: str) -> str:
        raise TimeoutError("sensitive synthetic provider detail")

    decision = SafetyEngine(InMemoryLockStorage(), JsonCallableClassifier(caller)).evaluate(
        make_request("Tonight.", ("Prior synthetic context",))
    )
    assert decision.classifier_error == "TimeoutError"
    assert decision.recommended_action is RecommendedAction.CONTINUE
    assert "sensitive" not in repr(decision)


def test_keyword_hit_and_existing_lock_still_bypass_provider_with_context() -> None:
    def caller(_: str) -> str:
        pytest.fail("keyword hits and existing locks must bypass provider")

    storage = InMemoryLockStorage()
    engine = SafetyEngine(storage, JsonCallableClassifier(caller))
    first = engine.evaluate(make_request("I want to die", ("Prior synthetic context",)))
    second = engine.evaluate(make_request("ordinary follow-up", ("Other context",)))
    assert first.signal_detected and not first.classifier_attempted
    assert second.already_locked and not second.classifier_attempted


def test_contextual_storage_failure_propagates() -> None:
    class FailingStorage:
        def get(self, subject_id):
            return None

        def put(self, record):
            raise OSError("synthetic write failure")

    engine = SafetyEngine(FailingStorage(), JsonCallableClassifier(lambda _: '{"crisis": true}'))
    with pytest.raises(OSError, match="synthetic write failure"):
        engine.evaluate(make_request("Tonight.", ("Prior synthetic context",)))


def test_custom_contextual_classifier_receives_bounded_history() -> None:
    class ContextualClassifier:
        def classify(self, message):
            pytest.fail("contextual method expected")

        def classify_with_context(self, message, prior_messages):
            assert message == "Tonight."
            assert prior_messages == tuple(text[:500] for text in history[-6:])
            return Classification(False)

    history = tuple(f"synthetic {i}: " + "x" * 600 for i in range(8))
    decision = SafetyEngine(InMemoryLockStorage(), ContextualClassifier()).evaluate(
        make_request("Tonight.", history)
    )
    assert decision.classifier_attempted and decision.classifier_error is None


def test_provider_reason_can_contain_history_and_must_be_treated_as_sensitive() -> None:
    marker = "PRIVATE_SYNTHETIC_HISTORY"
    storage = InMemoryLockStorage()
    classifier = JsonCallableClassifier(
        lambda _: json.dumps({"crisis": True, "reason": marker})
    )
    decision = SafetyEngine(storage, classifier).evaluate(make_request("Tonight.", (marker,)))
    record = storage.get("synthetic-user")
    assert record is not None
    assert record.message_excerpt == "Tonight."
    assert record.reason == decision.reason == f"classifier: {marker}"
