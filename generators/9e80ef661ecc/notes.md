# Working notes: 9e80ef661ecc

## Source and prior evidence

- Assignment: `review-1926437c3fb346bd`.
- Baseline generator SHA-256: `06ee378b8c6b28f10507ee95745f5d1f2a41222fd461a8a9ab2c5e0549f6fc54`.
- Canonical selected rule hash: `609d24e8c088`.
- No prior selected-task return was used as a lead; associated notes were empty.
- Required blind solve `a20ecf84f041` completed before opening this task: one revision, 3/3 visible examples, exposure no, reference consulted no.

## Baseline findings

The generator implemented the wrong transformation: crop each component, sort
by hole count, then pack. The selected Racket authority preserves positions and
recolors same-color 4-connected objects by topological hole count. Baseline also
merged touching nonzero colors, rejected a canonical input, omitted `RULE_HASH`,
and advertised dead or incompatible overrides.

Completed before battery: 6 green, 1 advisory, 5 failed (lint, self-check,
defect lint, profile floor, override). Earlier interrupted setup runs are
retained separately and are not used for claims.

## Repair decisions

- Preserve Racket; replace Python generator.
- Same-color 4-connectivity defines objects; different touching colors remain separate.
- Hole count = enclosed complement regions in the object's bounding box.
- Mapping: 0→2, 1→3, 2→4, 3→6, 4+→9.
- Four scheduled profiles: canonical, equal_features, touching, extended.
- Keep only one truthful exact axis: `profile`.
- Declare foreground-area, enclosed-cell, canonical-range, global-color,
  all-nonzero-connectivity, and identity rivals.
- One consolidated diagnostic witness avoids redundant Racket calls.
- Difficulty uses explicit palette rotations after defect lint exposed that
  keyed `GenCtx` RNG labels did not implicitly salt by band.

## Test-first record

The new task test suite was written before production replacement. Against the
baseline it produced 53 failures, 1 pass, and 1 skipped direct Racket check.
After implementation it produced 54 passes and 1 direct-environment skip; the
supported wrapped task-test stage later ran 55/55 tests with Racket available.

## Historical v3.0 evidence

- Final generator SHA-256: `759219d26fa48fd24298434b2d7234b2464296c8e31addfd5c70ed0a091217a2`.
- Full after battery: 12/12 stages green.
- Wrapped task tests: 55 passed in 4.57s.
- Semantic smoke: 600/600 strict, 4/4 canonical accepted, 12/12 lessons identifiable.
- Final source-bound probe: 300/300 lessons identifiable against the six declared rivals; 1,500 inputs, 1,469 unique;
  zero strict/oracle/mirror failures; every named rival refuted in every lesson.
- Post-repair solve: one revision, 4/4 visible demonstrations; earlier exposure yes, reference consulted no.

## Historical v3.0 residual limitation

The generator uses a finite hand-designed mask library and fixed dimensions per
profile. Placement and palettes vary, and named feature shortcuts are explicitly
broken, but a literal template/profile memorizer remains possible. No universal
induction claim is made.

## Assigned audits

- `1b46e014e17c`: reproduced always-connected-template coverage gap with a validator-clean, Racket-backed disconnected-template counterexample.
- `2d585b947291`: reproduced global-color-frequency shortcut over 1,200 generated inputs and 4 canonical pairs; exact validator-clean counterexample is outside ordinary one-color-per-object generation.

## October 3 maintainer follow-up — v3.1.0

The owner relayed a concrete adversarial review. An independent replay of the
previous source on the same 300-lesson sampler confirmed that all six newly
proposed rivals survived every lesson: row-only gaps, row/column gaps,
8-connected holes, 8-connected objects, four-only mapping and the frozen old
shape library. Its 1,469 distinct raw grids collapse to six object-multiset
signatures and nine D4-normalized shapes. The old ZIP and receipts are unchanged.

Replaced the equal-feature masks with matched 4×4, area-14 witnesses, including
diagonal cavities. Added same-color diagonal object contact, explicit five- and
six-hole examples, procedural connected masks, boundary notches, multi-cell
cavities, D4 transforms, duplicated counts and border placement. Profiles now
share canvas dimensions and are recognized structurally. Small public-like
examples remain in half of the canonical-profile draws. Global RNG behavior and
the Racket authority remain unchanged.

Measured follow-up: ten new regressions failed against v3.0; the full task suite
now passes 66 tests, including 70 independently sampled-mask Racket comparisons.
The 300-lesson, 1,500-input source-bound Racket census has zero parity/grammar
failures and refutes all twelve declared rivals in every lesson. It reports
1,500 unique raw grids, 943 scene multisets and 3,908 normalized object shapes.
Both task-local diversity floors pass in every band.

Evidence is compact under `evidence/topology-20261003/`; the new approval receipt
links `evidence/maintainer-topology-20261003.json`. Previous authored solves remain
bound to v3.0; no new solve, model gain or training admission is claimed.

Limits: the rival set is finite; masks start from bounded rectangles; diagnostic
scenes remain deliberately structured. The scene metric removes spatial and
color relations, so its name is not a claim of exhaustive scene topology.
Profile/rival evidence is regression coverage, not universal identifiability.
