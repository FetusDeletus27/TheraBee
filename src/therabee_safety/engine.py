"""Crisis signal decision orchestration. No external action is performed."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .classifier import CrisisClassifier
from .scanner import keyword_scan
from .storage import LockStorage, new_lock

CLASSIFIER_MIN_LENGTH_EXCLUSIVE = 20

CRISIS_RESPONSE_TEXT = (
    "I can see you're going through something really serious right now. "
    "I care about your safety, and I want to make sure you get the right support. "
    "Please reach out to one of these resources immediately:\n\n"
    "** 988 Suicide & Crisis Lifeline ** - Call or text 988 (24/7)\n"
    "** Crisis Text Line ** - Text HOME to 741741 (24/7)\n"
    "** Emergency Services ** - Call 911\n\n"
    "You are not alone. These are people who are trained to help and they want to hear from you."
)


class RecommendedAction(str, Enum):
    CONTINUE = "continue"
    SHOW_RESOURCES_AND_RESTRICT_FLOW = "show_resources_and_restrict_flow"


@dataclass(frozen=True, slots=True)
class ScanRequest:
    subject_id: str
    session_id: str
    message: str


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    signal_detected: bool
    already_locked: bool
    reason: str | None
    recommended_action: RecommendedAction
    response_text: str | None
    classifier_attempted: bool = False
    classifier_error: str | None = None
    action_performed: bool = False


class SafetyEngine:
    """Detect a signal, record a lock recommendation, and return a decision.

    A stored record is application state only. This class does not call, text,
    notify, navigate, block a user, or contact emergency services.
    """

    def __init__(self, storage: LockStorage, classifier: CrisisClassifier | None = None) -> None:
        self._storage = storage
        self._classifier = classifier

    def evaluate(self, request: ScanRequest) -> SafetyDecision:
        existing = self._storage.get(request.subject_id)
        if existing is not None:
            return self._crisis_decision(existing.reason, already_locked=True)

        hit = keyword_scan(request.message)
        if hit is not None:
            self._storage.put(new_lock(request.subject_id, request.session_id, hit.reason, request.message))
            return self._crisis_decision(hit.reason)

        attempted = False
        classifier_error: str | None = None
        if self._classifier is not None and len(request.message.strip()) > CLASSIFIER_MIN_LENGTH_EXCLUSIVE:
            attempted = True
            try:
                result = self._classifier.classify(request.message)
                if result.crisis:
                    reason = f"classifier: {result.reason or 'flagged as crisis'}"
                    self._storage.put(new_lock(request.subject_id, request.session_id, reason, request.message))
                    return self._crisis_decision(reason, classifier_attempted=True)
            except Exception as exc:  # Provider and parse failures intentionally fail open.
                classifier_error = f"{type(exc).__name__}: {exc}"

        return SafetyDecision(
            signal_detected=False,
            already_locked=False,
            reason=None,
            recommended_action=RecommendedAction.CONTINUE,
            response_text=None,
            classifier_attempted=attempted,
            classifier_error=classifier_error,
        )

    @staticmethod
    def _crisis_decision(
        reason: str, already_locked: bool = False, classifier_attempted: bool = False
    ) -> SafetyDecision:
        return SafetyDecision(
            signal_detected=True,
            already_locked=already_locked,
            reason=reason,
            recommended_action=RecommendedAction.SHOW_RESOURCES_AND_RESTRICT_FLOW,
            response_text=CRISIS_RESPONSE_TEXT,
            classifier_attempted=classifier_attempted,
        )
