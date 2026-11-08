# e8fb1b5bedfe

Generate 2–4 separated hollow color-4 rectangular frames on canonical 12×12, 13×13, or 14×14 canvases.  Interior areas are distinct.  The selected rule ranks frames by **interior area**, fills only the smallest interior with color 2, fills only the largest interior with color 8, and leaves any middle frames hollow.

Version `3.0.0` replaces lossy random placement and misleading texture/grid controls with exact `scene_profile` and `n_frames` controls.  A deterministic three-profile schedule supplies counterexamples to two shortcuts that fit all three canonical pairs: “the smallest is always 3×3” and “the largest is the widest.”  Every three consecutive demonstrations also include a 3- or 4-frame case, refuting “fill all non-small frames.”

The canonical Racket program is unchanged semantically.  Its selected base `raw_code` and `target_code` are now exact copies of the canonical source and are pinned by `RULE_HASH = "583ccfcccab0"`.
