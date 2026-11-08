# b4ecb537757c

**Rotate inserts into matching-color frames.** A complete monochrome hollow
frame receives the external insert of its color. An isolated interior key
selects identity (1), clockwise quarter turn (2), half turn (3), or
counterclockwise quarter turn (4). The unchanged Racket rule clears the input,
retains complete frames, and pastes each transformed insert bbox at its frame's
interior top-left. Generated inserts fit completely after the selected turn.

The version-3 sampler constructs one to four distinct-color frames using colors
1–9 on a black canvas. Each frame has height/width 4 or 5, one separate key, and
one pure same-color external insert. Seven small connected motifs, their initial
orientations, randomized roles, cross-pocket insert assignment, jitter, and
reflections vary the scenes. Disjoint pockets avoid retries and fixed fallbacks.

Exact axes are `grid_h` 7–22, `grid_w` 12–24, and `n_frames` 1–4, subject to
declared pocket capacity. Invalid values, unknown axes, and infeasible exact
combinations fail visibly. Default eight-draw periods mix four one-frame
7×12 three-color scenes with four varied scenes. Seven demonstrations and one
query retain key coverage under every single holdout; two anchors expose
uniform and spatially inferred keys. Seventeen finite rivals check specified
alternatives. These are bounded teaching checks, not universal uniqueness.

The operational validator also accepts the canonical examples' unrelated
overwritten-frame fragments, while the sampler emits intact scenes. Fixed
pockets, seven motifs, and bounded frame sizes remain distribution limits.
See [current notes](notes.md) for compatibility changes and evidence.

Kind: `per_puzzle`. Version: `3.0.0`. Reference-rule hash: `1232696ab606`.
Approval is derived separately from current code and retained review evidence.
