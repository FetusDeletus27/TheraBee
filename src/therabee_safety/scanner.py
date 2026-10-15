"""Deterministic, negation-aware crisis phrase scanning."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class KeywordHit:
    kind: str
    matched_text: str

    @property
    def reason(self) -> str:
        return f"{self.kind}: '{self.matched_text}'"


_NEGATION_PREFIXES: Final = (
    r"(it'?s\s+)?not\s+(like|that|as if)\s+.{0,20}",
    r"(i'?m\s+)?not\s+(going\s+to|gonna|about\s+to)\s+",
    r"(i\s+)?(would|wouldn'?t)\s+(never|not)\s+",
    r"(i\s+)?don'?t\s+(actually|really)\s+(want|plan)\s+to\s+",
    # The source intended this form, but its match begins at "want", leaving
    # only "I don't actually " in the prefix slice.
    r"(i\s+)?don'?t\s+(actually|really)\s+$",
    r"(i\s+)?never\s+(said|meant|want(ed)?)\s+.{0,10}",
    r"(not\s+)?saying\s+(i|that\s+i).{0,10}",
    r"i'?m\s+not\s+",
    r"it'?s\s+not\s+like\s+",
    r"i\s+don'?t\s+want\s+to\s+",
    r"no\s+one\s+is\s+going\s+to\s+",
    r"(lol|lmao|haha|jk|just\s+kidding|joking)",
)
_NEGATION_SUFFIXES: Final = (r"\s*(lol|lmao|haha|jk|just\s+kidding|joking|or\s+anything)",)

_CRISIS_PHRASES: Final = (
    r"\b(want(ing)?|going|gonna|gon|finna|plan(ning)?|think(ing)?( about)?|about)\s*(to\s+)?(kill|end|hurt)\s+(my\s*self|myself|my life|it all)\b",
    r"\bi'?m\s+(going\s+to|gonna|gon|finna|about\s+to)\s+(kill|end|hurt)\s+(my\s*self|myself|my life|it all)\b",
    r"\bsuicid(e|al|ing)\b",
    r"\b(don'?t|do not|dont)\s+want\s+to\s+(be\s+)?(alive|live|exist|here)\b",
    r"\b(wish|hope)\s+(i|I)\s+(was|were|could be)\s+dead\b",
    r"\b(better off|world.{0,15}better)\s+(without me|if i.{0,10}(gone|dead|died))\b",
    r"\bno\s+reason\s+to\s+(live|go on|keep going|stay)\b",
    r"\b(ready|prepared|planning)\s+to\s+(die|end it|leave this world)\b",
    r"\b(goodbye|good\s*bye)\s*(forever|for\s*good|cruel\s*world)\b",
    r"\b(cut(ting)?|burn(ing)?|hurt(ing)?)\s+(my\s*self|myself)\b",
    r"\b(self[- ]?harm|self[- ]?injur)\b",
    r"\bi'?m\s+(going\s+to|gonna|gon|finna)\s+hurt\s+myself\b",
    r"\b(want|going|gonna|gon|finna|plan(ning)?)\s*(to\s+)?(kill|hurt|harm)\s+(someone|them|him|her|people|everybody)\b",
    r"\b(shoot(ing)?|stab(bing)?|poison(ing)?)\s+(up|them|people|everyone|the school)\b",
    r"\b(i have|got)\s+(a\s+)?(gun|knife|pills|weapon|rope|noose)\b",
    r"\b(standing|sitting|going)\s+(on|to)\s+(the\s+)?(edge|bridge|ledge|roof|tracks)\b",
    r"\b(took|taking|swallowed)\s+(too many|all|a bunch of)\s+(pills|medication|meds)\b",
    r"\b(overdos|od'?d|od'?ing)\b",
)
_PATTERNS: Final = tuple(re.compile(value, re.IGNORECASE | re.MULTILINE) for value in _CRISIS_PHRASES)
_HARD_TRIGGERS: Final = (
    "i want to die", "i want to kill myself", "i'm going to kill myself",
    "im going to kill myself", "i am going to kill myself", "i'm gonna kill myself",
    "im gonna kill myself", "gonna kill myself", "i'm gon kill myself",
    "finna kill myself", "how to commit suicide", "how to kill myself",
    "suicide methods", "i took all the pills", "i'm about to jump",
    "im about to jump", "this is my suicide note", "goodbye forever",
    "i want to end it all", "i want to end my life", "i'm gonna end it",
    "i don't want to be alive", "i dont want to be alive", "i don't want to live",
    "i dont want to live", "kill myself",
)


def _has_negation_context(message: str, start: int, end: int) -> bool:
    lower = message.lower()
    prefix = lower[max(0, start - 60):start]
    suffix = lower[end:end + 30]
    return any(re.search(rule, prefix, re.IGNORECASE) for rule in _NEGATION_PREFIXES) or any(
        re.search(rule, suffix, re.IGNORECASE) for rule in _NEGATION_SUFFIXES
    )


def keyword_scan(message: str) -> KeywordHit | None:
    """Return the first deterministic hit, or ``None``. Input is not retained."""
    lower = message.lower().strip()
    for trigger in _HARD_TRIGGERS:
        index = lower.find(trigger)
        if index != -1 and not _has_negation_context(message, index, index + len(trigger)):
            return KeywordHit("hard_trigger", trigger)
    for pattern in _PATTERNS:
        match = pattern.search(message)
        if match and not _has_negation_context(message, match.start(), match.end()):
            return KeywordHit("pattern_match", match.group())
    return None
