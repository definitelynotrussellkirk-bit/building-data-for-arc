# Review workspace for 9686a12edc93

`reference_probe.py` is an independent task-local analyzer and Python mirror. It deliberately does not import implementation helpers from `generator.py`.

It can:

- classify clear, blocked, and unaligned exactly-two color pairs;
- compute the intended empty-output rule mirror;
- compute the canonical-fitting `ignore_clearance` rival;
- compute a copy-then-connect rival and exact differing cells;
- load either the selected generator or a source path supplied through `GENERATOR_UNDER_TEST`.

The selected Racket rule remains label authority. Use `arcpuzzles apply` for retained authority evidence; use this helper for focused tests, counterexample construction, and future source-bound audits.
