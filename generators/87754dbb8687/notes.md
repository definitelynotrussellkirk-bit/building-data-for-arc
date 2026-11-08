# Working notes: 87754dbb8687

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current decision

Reviewer disposition: **ready for owner source review and fresh native acceptance**. This does not grant owner acceptance or training admission.

Current generator: version `1.2.0`, SHA-256 `cf09c7617535480b0bff7e1f7f7d2e67b11c9ea956251d7b41db1b60d285adae`. Canonical rule hash remains `0ac662ce40c7`; canonical program SHA-256 remains `ced3a6da403b4f237e3985a361e1067aebd9076b263658e5f9bff813d4f3bca0`.

## Defect and repair

The retained base did not reliably honor dimension/control endpoints, omitted color 1 from ordinary support, and lacked a pinned rule hash/self-check surface. The repair adds strict exact controls, full nonzero palette support, explicit incompatibility errors, deterministic sampling, a literal Python rule mirror, and `self_check`, without changing canonical semantics.

## Parametric design

- Default: `output_mode=equality`, byte-exact canonical program.
- Alternative: `output_mode=match_boxes`.
- A: construct the canonical row-header/column-header equality matrix.
- Intermediate: the full canonical equality grid and its input-dependent matched-cell geometry.
- B: for each nonzero matched color, fill the bounding box of its cells.
- Dependency: B derives both colors and coordinates from A; feeding B the raw header grid changes dimensions and painted regions.

The setting-independent sampler supports 2–6 demonstrations and 1–4 prefix-stable queries, always materializes four distinct queries, and includes a 30×30 query with spatially separated match groups in all four quadrants. Two demonstrations constructively distinguish the finite settings.

The second review pass hardened the episode certificate: it now enforces the declared demonstration/query bounds and rejects duplicate inputs across both splits. Stage B now validates that its intermediate is a nonempty rectangular ARC grid within 30×30 before deriving any geometry.

## Retained checks

Focused/staged tests passed **21 checks**. Native preflight passed 4 jobs, 24 parametric labels, 5 canonical pairs, and 32 protected-Racket evaluations. The cross-family boundary audit exercised all 676 supported dimensions with 10 seeds each (6,760 generated cases), plus representative protected-Racket edge shapes. The causal witness is `checks/87754dbb8687/causal/witness.json`; projection/privacy evidence is `checks/87754dbb8687/first-turn-final.json`; the exhaustive audit is `checks/round2-boundary-audit.json`.

## Next action and limits

Owner should review and integrate the exact bound source, rerun native qualification, and perform fresh acceptance. Finite tests, exhaustive declared-shape sampling, and one replayed ablation establish the exercised contract, not universal lesson uniqueness or training eligibility.
