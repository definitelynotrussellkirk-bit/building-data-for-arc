# Working notes: 3fb5ef8ad60e

## Delivered family

The unchanged canonical rule is the default `divider_reference=block_midrange`
setting: detect three distinct colored 2×2 blocks inside the cyan frame and divide
rows/columns at the midrange of the extreme block centers. The native alternative
`frame_midpoint` detects the same blocks but derives the divider from the cyan
frame bounding box. Both settings then map block centers through that input-derived
divider into a 2×2 color summary.

Inputs are setting-independent. The constructive sampler supports 2–6
demonstrations and 1–4 queries, guarantees three noncolliding summary cells under
both dividers, makes the settings disagree, rejects fixed-canvas and numeric-color
layout rivals, varies frame offsets/geometries/colors/missing cells, and includes
a substantive 30×30 case. Its four queries are privately shuffled.

The bounded audit covered four seeds, all supported demo/query counts and both
settings: 160 episodes, 1,040 labeled pairs, 24 protected-Racket evaluations, no
teaching holes, no duplicate inputs and no public projection leaks. The native
authoring preflight ran four jobs (two settings × seeds 0 and 17), with 32
protected-Racket label evaluations and a unique surviving setting in every job.

## Sequential dependency

A detects the frame and blocks and derives the selected integer divider. B must
consume that divider to classify every block center and place its color. The
protected `wrong_intermediate` witness changes the divider from `[10,11]` to
`[10,8]` on the same qualified input, changing the final summary.

## Status and limits

Reviewer-ready authoring evidence is retained under `checks/3fb5ef8ad60e/` and
task-local `workspace/parametric/evidence/`. This is finite evidence over the
listed seeds/rivals, not universal identifiability, owner acceptance or training
admission. The base generator and canonical authority bytes were not changed.

## Complementary source retained

The current owner-accepted `divider_reference` family remains selected. Return
`review-abc25c186f3648f3` independently adds `indexed_color_rotate`: derive the
2×2 summary, select an intermediate summary color from a cyan-border hole code,
then rotate by that color modulo four. Its exact source, inventory, protected
qualification and causal witness are retained under
`workspace/proposals/review-abc25c186f3648f3/`. These are reviewer-reported proposal
assets pending grouped reconciliation; no replacement or additional acceptance
is claimed.

Current duplicate decision: retain the incumbent accepted family. The incoming indexed-rotation proposal requires 1–4 frame holes and four blocks; incumbent zero-hole/three-block scenes are outside that rule grammar. `evidence/owner-merge-current/grammar-conflict.json` retains the exact input, source hashes and rejection. This is an unmerged proposal-domain conflict, not a newly demonstrated failure of the selected family.
