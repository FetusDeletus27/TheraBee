# Security and privacy notes

This package processes text that can contain highly sensitive health and safety information. It does not transmit data itself.

Integrators should:

- collect only necessary data and prefer pseudonymous identifiers;
- avoid raw-message logging and redact error, analytics, and tracing output;
- define retention, deletion, access, encryption, backup, breach, and legal-basis policies;
- treat use of any external classifier as disclosure to that provider;
- keep credentials server-side and out of source, mobile clients, logs, examples, and test data;
- authenticate and authorize administrative state changes server-side;
- audit access without storing unnecessary message content;
- verify resources and escalation plans for each supported jurisdiction;
- monitor classifier failures, because the preserved policy fails open;
- obtain qualified clinical, legal, privacy, and security review before deployment.

The in-memory store is for examples and tests. It is not durable, distributed, encrypted, or suitable as a production control by itself. A returned recommendation performs no action and must not be represented as an emergency notification.

Report suspected vulnerabilities privately to the maintainers through the repository's configured private security-reporting channel. Do not include real crisis messages or personal data in a public issue.
