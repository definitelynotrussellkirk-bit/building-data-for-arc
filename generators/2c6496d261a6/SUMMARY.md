# 2c6496d261a6

Keep every occurrence of a nonzero color if all its occurrences occupy one row.
Erase every occurrence of a color that spans multiple rows. Background is zero;
the output keeps the input dimensions. Canonical Racket authority: `e0b73d0c2fd9`.

The sampler constructs mixed keep/erase scenes without overwriting colors.
Ordinary draws include a horizontal multi-cell keeper, a singleton keeper, and
a distractor spanning at least three rows with a repeated occurrence in one row.
These cases distinguish global row confinement from local repetition, fixed
occurrence counts, a two-row cutoff, and dropping singletons. Other colors vary
row spans, counts, spacing, and column alignment; colors and positions are random.

Exact independent controls are `grid_h` (3..12), `grid_w` (7..18), `kept_colors`
(1..5), and `palette_size` (2..9), with kept colors fewer than total colors.
`n_distinct_colors` is a compatibility alias of `palette_size`, not another
independent axis. Ordinary draws use 3..9 total colors and 2..5 keepers; explicit
controls also support two total colors or one keeper. Difficulty changes mixture
weights between canonical-size layouts and broader layouts, while keeping the
same exact-control domain. Unsupported or incompatible requests fail explicitly.

The task-local contract supplies five pixel-derived witnesses, seven executable
wrong rules, and a demonstration-only lesson-identifiability hook. The reusable
`workspace/lesson_probe.py` measures actual three-demo/two-query episodes against
the unchanged Racket authority and binds evidence to source hashes. Its result is
finite-rival evidence, not a guarantee about arbitrary learners or unseen rivals.

Kind: `per_puzzle`. Selected version: `3.0.0` (review of imported `2.0.1`).
Approval is derived by the catalog from current code and retained evidence.
