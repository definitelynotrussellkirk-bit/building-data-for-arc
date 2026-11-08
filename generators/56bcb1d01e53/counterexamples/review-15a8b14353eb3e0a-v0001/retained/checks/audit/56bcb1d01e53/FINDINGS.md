# Findings-only audit — 56bcb1d01e53

Assigned and observed generator SHA-256: `7c7978cf0cd1f1f3842837e34539120bfb5c65a880b21053c1da05485437612d`.
Selected Racket rule: `a66a93e7a5d4`. Audit target source was not changed. These are three unresolved P2 findings. They do not identify a wrong label in the generator's current nonzero-background emitted inputs; they limit its teaching coverage and validator guarantees.

## A1 — No generated input teaches the canonical diagonal-center branch (P2)

The five templates in `generator.py` at `_TEMPLATES` (line 104) generate logical boxes of 4×5, 5×4, 5×5, or 6×6. Packing keeps them separate. The 7×7 diagonal-support center branch in `_apply_rule` (line 280) therefore has zero generated support. Matching the canonical 22×22 canvas and five-color profile does not recover this semantic coverage.

A concrete rival preserves bridge grouping, square rotation, rectangular reflection, and cardinal-supported center filling, but omits diagonal-supported center filling. It matches all 40 sampled production inputs (ten schedule positions in each of four difficulty bands) and every pair of the retained seed-11 four-pair lesson. All four held-out rotations pass the existing lesson hook while this rival survives.

This is a canonical failure, not only an extrapolation to a larger invented shape. Canonical test pair index 1 contains four 7×7 icons. Actual selected-rule Racket execution paints color 6 at zero-based row 5, column 14; the rival leaves background 8. All five stored canonical labels were independently confirmed against Racket in this audit.

Evidence: `audit_probe.py`, `audit-evidence.json` (`canonical`, `production_census`, `rotations`), and `audit-probe.command.json`.

Recommended repair: introduce a diagonal-supported 7×7 center witness and an explicit `cardinal_center_only` rival. Preserve the existing query-rotation guarantee against the expanded rival set. Extend the canonical-support observable to distinguish this branch from dimension/palette similarity.

## A2 — Full reflection symmetry remains indistinguishable from square rotation (P2)

The natural `square_dihedral_closure` rival adds horizontal, vertical, and diagonal reflections to each square's quarter-turn rotation partners. It keeps the bridge, rectangle, and center branches intact. It fits all five canonical labels and all 160 template/orientation/origin-parity cases (five templates × eight dihedral orientations × four origin parities).

This agreement covers the emitted square templates by construction: their completed shapes are already reflection-symmetric. The rectangular branch is unchanged, and packing separation plus unique icon colors prevents cross-icon interactions. Thus further seeds from this source do not distinguish the two rules.

A 7×7 input with a chiral 5×5 icon at origin (1,1) is accepted by `self_check`. The canonical Racket program adds only cell (2,5), changing background 1 to color 2. The executed D4 rival also adds (1,4), (2,1), (4,5), and (5,2). The Python rival and executed Racket rival agree exactly on this witness. Both complete programs and all inputs/outputs are retained.

Evidence: `child_d4_probe.py`, `child-d4-evidence.json` (160 checks and all five canonical fits), `minimal_witness_probe.py`, `minimal-witness-evidence.json` (`d4_witness`), `canonical-rule.rkt`, `rival-d4-rule.rkt`, and `minimal-witness-probe.command.json`. The child performed only Python checks; the separate minimal-witness receipt records the subsequent real Racket execution explicitly.

Recommended repair: include a chiral square witness in the normal teaching schedule and declare the D4 rival. Retain the witness even though both rules fit the original demonstrations: its purpose is precisely to distinguish their lawful extensions.

## A3 — Validator admits a background it explicitly excludes from generation (P2)

`generate` rejects `background=0`, but `_grid_facts` / `self_check` (line 475 onward) accepts a zero strict-majority background. `observe_overrides` returns `{"background": 0}` for such an accepted grid, and `rule_mirror` silently returns an answer that disagrees with the selected Racket rule.

The minimal 7×7 witness is the A2 input with background changed from 1 to 0. `self_check` returns `[]`. The selected Racket output and Python mirror differ at five cells: (1,2), (2,5), (3,3), (4,1), and (5,4). A second current-production mutation, seed 17 / index 1 / background 4 with colors 0 and 4 swapped, is also accepted and differs at 38 cells on its 18×22 canvas.

The existing generator comments and notes attribute the restriction to the object-extraction sentinel. The first semantic divergence is actually earlier: the runtime prelude's `mode(g)` excludes literal color 0 by default (definition at line 107). The Python `_background` includes it. The Racket rule's object extractor receives an explicit binary foreground mask, so the supplied sentinel explanation does not describe this cause accurately.

Evidence: `minimal-witness-evidence.json` (`zero_witness`), `audit-evidence.json` (`zero_background_witness`), the selected canonical rule, and `shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt`.

Recommended repair: make the validator enforce the declared nonzero-background domain, and have the public mirror reject inputs outside that domain or implement the actual Racket background semantics. Correct the explanatory comments. This finding does not imply current default generation emits zero-background inputs.

## Execution and limits

This audit executed 12 applications of the selected Racket rule: five canonical pairs, four production pairs, the larger zero-background mutation, and two minimal witnesses. One additional Racket application executed the explicitly separate D4 rival. Forty generated inputs were checked in Python; the template rival probe checked 160 cases. No full audit battery or runtime sweep was run. The retained public production challenge contains only training input/output pairs and an unlabeled test input.

Run from `WORK`, using its independent environment:

```sh
.venv/bin/python run_with_racket.py /absolute/path/to/WORK/.venv/bin/python ../checks/audit/56bcb1d01e53/audit_probe.py
.venv/bin/python run_with_racket.py /absolute/path/to/WORK/.venv/bin/python ../checks/audit/56bcb1d01e53/minimal_witness_probe.py
```

The exact executed interpreter, arguments, working directory, exit code, and log hash are in the two command receipts. Both commands exited zero; their assertions confirm the reported findings and source identity. `verification.json` binds the final evidence files and checks the public projection.
