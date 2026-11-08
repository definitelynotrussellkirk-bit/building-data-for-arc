# Visible-only solve notes

I had already studied this task's rule while repairing its generator, so this is
an exposed post-repair solve, not a blind solve. During this solve episode I read
only `solve/challenge.json` and did not consult the Racket rule, generator source,
reference outputs, private labels, or previous solve explanation.

## Hypothesis 1

The examples partition nonzero cells into same-color 4-connected components.
A component survives exactly when it reaches both kinds of outer boundary: at
least one top/bottom-row cell and at least one left/right-column cell. Components
that reach only one border axis or remain interior are replaced by zero.

Evidence from the visible examples:

- Train 1 keeps the two bottom-corner components and removes a top-only component
  plus an interior component.
- Train 2 keeps the long left/top component, the upper-right corner component,
  the lower-left corner component, and the right/bottom component; it removes a
  left-only component and interior pieces.
- Train 3 keeps two corner components and removes top-only/interior components.

Implementation plan: flood-fill each nonzero monochrome 4-connected component,
compute whether it touches a horizontal and a vertical border, and copy only
components satisfying both predicates.
