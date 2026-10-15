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

Implement `CrisisClassifier.classify(message) -> Classification`, or wrap a caller with `JsonCallableClassifier`. The caller receives the retained source prompt and returns JSON text. The package does not select a provider, model, transport, credentials, or paid service.

The classifier is attempted only when `len(message.strip()) > 20`, preserving the source threshold. Classifier exceptions and malformed JSON are reported in `SafetyDecision.classifier_error` and otherwise fail open, preserving the source monitor's effective behavior. This means processing continues and no lock recommendation is stored. Integrators should explicitly assess whether that failure policy is acceptable.

### Integration contract

`SafetyEngine.evaluate` reads lock state first. An existing lock or a new signal returns `SHOW_RESOURCES_AND_RESTRICT_FLOW` and the resource text. The host application must implement any restriction, navigation, notification, audit, authentication, persistence, or escalation. Storage read and write exceptions propagate so an infrastructure failure is not mistaken for a safe result.

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
