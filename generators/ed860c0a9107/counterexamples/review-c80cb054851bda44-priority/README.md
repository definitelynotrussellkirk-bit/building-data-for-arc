# Exact old-source teaching counterexample

Source v4.0.0 SHA-256:
`e1094f19d9fdddc9c645c810cba5949a937c35f47c05df395b479b3a13dde462`.
Seed 20000, difficulty easy, sample indices 0,1,2 for demonstrations and 3 for
query. `priority-witness-inputs.json` preserves the four exact grids in that order.
The independent predictions and public Racket receipt are adjacent JSON files.
All four intended Python labels equal the actual Racket labels; the receipt
binds the canonical normalized rule hash `8e6a03efc456`.

The column-major, highest-color and first-palette-appearance alternatives fit
all three demos but give 9 instead of 1 at zero-based query output (1,2):

Intended: `[[9,9,0,1,9],[1,1,1,0,1]]`.
Rival: `[[9,9,0,1,9],[1,1,9,0,1]]`.

This is a minimal four-pair lesson witness; labels were not inferred solely
from the generator's own mirror. Re-run the public `arcpuzzles apply` command
recorded inside the receipt to verify the unchanged canonical rule. Regenerating
the original inputs requires the pinned v4.0.0 source, not v4.1.0.

The repair covers the underlying failure with independently reconstructed
geometry and rival predictions in `tests/test_teaching_contract.py`, plus the
source-bound final production and cyclic-start censuses retained in the review
return. Those checks establish a finite seven-rival result, not universal
identifiability. The baseline exploratory search remains in
`workspace/review_source.py` with its explicit expected-source guard.
