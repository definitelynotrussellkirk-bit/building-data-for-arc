# Working notes: 4d0f228177b0

## Current design

The canonical generator remains unchanged and its exact selected Racket program is the default setting. The native parametric family adds one episode-fixed parameter, `finish`:

- `canonical`: execute the original cue expansion only.
- `first_hit_payload`: execute the canonical expansion, then inspect the yellow crossing ray produced by that expansion. The first adjacent payload color (`7` or `9`) in row-major yellow-cell order becomes an intermediate selector; every cell of that color in the expanded grid is recolored cyan (`8`).

This gives a real `A -> input-derived intermediate -> B` dependency. Inputs are matched across settings for equal seed/count requests. Demonstrations and queries are independent prefixes with limits of 2–6 and 1–4, and four distinct queries are retained for one-at-a-time presentation.

## Teaching and sampling decisions

The two-demo minimum deliberately crosses vertical cue colors `3` and `6`, first-hit colors `7` and `9`, remote selected payloads, later opposite-color hits, and cases where the unselected payload is globally more frequent. The four-query bank includes active `3` and `6` crossings, an inactive no-yellow case, and a substantive dense 30×30 boundary-touching case.

Declared semantic rivals cover canonical-only/B-before-A, fixed payload colors, recoloring both colors, last-hit selection, global majority, row-major first payload, local-component-only recoloring, and adjacent-ray-only recoloring.

## Findings and repairs

1. A remote payload could initially land one column left of the `2` cue. The canonical rule then treated it as the rightmost non-`2` cue, changing the horizontal center and suppressing the intended yellow ray. Remote placement now excludes the canonical center-selection hazard interval.
2. The first two demonstrations initially allowed a row-major-first-payload shortcut because the selected remote component was always encountered first. Remote ordering now crosses that nuisance feature while preserving the intended first yellow-ray hit.
3. The reusable crossed-control audit initially asserted that every *input* selected-color cell must become cyan. That was too strong when Step A legitimately overwrote an input payload cell. The audit now checks every selected-color cell remaining in the Step-A intermediate, matching the stated sequential semantics.
4. The inherited root-level test uses a machine-specific canonical path, but that file is outside this packet's editable source scope. A portable equivalent now lives in `tests/test_base_portable.py` and resolves the repository and canonical ledger through `reviewer_support`; the inherited file remains byte-for-byte unchanged.

## Final bounded evidence

- Focused suite: 13 tests passed.
- Adversarial probe: 64 seeds, 768 episodes, 4,736 pairs, nine rivals refuted on every two-demo lesson, five certificate attacks rejected, 30×30 and boundary/inactive surfaces exercised.
- Exact-source protected Racket audit: 10 episodes and 96 evaluations with one surviving setting each.
- Native authoring preflight: 24 parametric labeled pairs, seven canonical pairs, and 32 protected-Racket evaluations.
- Causal witness: protected replay of `skip_a` changed 48 output cells.
- Public projection: 16 single-query views, four first-turn cases, and 24 private-field invariance checks passed.

These are reviewer authoring results, not owner acceptance or training admission. The finite rival bank and sampled seeds do not prove universal uniqueness, and a solver may reproduce the canonical geometry without literally materializing an intermediate grid.
