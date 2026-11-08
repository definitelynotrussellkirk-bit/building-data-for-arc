# 27080597d778 — globally complementary panels

Two width-4 panels, separated by a gray column, form a height-3..10 by width-9
input. Each panel contains zeros and at most one nonzero, non-gray color. The
unchanged canonical Racket rule overlays the panels **only when every aligned
cell pair contains exactly one nonzero cell**. The overlay preserves the source
colors. If any overlap or double-zero gap exists anywhere, the entire output is
the original left panel, including its zeros. This is a global test, not a
per-cell or per-row combination.

Generator version `2.0.0` covers four profiles: complement, overlap-only,
gap-only, and equal-count overlap-plus-gap. A seed-permuted four-slot schedule
covers all four in every four consecutive draws. Keep at least four
demonstrations and validate each actual query after any filtering, deduplication,
or slicing. The task-local workspace tool generates Racket-labeled research
lessons, independently shuffles demonstrations, checks every final query, and
separates public challenges from private labels/programs.

See `notes.md`, `workspace/README.md`, and the source-local tests. Python mirrors
and named wrong solvers exist only for audits; Racket produces training labels.
The canonical/base authorities are unchanged (`RULE_HASH=7362bea2dda7`).
Approval remains derived from catalog evidence and was **not promoted** by this
review. Four examples falsify eight named rivals; this is not a proof of unique
induction among all possible programs or a measured model-training improvement.
