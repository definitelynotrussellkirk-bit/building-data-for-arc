# Workspace

`reference_probe.py` is the reusable independent analyzer for this task. It can:

- load the selected or a frozen generator without importing implementation helpers;
- segment maximal equal-row groups and report profile, run heights, row kinds, palette, and two-step repeats;
- compute an independent intended output and six named rival outputs;
- load canonical pairs through portable `reviewer_support` paths; and
- invoke the actual canonical Racket program for parity checks.

The selected implementation is `../generator.py`; task regressions are in `../tests/test_generator.py`. Workspace drafts are never automatically selected.
