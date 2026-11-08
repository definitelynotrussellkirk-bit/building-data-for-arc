# Solve work log

## Prior exposure

Before this solve I had read only the packet-level start/duties instructions. I had
not opened this task's generator, canonical rule, notes, reference solutions,
private labels, or audit evidence.

## Revision 1 — centered count-preserving bar

Visible examples show one black separator crossing two parallel black separators.
Gray cells overwrite parts of those lines in the input. The two parallel lines
bound a central band, and their midpoint coincides with the single perpendicular
line. In the output:

- the number of gray cells is preserved;
- gray cells become a one-cell-thick bar centered on the crossing;
- the bar is parallel to the pair of separators (horizontal for two separator
  rows, vertical for two separator columns);
- the paired separators move to the cells immediately on either side of the bar;
- the single perpendicular separator remains in place, with the gray bar
  overwriting its crossing cell(s).

Checks made by hand against the visible examples:

- example 0: 11 gray cells -> an 11-cell horizontal bar at row 5; separator rows
  move from 3/7 to 4/6;
- example 1: 7 gray cells -> a 7-cell horizontal bar at row 4; separator rows
  move from 2/6 to 3/5;
- example 2: 9 gray cells -> a 9-cell vertical bar at column 6; separator columns
  move from 3/9 to 5/7.

The implementation detects separator rows/columns as lines containing only black
or gray and at least one black cell, because the gray object can interrupt a
separator. It then constructs the transformed grid from the inferred orientation.
The visible data use orange=7, black=0, gray=5. Remaining uncertainty: no visible
example has an even gray count or an off-center separator midpoint; the code keeps
exact count and uses integer-centered placement but those cases are not evidenced.
