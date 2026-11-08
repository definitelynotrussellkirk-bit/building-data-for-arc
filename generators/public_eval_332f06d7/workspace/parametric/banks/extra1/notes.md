# Public parent 332f06d7

## Canonical rule

The solid color-0 rectangle is a boat and the equal-size color-2 rectangle is a
destination. Enumerate every top-left placement where the boat's full footprint
avoids the wall color. Retain the placement-graph component containing the
initial boat. Among its dead ends, choose the one nearest the destination
(top-left Manhattan distance, then reading order), restore the old boat cells to
corridor color 1, and paint the selected footprint color 0.

This explains reachable and unreachable destinations uniformly. The root
`reference.rkt` matches all four public demonstrations and the supplied test
gold under protected Racket.

## Episode-fixed extension

`finish=trace_route` additionally recolors to 9 the corridor cells swept by the
selected start-to-dead-end route, excluding the final boat. Generated placement
graphs are branched trees with a destination reachable to a point agent but not
to the full boat. The retained counterfactual marks every reachable placement,
including unused branches.

The family is reviewer-ready only. Owner registration, unchanged native
qualification, exact-source acceptance, and any training admission remain
separate gates.
