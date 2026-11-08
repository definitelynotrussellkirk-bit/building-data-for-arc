# 54b040e4bd08

Generator version `3.0.0` teaches global two-dimensional periodic repair.
It creates a 6–10 by 9–12 grid from a distinct-color `2x2`, `2x3`, or
`3x2` tile, erases one strictly interior solid zero rectangle, and leaves the
selected canonical rule to infer the smallest complete period and restore only
the zero cells.

The default four-slot curriculum is adversarial rather than merely random:
`row_gap_*` profiles refute row-by-row filling, `column_gap_*` profiles refute
column-by-column filling, and every profile makes the hole overlap the top-left
period block so a top-left-only tile reader fails. Each lesson uses three
ordered demonstrations plus one query; the declared lesson hook also supports
every query rotation.

Five public axes are exact and observable: grid height, grid width, tile shape,
top margin, and left margin. Unknown, mistyped, and out-of-range overrides are
rejected. `self_check` enforces dimensions, ARC colors, one solid interior zero
rectangle, a complete allowed smallest period, and distinct nonzero tile
residues. The canonical rule is unchanged and pinned by `RULE_HASH =
"55b239af8777"`.

Known scope limit: default production deliberately concentrates on thin
adversarial row/column bands and uses `2x3`/`3x2` profiles; `2x2` is covered by
the exact axis contract and canonical support rather than the default schedule.
The finite three-rival contract does not prove uniqueness against every possible
induction rule.

Owner acceptance: current repaired source is retained with reviewer-reported checks; audit-only findings remain source-bound with their target generators. No model trajectory is training-admitted.
