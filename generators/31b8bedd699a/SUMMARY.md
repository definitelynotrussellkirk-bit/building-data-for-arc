# 31b8bedd699a — separated frames, fixed output tokens

Kind: `per_puzzle`. Proposed generator version: `3.0.0`.
Canonical rule hash: `ca3b9033626d`; the selected Racket program is unchanged.

On background 0, retain monochrome hollow rectangular frames and discard solid
rectangles. Compare the ranges of the retained frames' top-left row and column
coordinates. Use a vertical output exactly when the row range is greater; ties
are horizontal. Stably sort by the selected top-left coordinate, then redraw
each frame as a **fixed 4×4 hollow token** of its color and concatenate the tokens.
Repeated frame colors retain their multiplicity. Input sizes do not set output
panel sizes.

Generated inputs have 2–5 complete frames, 0–3 solid distractors, object dimensions
3–8, and at least one background cell between every pair of object boxes.
The four exact controls are `grid_h` and `grid_w` in 15–30, `n_frames` in 2–5,
and `n_solids` in 0–3. Every joint tuple is constructively supported; unknown or
retired controls raise an error instead of being ignored.

Default lessons use a six-phase schedule and five demonstrations. Canonical-size
profiles alternate with larger/smaller-frame, repeated-color, tie, and distractor
counterexamples. Fourteen declared rivals are checked against complete lessons.
This is a deliberately restricted teaching distribution: canonical acceptance
and profile similarity do not establish full generative coverage or transfer to
all legal overrides. See `notes.md` for the measured scope and two open support
limitations. Approval and training admission remain maintainer decisions.
