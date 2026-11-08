# Parametric family: 6ecd8be24495

`selection_metric=total_seeds` returns the exact selected canonical program.
`selection_metric=distinct_colors` first selects the chamber containing the
largest number of distinct nonzero seed colors, using total seeds, local-majority
count, and lower color as deterministic tie-breakers. Both settings then fill
only the selected chamber's blanks with its local majority color.

Matched inputs give the total-count winner three colors, the distinct-count
winner four colors, and a separate stronger monochromatic decoy. Thus the first
two demonstrations distinguish both declared settings and the retained
first-max-distinct / strongest-pile shortcuts.
