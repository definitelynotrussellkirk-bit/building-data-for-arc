# Blind solve notes — 778a00c38b8d

## Attempt 1

Hypothesis: treat red cells (2) as 4-connected components. Recolor an entire
component green (3) iff it touches at least two distinct grid borders; preserve
all other cells, including gray 5.

Evidence from the four demonstrations:
- Corner-attached components touching top+left, top+right, bottom+left, or
  bottom+right all turn green.
- Components touching only one border remain red, even when they are near a
  corner or share a row/column with the gray marker.
- Interior components remain red.
- The rule explains the lower-left vertical component in example 3 because it
  reaches both the left and bottom borders, despite not containing a literal
  corner cell.

Rejected rivals:
- "Recolor components containing a corner cell" fails on example 3's lower-left
  vertical component, which touches left and bottom through different cells.
- "Recolor all boundary objects" fails on several one-border objects.
- Distance/direction relative to gray 5 does not consistently separate changed
  from unchanged objects.

Implementation: flood-fill each red 4-connected component, collect the set of
borders it touches, and recolor it when that set has size at least two.
