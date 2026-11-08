# Working notes: 60b3a4fe8090

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review repair — 2026-10-24

Baseline generator SHA-256 `140eb592f4225324382fcaabc5eed65319d10bc52b8475ecadc7256e469ec5cd`
used only colors 5..8 for room objects, required 4-connectivity and size 2..4,
and rejected all five canonical inputs. The retained audit's slide-every-blob
shortcut therefore matched the generated domain while disagreeing with the
selected Racket rule on canonical command-colored objects.

Version 1.2.0 pins `RULE_HASH = ddfddf7b7076` and generates a command
permutation, four distinct object colors, 1..3 ignored colors from 1..4, and at
least one movable color from 5..8. The object grammar now covers sizes 2..5 and
8-connected diagonal forms. Ignored objects are placed away from their
commanded edge, making the executable `slide_all_colored_objects` rival disagree
on every generated witness. `self_check` owns every canonical input, including
the one attached colored divider spill, while rejecting unattached wall damage.
The only exact public controls are now the observable
`ignored_object_count` and `object_size`; unknown and coercive overrides fail
closed.

The independent Python mirror, rival, witness claim and lesson competitor are
exercised by task-local tests and the strict semantic gate. No canonical Racket
source or selected base authority changed. Final generator SHA-256:
`a52ce69cb0cc3be497240d0272799ad97ea499372956bf441f7a13ac0b5352d2`.
Focused evidence is under `WORK/checks/60b3a4fe8090-*` in the return.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-21d7702b7080069d:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `140eb592f4225324382fcaabc5eed65319d10bc52b8475ecadc7256e469ec5cd`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted sourcea52ce69cb0cc3be497240d0272799ad97ea499372956bf441f7a13ac0b5352d2 generates, validates and teaches command-colored distractors instead of excluding1–4.18task tests and source-bound strict semantic/override checks are reviewer-reported; canonical Racket unchanged.

### Assessment or prior finding

## 60b3a4fe8090

**Reproduced distribution/validator defect; no audit-target files changed.** Generator SHA-256 is `140eb592f4225324382fcaabc5eed65319d10bc52b8475ecadc7256e469ec5cd`; canonical Racket rule hash is `ddfddf7b7076`.

The generator hard-codes movable object colors to `5..8`, so its ordinary distribution never contains a non-command blob colored `1..4`. Canonical authority examples do contain such blobs, and the selected Racket rule deliberately excludes all colors `1..4` from movable room objects. This distinction matters: a plausible wrong solver can read each room command and slide **every** remaining nonzero/non-wall blob regardless of color. That rival is answer-equivalent on the generated domain, but not on the canonical task.

Concrete counterexample: canonical training pair 0. The supported Racket application deletes/ignores a color-4 blob in the upper-left room and a color-3 blob in the lower-right room. The rival slides them, producing seven wrong colored cells: `(2,4)`, `(2,5)`, `(3,4)` in color 4 and `(7,8)`, `(7,9)`, `(8,8)`, `(8,9)` in color 3.

The exact canonical input is **outside the current generator distribution and rejected by its validator** (`room at (0,0): expected exactly one object component, got 0`; `room at (6,6): expected exactly one object component, got 0`). More broadly, `self_check` rejects all five canonical pairs, with error counts `2,2,3,2,3`. A 100-draw probe (`seed=777`, medium, sample indices 0–99) found zero command-colored non-command cells and zero generated self-check failures; source inspection independently guarantees this because `avail_colors = [5,6,7,8]`.

Evidence:

- `checks/audit/60b3a4fe8090/input.json`
- `checks/audit/60b3a4fe8090/racket.json`
- `checks/audit/60b3a4fe8090/counterexample.json`

Racket reproduction, from `packet_root`:

```sh
python3 run_with_racket.py python3 -m arcpuzzles apply 60b3a4fe8090 \
  --input ../checks/audit/60b3a4fe8090/input.json \
  --out ../checks/audit/60b3a4fe8090/racket.json
```

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-21d7702b7080069d-v0001/audit_assets.json), manifest SHA-256 `b3f043de37cc0ee32453e5bc2a6701507ec771868bb5f4710c5fffa1aa254145`.
<!-- arcpuzzles-current-audit-assessment:end -->
