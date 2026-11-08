# Adversarial witness — ticket-055b319647a7e42e

**Status:** finding (`A2-CANONICAL-SHORTCUT-CONTRACT`).

Source SHA-256 `22b8362e7f78589ab539b237fd4dfda5300caaf4e070f46dcafc2753c01a9575` declares `identity` inside `CANONICAL_SHORTCUTS`, but that function fits **0/5** canonical pairs. Canonical pair 0 is lawful (`self_check == []`); the live Racket authority returns its tight 4x5 crop, while `identity` returns the original 8x9 input.

This reproduces the retained current-source finding with one bounded live probe. It is a declaration/gate-contract problem, not a label problem. The peer source was not modified, and this source-bound finding awaits maintainer assessment.

Evidence: `witness.json`, `racket-receipt.json`, `input.json`, `probe.py`, and `probe.log` in this directory. The two `probe-authoring-red*.log` files retain import-path preflight corrections before the final targeted run.
