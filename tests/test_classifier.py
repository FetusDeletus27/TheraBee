import pytest

from therabee_safety import JsonCallableClassifier


def test_json_adapter_accepts_fenced_json() -> None:
    result = JsonCallableClassifier(lambda _: '```json\n{"crisis": true, "reason": "synthetic"}\n```').classify("text")
    assert result.crisis and result.reason == "synthetic"


@pytest.mark.parametrize("response", ['{"crisis": "yes"}', '{"reason": "synthetic"}', '[]'])
def test_json_adapter_rejects_missing_or_non_boolean_crisis_flag(response: str) -> None:
    with pytest.raises(ValueError, match="boolean 'crisis'"):
        JsonCallableClassifier(lambda _: response).classify("text")
