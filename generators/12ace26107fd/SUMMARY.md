# 12ace26107fd

Zero-background grid with one cardinal-connected, hole-free shape in a single
foreground color from 1 through 8. The canonical rule repeatedly removes cells
that lack a north, south, east, or west neighbor. The one-row output records the
number removed on each pass, outside to inside; these are exact shell counts.
For example, the thirteen-cell diamond yields [[8, 4, 1]].

The repaired generator samples areas 3–14 and supports exact height, width,
shape-size, and color controls. Its default period-three schedule supplies two
different nine-cell shapes whose outputs are [[8, 1]] and [[9]], plus a broader
shape family. Five demonstrations from a six-pair bundle retain both outputs
after any one holdout, refuting an area-only rule. Finite production and rotation
censuses cover four declared rivals; they do not prove universal identifiability.

Kind: `per_puzzle`. Imported version: `3.0.2`. Reviewed generator version: `4.0.3`.
Approval is derived by the catalog from current code and retained evidence.
The final stock battery still reports output-diversity and minimal-shape lint
warnings. See notes.md and the retained review for the acceptance decision.
