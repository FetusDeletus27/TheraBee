import pytest

from therabee_safety import JsonCallableClassifier


def test_json_adapter_accepts_fenced_json() -> None:
    result = JsonCallableClassifier(lambda _: '```json\n{"crisis": true, "reason": "synthetic"}\n```').classify("text")
    assert result.crisis and result.reason == "synthetic"


def test_json_adapter_rejects_invalid_shape() -> None:
    with pytest.raises(ValueError):
        JsonCallableClassifier(lambda _: '{"crisis": "yes"}').classify("text")
