# 5e0575c16ab4

Fill the inclusive horizontal span for a color only when that color appears exactly twice in the whole grid, both occurrences share a row, and every cell strictly between them is zero.

Kind: `per_puzzle`. Version: `2.0.0`. Selected rule hash: `8cad321146ee`.

The four-example curriculum cycles through:

- `canonical`: ordinary globally unique blank bridges;
- `global_repeat`: two tempting row-local pairs of one globally repeated color;
- `blocked_bridge`: an exactly-twice pair with a nonzero blocker;
- `count_alignment`: a vertical pair and a three-occurrence row.

Exact observable axes are `grid_h`, `grid_w`, `positive_pairs`, and `profile`. Unknown overrides are rejected. The generator declares executable semantic rivals/witnesses and checks lesson identifiability.

Review `review-01c692811d9c592c`: final source-bound battery 12/12 green; 600/600 semantic draws lawful; 12/12 sampled lessons identifiable; 26,190/26,190 override draws accepted with no findings. The Racket authority was not changed.
