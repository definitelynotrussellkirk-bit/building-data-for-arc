# 2fd7d58a066c — Vertical Gap Fill

For every input column containing at least one nonzero cell, the authoritative rule paints the inclusive span from that column's topmost marker through its bottommost marker in cyan (`8`) on a fresh background-`0` grid. Marker colors are discarded. Empty columns remain empty, adjacent columns are independent, and a singleton marker is a one-cell span.

Version `3.0.0` uses one honest exact axis, `scene_profile`, and a five-example schedule:

1. `canonical_pairs` — canonical dimensions, color-2 endpoint pairs. This occurs twice per cycle to retain canonical-scale support.
2. `adjacent_shared` — adjacent occupied columns and repeated non-2 marker colors.
3. `mixed_extremes` — at least one column whose top and bottom markers have different colors.
4. `singleton_and_extra` — one singleton column plus a different column with an extra interior marker.

Any five consecutive default samples contain every profile. The counterexample profiles falsify rules that use only color 2, require same-colored extremes, require exactly two markers, ignore singletons, forbid adjacent columns, or process only one column per marker color.

Kind: `per_puzzle`. Imported version was `2.1.1`; selected version is `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
