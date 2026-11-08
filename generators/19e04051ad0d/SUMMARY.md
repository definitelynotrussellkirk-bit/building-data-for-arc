# 19e04051ad0d

Infer the uniquely modal background and the three vertical regions separated by
exactly two full-background columns. Fill each region's background holes with
the NEXT region's foreground color, cyclically left to right. Preserve original
foreground cells and the separator columns.

Kind: `per_puzzle`. Version: `3.1.0`. Canonical `RULE_HASH`: `3448ae999e2e`.
Approval is derived by the catalog from current code and retained evidence;
this review does not grant training approval.

## Teaching support

Both numeric color-cycle orientations occur, alternating by sample index. The
three cyclic rotations are keyed random nuisance variation, so all six relative
foreground-color orders have support. With no sampler rejection, every three
consecutive inputs refute both numeric successor and numeric predecessor rules.
Production-sampler and cyclic-query evidence checks that premise on actual
materialized lessons; it is not a universal induction guarantee.

Existing shape, palette, mask and exact-axis controls are retained. Ordinary
layouts remain asymmetric; the canonical `222` layout remains legal through an
exact override. See `notes.md` and `workspace/README.md` for limitations, tests,
and source-bound replay commands.
