# Working notes: ec23789c7821

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current decision

Reviewer disposition: **ready for owner source review and fresh native acceptance**. This does not grant owner acceptance or training admission.

Current generator: version `2.1.0`, SHA-256 `162a73c18539242c15947b827ad9b1c04db7aa55a378400f00923ebc473134e3`. Canonical rule hash remains `281bfb5a3049`; canonical program SHA-256 remains `281bfb5a3049e425333758bdc993a939df6f80bbacf5d74910da2812f1e8a36d`.

## Defect and repair

A retained audit of 600 ordinary draws found 2,372 target runs but zero preserved non-target components, so a stronger wrong rule—transform targets and discard everything else—fit the entire ordinary domain. Exact endpoint overrides also failed, and the source lacked `RULE_HASH` and `self_check`. The repair always includes preserved boundary cues and a length-two distractor, honors exact dimensions/counts/palette controls, uses constructive nonmerging placement, fails closed on invalid requests, and adds a literal rule mirror plus validation.

## Parametric design

- Default: `finish=vertical`, byte-exact canonical program.
- Alternative: `finish=plus`.
- A: apply the canonical H3→V3 conversion and preserve all non-target colored cells.
- Intermediate: that complete canonical first-pass grid.
- B: detect exact vertical triples in the intermediate and add same-color left/right arms at their centers.
- Dependency: B receives target orientation, center, and color from A-created V3s; applying B directly to the raw horizontal-run input misses them.

The hidden-setting-independent sampler supports 2–6 demonstrations and 1–4 prefix-stable queries, always stores four distinct queries, preserves distractors, separates targets, and places substantive content in every quadrant of the 30×30 query. Two demonstrations distinguish the finite settings.

The second review pass found and repaired a lower-bound defect in that sampler. At 7-column widths the old candidate stride could leave fewer than two targets, and the fixed side distractor could overwrite a row-2 target. Candidate spacing now supports two separated triples at 7×7, and the side distractor occupies rows outside the target lattice. The certificate now also enforces count bounds and rejects duplicate inputs across both splits.

## Retained checks

Focused/staged tests passed **26 checks**. Native preflight passed 4 jobs, 24 parametric labels, 4 canonical pairs, and 32 protected-Racket evaluations. An exhaustive sweep covered every 7×7 through 30×30 rectangle with 10 seeds each (5,760 generated cases): every case retained at least two targets and produced distinct vertical/plus labels. Representative boundary shapes also matched protected Racket. The causal witness is `checks/ec23789c7821/causal/witness.json`; projection/privacy evidence is `checks/ec23789c7821/first-turn-final.json`; the exhaustive audit is `checks/round2-boundary-audit.json`.

## Next action and limits

Owner should review and integrate the exact bound source, rerun native qualification, and perform fresh acceptance. Finite generated cases, exhaustive declared-shape sampling, and one replayed skip-A witness do not prove universal uniqueness or training eligibility.
