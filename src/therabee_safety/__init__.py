"""Small, dependency-free crisis signal decision library."""

from .classifier import Classification, CrisisClassifier, JsonCallableClassifier
from .engine import CRISIS_RESPONSE_TEXT, RecommendedAction, SafetyDecision, SafetyEngine, ScanRequest
from .scanner import KeywordHit, keyword_scan
from .storage import InMemoryLockStorage, LockRecord, LockStorage

__all__ = [
    "CRISIS_RESPONSE_TEXT", "Classification", "CrisisClassifier", "InMemoryLockStorage",
    "JsonCallableClassifier", "KeywordHit", "LockRecord", "LockStorage", "RecommendedAction",
    "SafetyDecision", "SafetyEngine", "ScanRequest", "keyword_scan",
]
