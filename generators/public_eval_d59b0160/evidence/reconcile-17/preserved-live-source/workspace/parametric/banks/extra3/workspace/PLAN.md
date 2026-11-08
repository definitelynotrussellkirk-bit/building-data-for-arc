# Color-key panel erasure implementation plan

Goal: reconstruct the supplied general rule, then build a portable two-setting family.
Canonical: erase each 4-connected non-orange panel containing all distinct key colors.
Alternative: seed that erasure, then propagate through shared non-key colors until closure.
Preserve originals and gold; no registration, acceptance, or shared source changes.

Approaches: a one-pass any/all switch is too shallow; a sequential palette cascade retains
the original all-key decision and adds an input-dependent graph closure. Chosen by author.
An isolated extracted packet is the workspace (no Git metadata).

- [x] Write failing original-label, parameter/count, privacy, rival, and portability tests.
- [x] Implement engine, Racket programs, thin adapter, and generated standalone sampler.
- [x] Replay all originals; test meaningful rivals including partial-key, multiplicity,
  one-wave, global-palette, and 8-connectivity mistakes; repair concrete findings.
- [x] Run current-source preflight, 64-seed audit, strict public export checks,
  protected causal witness, and shared witness replay.
- Final handoff: retain self-review, patch reconstruction and package validation in WORK/checks/final/.

Review focus: frame excluded from objects; key multiplicity ignored; black cells remain
part of a multicolor panel; diagonal-only contacts stay separate; palette propagation
excludes key colors; colors/roles/positions are shuffled; four queries shuffled before
prefix; no external native resources or ordinary-generator imports.

Ruling: reuse the previous task-local verifier and public-file validator, not its results.
Ruling: no separate reviewer tool is available; author self-review is explicitly weaker.
