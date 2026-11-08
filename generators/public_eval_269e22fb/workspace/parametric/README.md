# 269e22fb parametric family

The default `pocket_policy=preserve` is byte-identical to `reference.rkt` and
completes the unique dihedral pose of the 20×20 emblem containing the input crop.
`mark_enclosed` first performs that same input-dependent completion, then marks
all background regions not four-neighbor reachable from the completed canvas
boundary with red (2). Generated episodes exclude red from the two crop colors.

The sampler holds inputs fixed across settings, supports 2–6 demonstrations and
1–4 prefix-stable private queries, and uses ten distinct crop profiles. Output
size is intrinsically 20×20, so 30×30 stress is not lawful for this parent.
