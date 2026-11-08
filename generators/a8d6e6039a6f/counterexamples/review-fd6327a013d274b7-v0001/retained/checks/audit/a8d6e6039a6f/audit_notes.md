## a8d6e6039a6f

**Finding: a naturally generated oversized template passes validation and overwrites gray frame borders.**
Severity: high. This is a generator domain defect and a validator false negative on the selected bytes. The finding is reproduced; no repair or audit-status change was made.

### Exact source binding

| Identity | Value |
| --- | --- |
| Selected generator | `generators/a8d6e6039a6f/generator.py`, version `4.0.0` |
| Generator SHA-256 | `d6a36459af5a75c32e37820d5e631fb078369d69ba2ff384edbd539811890fdd` |
| Canonical normalized rule hash | `9921e422d6f8` |
| Raw canonical rule text SHA-256 | `250788bac4cbc9a82e250c8766948ad99609c2c2afcc8e9062d0f7181c4886c0` |
| Public runtime executable-wrapper SHA-256 | `8f7ad27f3ec05b381b8d1f929308c00166b54d99eb566dc902c502b73159d67c` |
| Catalog approval at execution | `approved=true`, `train_safety=reviewed_safe`; an inherited label, not this audit's approval |
| Existing task review index | `evidence/review_index.json` absent |

The existing `notes.md` is a placeholder. The current imported associated note describes preserving the gray frames and fitting centered stamps. The canonical examples and the generator invariant at line 30 also support that contract.

### Natural counterexample

`generate(seed=14, sample_index=0, difficulty=None)` with **no overrides** returns the witness. `observe_overrides` recovers `{"scene_code": 172945}`, and `generate(0, 0, scene_code=172945)` reconstructs the identical grid.

The 14-by-21 input uses layout 4, three gray frames with 2-by-2 interiors, keys `(1, 2, 3)`, template pattern 19, palette `(6, 7)`, key spot 2, and loose placement 1. Its template crop is:

```json
[[6,7,6],
 [6,0,0]]
```

The identity and horizontal-reflection stamps are 2-by-3; the clockwise-rotation stamp is 3-by-2. None fits its 2-by-2 destination interior.

The selected generator's `self_check` returns `[]`. Public `Catalog.apply(..., reference="canonical", check_generator_domain=True)` also returns `generator_domain={"status":"valid","errors":[]}` and a well-formed output. Actual Racket execution changes these original frame-border cells, using zero-based row/column coordinates:

| Cell | Input | Racket output |
| --- | --- | --- |
| `(2, 12)` | 5 | 6 |
| `(4, 18)` | 5 | 6 |
| `(10, 12)` | 5 | 6 |
| `(11, 12)` | 5 | 6 |

The first frame's actual output crop is `[[5,5,5,5],[5,6,7,6],[5,6,0,5],[5,5,5,5]]`: the stamp replaces its right border. The Python `rule_mirror` agrees exactly with Racket on this witness. The issue is admission of an input outside the intended full-fit domain, not an asserted Python/Racket mismatch.

`checks/audit/a8d6e6039a6f/witness.json` retains the complete input, actual Racket output, and an independently implemented frame-preserving rival output. That rival applies the same transforms and placement while clipping colored cells to the frame interiors. It differs from Racket at the four cells above. It is a diagnostic comparator, not a claimed canonical answer: a 2-by-3 piece cannot fit completely in a 2-by-2 interior.

### Why the defect is admitted

`_make_layouts` at lines 239–282 enumerates both four-cell and five-cell outer frame sizes, then selects the first fourteen layouts of each frame-count branch. Twenty-two of the twenty-eight generalized layouts have 2-by-2 interiors. `LAYOUT_PATTERN_COUNTS` at lines 304–306 nevertheless enables all 256 patterns on every generalized layout. Of those patterns, 177 have shape 2-by-3 and 60 have shape 3-by-2.

`_analysis` at lines 622–651 verifies profile recovery and exact scene reconstruction, then computes `rule_mirror`; it never rejects a transformed template that exceeds an interior. `self_check` at lines 654–657 simply returns those errors. The mirror's `_paste_centered` at lines 499–512 and the canonical Racket stamp use a nonnegative placement offset without an interior-fit guard, so overflow reaches the gray border. This yields a valid ARC grid while violating the generator's explicit semantic invariant.

A finite census of all **172,800 declared layout/template/key-order profiles**, weighted by the declared key spots, twelve palettes, and four placements, identifies **48,052,224 of 61,489,152 scene codes (78.1475%)** as dimensionally infeasible. This is an exact census of the declared tables' dimensions. It is not a measurement of the natural draw distribution, a full per-scene execution, or proof that every remaining scene satisfies every other invariant. Full per-layout counts are in `checks/audit/a8d6e6039a6f/table_census.json`.

### Validation and limits

The retained probe executed **six actual Racket inputs** in one public `Catalog.apply` call:

- The natural seed-14 counterexample, accepted by both domain checks and overwriting the four recorded gray cells.
- A fitting generalized control with layout 13, pattern 19, and `scene_code=21382032`. Its 3-by-3 interiors preserve all gray borders, and the rival equals Racket.
- All four canonical train/test pairs. Every Racket result matches its recorded canonical output, is accepted by the domain check, and preserves gray frame borders.

No full battery, task-test stage, or exhaustive natural-seed sweep was run. The dimension census is independent of the six runtime executions. No source, rule, catalog, shared code, solve-lane file, approval, or audit-status record was changed. A repository Git-status check was attempted; this packet checkout has no Git metadata.

Recommended follow-up: restrict each layout to patterns whose transformed dimensions fit every destination, or provide larger interiors for the wider templates; additionally make the observational validator reject overflow. Preserve exact scene-code reconstruction and add this naturally scheduled witness as a regression. This audit intentionally supplies evidence without selecting or applying that repair.

### Reproduction and retained assets

Run from `WORK`:

```bash
.venv/bin/python3 run_with_racket.py "$PWD/.venv/bin/python3" ../checks/audit/a8d6e6039a6f/probe.py
```

The wrapper sets the payload working directory to `WORK/repo`. The probe asserts the exact generator hash, canonical raw rule hash, normalized rule hash, and executed wrapper hash before making source-bound findings. The verified run exits 0 and reports `issue_reproduced` with six Racket inputs checked. `commands.json` also discloses an initial probe-only hash-guard error, corrected by distinguishing canonical text from its executable wrapper.

Retain this whole focused directory:

- `checks/audit/a8d6e6039a6f/probe.py`
- `checks/audit/a8d6e6039a6f/evidence.json`
- `checks/audit/a8d6e6039a6f/witness.json`
- `checks/audit/a8d6e6039a6f/racket_apply.json`
- `checks/audit/a8d6e6039a6f/table_census.json`
- `checks/audit/a8d6e6039a6f/commands.json`
- `checks/audit/a8d6e6039a6f/audit_notes.md`
