# TheraBee Safety

A small Python package extracted from TheraBee's existing crisis monitor. It provides deterministic phrase detection, an optional classifier boundary, a storage boundary, and typed decisions for an integrating application.

This is safety-supporting software, not a medical device. It has **not been clinically validated**, provides **no guarantee** of detecting a crisis or avoiding false positives, and performs **no action**. It does not contact emergency services, a hotline, caregivers, or any other person. An application must decide how to show resources, restrict a flow, obtain human review, or take any other action.

## Features

- Pure, deterministic, negation-aware keyword and regular-expression scanner
- Original phrase list and first-match behavior preserved where practical
- Typed request, decision, classifier, and lock-record interfaces
- Optional vendor-neutral classifier protocol and JSON callable adapter
- Thread-safe in-memory storage with no SQLite, UI, HTTP, or session framework dependency
- US resource response text carried over from the source monitor
- No runtime third-party dependencies

## Install

Requires Python 3.10 or later.

```console
python -m pip install .
```

For tests:

```console
python -m pip install -e ".[test]"
python -m pytest
```

## Usage

```python
from therabee_safety import InMemoryLockStorage, SafetyEngine, ScanRequest

engine = SafetyEngine(InMemoryLockStorage())
decision = engine.evaluate(ScanRequest(
    subject_id="pseudonymous-user-id",
    session_id="session-id",
    message="I want to die",
))

if decision.signal_detected:
    # The host, not this package, may display decision.response_text.
    print(decision.recommended_action.value)
assert decision.action_performed is False
```

Run `python examples/synthetic_example.py` after installation for a synthetic demonstration.

### Optional classifier

Implement `CrisisClassifier.classify(message) -> Classification`, or wrap a caller with `JsonCallableClassifier`. The caller receives a crisis-assessment prompt and JSON-encoded message payload and returns JSON text. The package does not select a provider, model, transport, credentials, or paid service.

Without conversation context, the classifier is attempted only when `len(message.strip()) > 20`. JSON responses must include a boolean `crisis` field. Provider exceptions, including timeouts raised by the caller, and invalid classifier responses set `classifier_attempted=True` and report the exception type in `SafetyDecision.classifier_error`. The decision excludes the exception message, which may contain sensitive provider or user data. A successful `{"crisis": false}` leaves `classifier_error` unset.

On a classifier error, the engine recommends `CONTINUE` and stores no lock. The host can check `classifier_error` and apply its own fallback.

### Context-aware assessment (New addition as of 11/13)

`ScanRequest` accepts optional `prior_messages`, a tuple of prior **user** messages
in chronological order. The host must supply only messages belonging to the same
subject and session; the package does not retrieve or verify conversation history.
Do not include system instructions or assistant messages in this field.

```python
request = ScanRequest(
    subject_id="synthetic-user",
    session_id="synthetic-session",
    message="Tonight.",
    prior_messages=("When will you finish your homework?",),
)
```

`JsonCallableClassifier` implements the optional
`ContextualCrisisClassifier.classify_with_context(message, prior_messages)` protocol.
It sends the latest six prior messages, each truncated to its first 500 characters,
alongside the full current message in a JSON-encoded prompt payload. It does not
retain history between calls. The host's caller may transmit or retain this payload;
review provider handling before sending sensitive data. The engine applies the same
history limits before calling custom contextual adapters. Prompt instructions label the payload as
untrusted data, but do not guarantee resistance to prompt injection.

When a contextual classifier and at least one nonblank prior message are supplied,
nonblank short follow-ups can also reach classification. Empty current messages do
not. Existing single-message classifiers keep their original length threshold and
receive only the current message. Keyword hits and existing locks still take priority:
context never overrides a deterministic hit. History is not stored as a separate
field in lock records, and `message_excerpt` contains only the current message.
However, provider-generated reasons are returned and stored as before and can quote
history or other sensitive text. Hosts must treat both reasons and excerpts as
sensitive and apply appropriate retention and access controls.

The prompt asks the provider to interpret the current message in context, including
negation, quotation, historical references, and casual phrasing. Automated tests use
synthetic examples and mocked provider responses to check payloads, routing, and
error handling. They do **not** establish semantic accuracy or clinical validity.

### Labeled synthetic examples

`examples/ambiguous_examples.json` begins a small labeled set of synthetic
conversation examples for planned evaluation and comparison runs. Each entry has an
identifier, the current message, ordered prior messages, a boolean draft label, and
a neutral note explaining the label. The labels are draft annotations written by the
authors, **not** ground truth or clinical judgments; the corresponding test checks
only that the file matches this schema.

### Integration contract

`SafetyEngine.evaluate` reads lock state first. An existing lock or a new signal returns `SHOW_RESOURCES_AND_RESTRICT_FLOW` and the resource text. The host application must implement any restriction, navigation, notification, audit, authentication, persistence, or escalation. Storage read and write exceptions propagate, including failed writes after a positive classifier result.

## Behavior changes from the application

- A decision recommends action but never performs or claims to perform it.
- "Lock" storage is an abstract application-state record, not account enforcement.
- SQLite, SQLAlchemy models, FastAPI routes, Flutter marker matching, logging, global clients, and environment loading are excluded.
- No OpenAI dependency, provider model identifier, API call, or credential handling is included.
- Classifier failures remain fail open but are now visible in the typed decision.
- Stored messages remain truncated to 500 characters, but the included storage is memory-only.
- Timestamps are timezone-aware UTC values rather than naive ISO strings.
- The original hardcoded development unlock key and client-embedded key are excluded.

## Limitations

- Negation handling is local pattern matching, not language understanding (temporary)
- The response resources are US-specific at present.
- In-memory state is lost at process exit and is not shared between workers.
- No guarantees are made about safety, accuracy, availability, suitability, or outcomes.

## Privacy and security

Use pseudonymous subject IDs and minimize message retention. Do not log raw messages by default. Apply encryption, access control, retention limits, deletion procedures, incident response, and applicable consent rules in the host. Never place secrets in source code, mobile clients, examples, logs, or test fixtures. Protect unlock and administrative operations with server-side authorization, audit, and rate limits.

The available repository identified Finn Sommer and Olutayo Oyewusi for attribution, but did not provide a clear copyright statement. `NOTICE` therefore attributes the project without asserting ownership.

## License

Apache License 2.0. See `LICENSE` and `NOTICE`.
