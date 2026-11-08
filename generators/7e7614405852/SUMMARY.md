# 7e7614405852

Scan each row for maximal nonzero monochromatic runs. Recolor only the center
cell of a run whose length is exactly three; preserve every other cell.

Kind: `per_puzzle`. Reviewed version: `2.0.0`. Canonical rule hash:
`5eb06a6d574a`.

The constructive sampler exposes seven exact, observable axes: grid height and
width; counts of horizontal runs of lengths 2, 3, 4, and 5; and the count of
vertical length-3 distractors. Ordinary draws always include a horizontal
length-5 run and a vertical triple so lessons refute odd-length, at-least-three,
and orientation-insensitive shortcuts. See `workspace/reference_probe.py` and
`checks/reference-probe.json` in the review return for a rerunnable independent-oracle probe.
