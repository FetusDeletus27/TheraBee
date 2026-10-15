"""Run with: python examples/synthetic_example.py after installing the package."""

from therabee_safety import InMemoryLockStorage, SafetyEngine, ScanRequest

engine = SafetyEngine(InMemoryLockStorage())
decision = engine.evaluate(
    ScanRequest(
        subject_id="example-user-not-a-real-person",
        session_id="example-session",
        message="I want to die",  # Synthetic test input.
    )
)
print(f"signal_detected={decision.signal_detected}")
print(f"recommended_action={decision.recommended_action.value}")
print(f"action_performed={decision.action_performed}")
print(decision.response_text or "No resource response recommended.")
