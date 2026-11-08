# Bounded replay assessment — ticket-1ffefe8d9b1dae46

Status: **finding**. Consumer: `existing_audit_assessment`.

The source, audit index, assets manifest, canonical audit-record hash, and all four retained witness assets match the pinned identities. The exact retained witness uses seed `20261011`, sample index `7`, difficulty `medium`; the ticket seed is retained as allocation identity and was not substituted into the historical witness.

One targeted probe executed `replay.py` from `WORK/repo`, returned **0**, and took **0.104081 seconds**, measured around the child process. The complete absolute command, working directory, explicit environment, source and replay hashes, timestamp, and exit status are in `receipt.json`. Total authoring time was not measured and remains null. The original witness was executed with only its two output paths redirected into this ticket directory.

The new probe JSON matches the retained JSON, and the generated input matches the retained input byte for byte. On that 13-by-15 grid with 13 nonzero cells, `self_check` returns `expected 2-4 components, got 1` despite `single_component` being advertised and generated. The same replay confirms that an undeclared texture equals `plain` for the same seed, the four documented endpoints (`grid_h=10`, `grid_h=18`, `grid_w=12`, `grid_w=22`) raise `ValueError`, and `RULE_HASH` is absent.

Fresh canonical authority execution was attempted within the same bounded probe but blocked during the existing runner import by `ModuleNotFoundError: No module named 'scripts'`, before Racket was started. `authority.json` records that limitation. The hash-verified retained authority result records a successful 5-by-3 crop for exactly this input with rule hash `82b12cea1db8`; that is historical retained evidence, not a fresh authority result. No second probe, full audit battery, profile census, semantic gate, or authority parity sweep was run.

No production, shared, approval, audit-resolution, or policy files were changed. The existing audit remains `needs_triage`, source-bound, and reviewer-reported pending maintainer assessment.

## Suggested AUDIT.md paragraph

### 06789067e67f

The bounded supplementary ticket `ticket-1ffefe8d9b1dae46` reproduces the retained audit witness against source SHA-256 `b073dca45ab31a4ca9fe903aa6249d5e8ab3a459d7c5889b493142600b76dde5`. At seed `20261011`, sample index `7`, difficulty `medium`, advertised `texture="single_component"` produces a grid that its own `self_check` rejects with `expected 2-4 components, got 1`. The new `checks/tickets/ticket-1ffefe8d9b1dae46/probe.json` and input bytes exactly match their hash-verified retained originals. The same bounded replay reproduces unknown-texture acceptance, the four rejected advertised dimension endpoints, and missing `RULE_HASH`. The single targeted probe returned 0 in 0.104081 seconds; details are in `checks/tickets/ticket-1ffefe8d9b1dae46/receipt.json`. A fresh authority application was blocked by a missing `scripts` module before Racket execution; the separately retained, hash-verified authority result reports prior successful execution. This replay does not revalidate the prior battery claims and does not resolve or clear the existing audit.
