# Visible-only solve notes

Task: `538503abef57`; assignment: `review-39704160ebbd4e4c`.

## Exposure and scope

I am a fresh isolated solver agent with no earlier exposure to the rule or generator. I consulted only the prepared `solve/README.md`, `solve/challenge.json`, `solve/summary.json`, and my own solve files. I did not consult a reference, generator source, canonical data, private labels, audits, other agents' work, or prior solution notes during this solve. The overall review will conservatively record earlier exposure as **yes**, because the coordinator authored the generator; this is distinct from my own lack of earlier exposure.

## Revision 1: observable hypothesis and probe

The visible grids preserve dimensions, colors, object bounding boxes, and foreground counts. Each separate monochromatic object is reflected across the diagonal joining the top-right and bottom-left corners of its tight bounding box. All visible objects have square bounding boxes. Separate objects of the same color are handled independently.

Revision 1 implements four-connected monochromatic components and this reflection. No other solver revision has been made. An attempted auxiliary probe-file write was blocked; the probe was then run inline without creating that file. This was an environment issue, not a failed transformation hypothesis.

An inline `python3 -B -` probe compared all eight square symmetries with the visible outputs. Anti-diagonal reflection matched all 8 components. The half-turn matched 2, the counterclockwise quarter-turn matched 1, and each of the other 5 alternatives matched 0. The complete solver outputs matched all 3 visible training grids. Both unlabeled query inputs executed and produced 9 by 11 grids; their correctness is unknown.

The official checker will be used only for visible-pair and execution feedback. There are no private query labels available to this solver. Generalization outside the visible component layouts remains unverified.
