# Working notes: 616a5c01a7ea

## Delivered family

The exact canonical default remains `right_policy=fixed_half_turn`: retain the left source panel, place its clockwise quarter-turn in the middle, place its half-turn on the right, and preserve the two color-5 separators.

The nearby setting `right_policy=marker_row_control` creates an input-dependent sequence. Step A constructs the clockwise middle panel. The intermediate is the row of the unique color-8 marker in that constructed panel, classified against the upper/lower half boundary. Step B uses a half-turn on the right for an upper-half marker and a counterclockwise quarter-turn for a lower-half marker. The first demonstration takes the distinguishing lower branch; the second takes the agreeing upper branch, so the lesson cannot be reduced to an unconditional counterclockwise right panel.

Every generated source panel has eight distinct dihedral signatures and exactly one marker. Inputs are identical across settings, deterministic, count-prefix stable, and support 2–6 demonstrations plus 1–4 queries. Because the canonical strip has width `3n+2`, the largest lawful grid under the 30-cell dimension cap is 9×29; that query contains substantial source content rather than padding.

## Base-test repair

The inherited tests assumed a staged `puzzle_generators.per_puzzle` import and a canonical-data path relative to the task directory. They now use `reviewer_support` for portable generator loading, root discovery, canonical pairs, and canonical-data lookup. The base solution's selected target is compared by normalized rule hash rather than byte formatting: its compact `target_code` and the pretty-formatted canonical authority normalize to the same `79b7067ac64d` rule, while the archival raw code remains intentionally distinct.

## Adversarial review and retained evidence

- Direct tests: 21 passed plus 5 unittest subtests; copied-runtime gate reports 26/26 passed.
- Visible demonstrations reject copy-all, counterclockwise middle, swapped panels, mirrored middle, unconditional counterclockwise right, and inverted marker-branch shortcuts.
- Structural self-audit: both settings × seeds 0 and 17; both marker branches; all source panels had eight D4 signatures; sizes through 9×29.
- Authoring preflight: four jobs (two settings × two seeds), 2 demonstrations + 4 queries each, 32 protected-Racket label evaluations, all passed.
- Causal witness: protected Racket replayed the qualified setting and a wrong lower-half classification; the final right panel changed.
- Public projection: 16 one-query views; source-bound projection verification passed. The combined first-turn check covered this task's four episodes with 24 private-field invariance mutations and four positive controls.

This is reviewer-ready source, not owner acceptance. The finite checks do not prove universal identifiability, and no training admission is claimed.
