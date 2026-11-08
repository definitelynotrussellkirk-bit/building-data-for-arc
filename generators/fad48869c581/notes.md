# Working notes: fad48869c581

The base generator was repaired before parametric work: ordinary generation now
constructs isolated monochrome L triominoes whose intended missing corners match
the canonical snapshot rule exactly; exact size/count overrides, unknown-override
rejection, observer support, deterministic 30×30 stress, and a Python rule mirror
are covered by focused tests. The selected canonical Racket bytes remain exact.

The native family in `workspace/parametric/` adds `square_halo` beside the exact
`canonical` default. Stage A completes each L to a solid monochrome 2×2 square.
Stage B reads that completed snapshot and fills the one-cell clipped halo around
each derived square with its color while preserving existing nonzero distractors.
The original inputs contain no solid squares, so the protected skip-A program has
no Stage-B trigger and produces a different answer.

Final staged tests passed 34 cases. The bounded audit covered 32 seeds, all 2–6
demonstration and 1–4 query prefixes, 640 Python labels, 40 protected-Racket
labels, 20 protected-Racket skip-A evaluations, 32 Python causal separations,
and 128 named-rival rejections. Two substantive 30×30 scenes, boundary contact,
distractors, count limits, four-query projection, and first-turn privacy were
exercised. `preflight_compat.py` only wraps this legacy task's singleton canonical
`test` pair in memory for the shared authoring preflight; it preserves the raw
catalog hash and does not edit catalog data. Owner source review, native
qualification/acceptance, and training admission remain pending.
