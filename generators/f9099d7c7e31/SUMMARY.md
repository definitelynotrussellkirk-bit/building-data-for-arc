# f9099d7c7e31 — Extract the widest object

A zero-background 9–11 by 9–11 grid contains 3–4 distinct-colored, four-connected objects. Select by bounding-box width, breaking width ties by occupied cell count, then crop the original input to the selected object's tight box. Preserve background holes and any foreign-colored cells inside that box.

Kind: `per_puzzle`. Revised version: `4.0.0` (packet baseline: `3.0.0`).

The four-example schedule retains canonical morphology anchors and now teaches against largest bounding-box area, both height-based width-tie rules, and border-only selection, in addition to the previous four rivals. The default tie example contains a 10-cell 3×5 winner, an 8-cell 4×5 loser, a 5-cell 1×5 loser, and a narrower 12-cell 4×3 distractor. The cropped output still preserves foreign colors and zeros.

The eight public override axes, canonical Racket rule, canonical labels, declared strict-profile floor, and approval mechanism are unchanged. Approval is derived by the catalog from current code and retained evidence; this review does not grant approval or claim a training-score improvement.

Run the independent probe and all task tests with the commands in `workspace/README.md`.
