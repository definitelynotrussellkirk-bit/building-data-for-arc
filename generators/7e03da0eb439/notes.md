# Working notes: 7e03da0eb439

## 2026-10-26 parametric build, adversarial round 2

The production generator and exact canonical rule remain unchanged. The native family is under `workspace/parametric/`:

- `trigger_mode=color_2` is the exact canonical rule: self-tile the input into each output block whose corresponding input cell is color 2.
- `trigger_mode=center_cue` reads the unique center cell of an odd-square input as step A, binds that input-dependent color as the intermediate, then self-tiles at every cell matching that cue as step B.

The first build fixed the obvious historical shortcut `value > 1`, but a broader search found a genuine remaining teaching defect: for some seeds, fixed non-center cue readers and global/row/column modal cue readers fit both demonstrations while changing all four queries. Root cause was independent D4 transforms on the teaching pair, which destroyed the intended cross-example coordinate certificate.

The repaired pair now shares one seed-dependent D4 transform. Its color-2 coordinate sets are disjoint, while its center-cue coordinate sets intersect only at the center. Distinct modal distractors and line layouts reject every global and normalized row/column mode. The declared bank contains 40 rivals: 8 fixed non-center anchors, 21 global/line modes, 8 fixed colors, and 3 broad shortcuts.

Fresh bounded evidence:

- 57 focused behavioral tests pass, including seven-seed regressions for every non-center anchor and every global/row/column mode.
- `probe.py` passes 70/70 jobs over seeds `0,1,2,9,17,23,100`, both settings, demo counts 2..6, and four queries.
- Settings share inputs, one-query requests are prefixes of four-query requests, all 40 declared rivals are rejected, and the coordinate certificate holds at every audited seed.
- Maximum lawful geometry remains 5×5 input → 25×25 output; exact 30×30 is impossible for this self-tiling family under the ARC dimension bound.

Source inventory: `workspace/parametric/evidence/manifest.json`.
Protected-Racket preflight, causal witness, public projection, and first-turn receipts are regenerated after this source inventory in the return package. Those are authoring evidence only; owner review, native acceptance, and training admission remain pending and are not claimed.
