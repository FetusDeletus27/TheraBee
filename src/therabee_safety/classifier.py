"""Optional classifier contracts and a dependency-free JSON adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Protocol


CLASSIFIER_PROMPT = """You are a crisis detection safety system for a mental health chatbot used by teens.

Your ONLY job is to determine if the following message indicates:
1. Suicidal ideation or intent
2. Active self-harm or plans to self-harm
3. Intent to harm others
4. Immediate physical danger

You must respond with ONLY a JSON object:
{"crisis": true, "reason": "brief explanation"}
or
{"crisis": false}

Be cautious but NOT overly sensitive. Consider context:
- General sadness, venting, or frustration is NOT a crisis
- Hypothetical or academic discussion of death is NOT a crisis
- Song lyrics quoted obviously are NOT a crisis
- Past tense descriptions without current intent are NOT a crisis
- NEGATED statements like "it's not like I'm gonna kill myself" or "I'm not suicidal or anything" are NOT a crisis
- Casual dismissals with "lol", "jk", "just kidding", "or anything" are usually NOT a crisis
- Statements where the person explicitly denies ideation are NOT a crisis

DO flag:
- Any expression of current intent or plan to harm self or others
- Active suicidal thinking ("I keep thinking about ending it")
- Urgency indicators ("tonight", "right now", "I've decided")
- Acquiring means ("I got pills", "I found a gun")
- Even if phrased casually, if there's genuine current intent, flag it

Message to evaluate:
"{message}"
"""


@dataclass(frozen=True, slots=True)
class Classification:
    crisis: bool
    reason: str | None = None


class CrisisClassifier(Protocol):
    def classify(self, message: str) -> Classification:
        """Classify one message. Implementations may raise on provider failure."""


class JsonCallableClassifier:
    """Adapt any caller that accepts a prompt and returns JSON text.

    The caller is supplied by the integrator. This package performs no network I/O
    and has no dependency on a model vendor.
    """

    def __init__(self, caller: Callable[[str], str]) -> None:
        self._caller = caller

    def classify(self, message: str) -> Classification:
        content = self._caller(CLASSIFIER_PROMPT.replace("{message}", message)).strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(content)
        if not isinstance(data, dict) or not isinstance(data.get("crisis", False), bool):
            raise ValueError("classifier response must contain a boolean 'crisis'")
        reason = data.get("reason")
        return Classification(data.get("crisis", False), str(reason) if reason is not None else None)
