# Solve work log

## Prior exposure

I did not open the generator, canonical rule, private labels, prior solution notes, or audit evidence before this solve. I used only the visible examples in `challenge.json`/`README.md` and local tests built from the four visible training pairs.

## Hypothesis

Each input contains one isolated marker cell whose color is 1, 2, 3, or 4, plus a larger connected multicolor object. The output removes the marker and surrounding background, crops the larger object to its bounding box, and rotates that crop clockwise by `marker_color - 1` quarter-turns:

- marker 1: no rotation;
- marker 2: 90 degrees clockwise;
- marker 3: 180 degrees;
- marker 4: 90 degrees counterclockwise (three clockwise turns).

The four training examples exercise all four marker values. The marker positions vary, so I treated color—not marker position—as the instruction.

## Tests and alternatives

I first added `test_visible_examples.py`, which imports `solution.py` and checks all four public training pairs directly from `challenge.json`. It failed on the untouched `NotImplementedError`, establishing the test before implementation. I then implemented crop-plus-rotation and reran the same test.

A rejected alternative was to orient the object from the marker's relative spatial position. That matches the training placements superficially, but query 1 places marker color 2 upper-left rather than upper-right, while the color sequence 1–4 gives a complete and consistent rotation code across all demonstrations.

## Predicted query outputs

For query 0 (marker 1), the cropped object is returned unchanged:

```text
8 8 0 0
0 8 7 8
0 0 7 7
```

For query 1 (marker 2), the cropped object is rotated 90 degrees clockwise:

```text
8 5 5
8 5 0
8 0 0
```

Remaining uncertainty: the visible data assumes exactly one marker color in 1–4 occurring once and a nonempty payload. The implementation reports a clear error outside that observed contract rather than guessing.
