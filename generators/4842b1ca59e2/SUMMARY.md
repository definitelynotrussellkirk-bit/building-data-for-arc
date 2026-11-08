# 4842b1ca59e2 — first seed paints its whole column

Version **3.0.0** is a constructive input sampler for the unchanged canonical
rule. Scan each column from top to bottom: an empty column remains zero; otherwise
the first nonzero seed's color fills the entire column. Lower seeds are overwritten.

Default inputs are 4–5 by 5–6 canonical-profile grids with 2–3 active columns.
Every ordinary draw contains one or two multi-seed columns whose top and bottom
colors disagree, so the lesson refutes both canonical-fitting shortcuts: “only
single-seed columns paint” and “the bottommost seed wins.” Exact controls are
`grid_h`, `grid_w`, `active_columns`, `stacked_columns`, and `stack_depth`.

The validator also accepts all four canonical single-seed inputs. The generator
and its tests do not alter the Racket authority. Current known limits are a narrow
reviewed extension: default multi-seed stacks are contiguous, lower colors reuse
another active top color, and active top colors are distinct.
