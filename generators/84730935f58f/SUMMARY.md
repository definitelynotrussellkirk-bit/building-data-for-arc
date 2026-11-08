# 84730935f58f

A zero-background grid contains a stencil selector at `(0, 0)` and two or more coloured seeds elsewhere. Selector `1` chooses a five-cell cardinal plus; selectors `2..7` choose a five-cell diagonal X. For the canonical rule, every non-selector nonzero cell is a seed and the output is a **fresh** zero grid containing the in-bounds union of the selected stencils in cyan (`8`). The selector is not copied to the output.

The ordinary generator alternates selector mode by sample index so a four-example lesson cannot omit a branch. It supports strict 5–14 dimensions, 2–8 seeds, 1–6 distinct seed colours (bounded by seed count), and real default/many/spread/tight placement profiles.

The task-local native family preserves that canonical rule as `render_mode=union` and adds `render_mode=overlap_highlight`, which computes selector-dependent coverage multiplicity and paints multiply covered cells red (`2`). It supports 2–6 demonstrations and exactly four distinct queries up to a substantive 30×30 case.

Kind: `per_puzzle`. Generator version: `2.1.0`. Reviewer authoring evidence is source-bound; owner acceptance and training admission remain separate.
