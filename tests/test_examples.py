"""Schema checks for the labeled synthetic example set.

These verify the data file's structure only. They do not evaluate any
classifier, and the labels are draft annotations, not ground truth.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EXAMPLES_PATH = Path(__file__).resolve().parents[1] / "examples" / "ambiguous_examples.json"
REQUIRED_KEYS = {"id", "message", "prior_messages", "label", "note"}


@pytest.fixture(scope="module")
def examples() -> list[dict]:
    data = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
    return data["examples"]


def test_example_set_is_small_and_nonempty(examples: list[dict]) -> None:
    assert 0 < len(examples) <= 20


def test_every_example_matches_the_documented_schema(examples: list[dict]) -> None:
    for example in examples:
        assert set(example) == REQUIRED_KEYS, example.get("id")
        assert isinstance(example["id"], str) and example["id"]
        assert isinstance(example["message"], str) and example["message"].strip()
        assert isinstance(example["prior_messages"], list)
        assert all(
            isinstance(text, str) and text.strip() for text in example["prior_messages"]
        )
        assert isinstance(example["label"], bool)
        assert isinstance(example["note"], str) and example["note"].strip()


def test_example_ids_are_unique(examples: list[dict]) -> None:
    identifiers = [example["id"] for example in examples]
    assert len(identifiers) == len(set(identifiers))


def test_both_labels_are_represented(examples: list[dict]) -> None:
    labels = {example["label"] for example in examples}
    assert labels == {True, False}
