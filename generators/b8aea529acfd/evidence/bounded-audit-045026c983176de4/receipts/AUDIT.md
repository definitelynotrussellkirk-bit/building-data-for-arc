## b8aea529acfd

**No issue found within the tested scope.** Findings-only audit 1 for immutable assignment `review-045026c983176de4`; no selected generator, rule, notes, catalog, or shared source was edited.

### Source binding and inspection

- Generator version `2.1.0`, SHA-256 `5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999`.
- Selected executable rule hash `8e26e8f07755`; full selected-rule SHA-256 `8e26e8f07755275993a3cc2f3a1e95d3c3ff2dc44c4bd7d008bc376c9fe73c33`. The public apply receipt separately records rule-text SHA-256 `b599713c7e7b3883413720d1d05ef4f24675cbd9c397fc46272a9285b7f41049`.
- Read the selected generator, current notes, canonical ledger row, solution record, current `evidence/review_index.json`, and relevant associated notes. The current index has no explicit audit entries. Retained reports were treated as provenance, not as rerun results.

### Tested scope and observations

The adversarial target was the earlier duplicate-skipping failure: easy seed 370 previously lost its second witness and became ambiguous under query rotation. The public Racket-backed `lesson-census` now materialized all eight declared starts at seed **370** in each of easy, medium and hard: **24 lessons, 96 labeled pairs, 96 query rotations, 33 distinct inputs**. Production and rotation status are both `no_ambiguity_found`; materialization/scoring errors and hook warnings are zero. This is complete fixed-seed start coverage, not all-seed coverage.

An independent retained Python probe exercised seed 370, indices **0–31** per band (**96 draws**), determinism, both validators, all **15** exact profile controls, and four-pair windows at starts 0–7. All checks passed. These generated observations use the Python mirror; they are not represented as 96 independent Racket calls. All **48** dense draws separated both canonical-fitting shortcuts; all four canonical labels fit both shortcuts. The four simpler transform rivals are already refuted by canonical labels and are not relabeled as canonical-fitting shortcuts.

Public `apply` executed the actual selected Racket rule on all **four canonical pairs** and **six generated dense witnesses** (indices 1 and 3 in each band). All ten outputs exactly matched the retained expectations, and the generator-domain checks accepted them. Every one of the six exact generated witnesses disagrees with all six declared semantic rivals. Inputs, authoritative outputs and exact rival outputs are retained in `input.json`, `racket.json`, and `witness-rivals.json`.

Source inspection supports the specific repaired schedule claim: four consecutive ordinary positions contain two witnesses; their forced opposite full accent edges prevent duplicate inputs, anchor signatures differ, and dense canvas sizes differ from anchors. Removing any one of those four pairs leaves a witness against both crop shortcuts.

### Limits and evidence

No additional source-bound defect was reproduced. Explicit profile overrides bypass the ordinary curriculum by declared design; validator-only acceptance and arbitrary off-distribution grids were not counted as generated support. Dense-edge/palette correlations remain disclosed distribution limits. This audit does not certify resistance to undeclared hypotheses, every seed, arbitrary lesson sizes, or training admission. No full battery or task-local test suite was rerun.

Reproduction commands and exit codes: `checks/audit/b8aea529acfd/commands.json`. Main receipts: `probe.json`, `census.json`, `census.summary.json`, `racket.json`, and `verification.json`; runnable probes: `probe.py`, `verify.py`. All paths in this paragraph are beneath `WORK/`, with receipt basenames relative to this audit directory.
