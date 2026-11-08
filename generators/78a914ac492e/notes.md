# Working notes: 78a914ac492e

## Current validator contract

`self_check` requires exactly one non-seed template and at least one seed,
classifying multicolor 8-connected objects with the canonical rule's per-color
rectangle test. Merely counting colors admitted the built-in `no_template`
fixture (canonical Racket error) and `no_seeds` fixture (identity output).
The sampler and canonical rule are unchanged. Canonical expansion explicitly
clips at the grid boundary; clipping by itself is not a validator defect.

Bounded evidence: `checks/78a914ac492e-robustness/before.json` reproduced both
false accepts on generator SHA-256
`f65bbe96750f5e50a5023b28fbb4e91841bc8b856cfe86b8b12b0afe7c276e11`.
`after.json` in the same evidence folder checks three fixed normal draws and
three built-in degenerates through canonical Racket: 6/6 validator expectations
met. The focused regression changed from 2 failed / 5 passed to 7 passed,
including acceptance of all 10 canonical inputs (`before-tests.xml` and
`after-tests.xml`). Current generator SHA-256:
`adcff8de8656a8515150c595a81c263295826b4934b236cb9d1fd043aa65baa1`.
Both canonical rows share normalized rule hash `9d9305fdca24`; raw program
SHA-256 is `25e076b716a86afb95175a155094782168e74525253a712c04cd1909332a93ec`.

This was a missing-object validation check, not a full semantic validator review.
Other controls, broad seed coverage, label overlap/order behavior, and teaching
distribution were not audited. Invalid fixtures still fail or yield identity
when sent directly to the unchanged reference rule without validation.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric decision — `scale_basis`

The proposed family preserves the source task's object roles: one non-rectangular two-color template is copied at each rectangular seed, the template accent is recolored from the seed, and placement remains anchored by the shared color. The episode-fixed parameter changes only the isotropic scale basis:

- `longer_side` uses `max(seed_common_height, seed_common_width)` and is the exact canonical/default Racket source (`9d9305fdca24`, whitespace-normalized).
- `shorter_side` replaces that single scale expression with `min(...)`; all other Racket text and behavior are retained.

Asymmetric common-color seed rectangles make the settings causally distinguishable. Every generated demonstration and query is checked to produce different outputs under the two rules, while matched seeds/settings use identical inputs.

## Teaching and export decisions

The sampler is constructive and supports 2–6 demonstrations with four fixed query profiles. The query set includes mixed orientations/scales, a three-seed scene, and a 30×30 boundary-contact scene. Every label is executed in protected Racket and cross-checked against an independent Python mirror.

Private episodes retain the chosen setting, exact program, query answers, both-setting labels, sampling metadata, and source hashes. Public projection removes all of those fields and hashes only visible challenge bytes. Four controller-side files expose one query at a time; no future query or total-count hint is serialized, and the first turn equals the ordinary single-query projection.

The selected production generator and canonical row are unchanged. The prototype is marked `proposed`, `training_admitted: false`, and requires separate qualification/acceptance.

## Focused evidence and limits

- `tests/test_parametric_scale_basis.py`: 12 focused tests, including both real Racket programs, 2/3/6-demo bounds, exact four queries, 30×30 boundary content, public/private separation, adapter contract, and tamper rejection.
- `workspace/parametric/evidence/current/verification.json`: compact receipts for a Racket-replayed `longer_side`/2-demo export and a Racket-replayed `shorter_side`/6-demo export.
- Full materialized examples are retained under packet `checks/78a914ac492e-parametric/` rather than duplicated inside the task home.

These checks establish the bounded contract and finite teaching distinction only. They do not certify universal induction, owner acceptance, or training suitability.
