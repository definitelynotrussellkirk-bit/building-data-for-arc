# Visible-example solve work log

This is an agent-authored work log, not a captured token trace.

## Access and exposure

A new solving worker performed this solve. The supervising review session had earlier source exposure, so this run must be recorded with `--earlier-exposure yes`. The worker read only the public `WORK/solve/README.md` and `WORK/solve/challenge.json` as puzzle evidence. It did not consult generator source, a reference rule or solution, private query labels, prior solve explanations, or canonical-data helpers. Reference consultation for this solve is `no`.

The challenge contains five labeled training examples and two input-only queries. An inline Python analysis using only `challenge.json` summarized panel bounding boxes and local marker coordinates. That analysis did not execute a candidate solution or compare predicted grids against training labels.

## Revision 1: proposed transformation

Use the uniform outer background to find separate rectangular panels. The sole panel without markers supplies output dimensions and its fill color. Select the widest marked panel as the donor. Transfer each marker while preserving its distance to the nearest edge on each axis. A marker exactly centered on an axis is anchored to both edges, potentially creating two copies on that axis. Ignore coordinates falling outside the destination.

The visible examples support this rule: the 7 by 11 donor in training examples 0, 2, and 4 yields four copies of its central marker; the 11 by 9 donor in example 1 yields two copies of its middle-row marker in the 20 by 7 destination; and the 9 by 15 donor in example 3 yields the four displayed corner markers in the 9 by 9 destination. Different colors and positions in narrower panels do not change the shared outputs of examples 0 and 4.

Implementation uses only the input grid and Python standard library. It detects filled nonbackground components, identifies each component's dominant fill color, and transfers donor marker colors. It does not read challenge data or any external files at runtime. All observed inputs have a uniform background border, separated full rectangular panels, exactly one blank panel, and a unique widest marked panel. A width tie is resolved by greater height; that tie behavior is not established by these examples.

## Planned official check

Run exactly:

```sh
WORK/.venv/bin/python3 review.py solve check --intent solve --note 'Revision 1: the widest marked rectangle supplies markers to the sole blank rectangle, preserving nearest-edge distances and duplicating axis-center markers; this accounts for the visible center duplications and differing output sizes.'
```

This is the first genuine program revision. No failed candidate or negative check has been fabricated. Feedback from the official check will establish visible-example agreement and execution only; it cannot establish correctness of the two hidden query outputs.
