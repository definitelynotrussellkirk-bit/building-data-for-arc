# Solve work log

## Prior exposure

Before this blind episode I had not opened task `9de4ae27d0d0`'s generator,
canonical rule, notes, solutions, audit records, or private labels. I also had
not opened the assigned repair generator. I had only read packet-level
instructions and the generated duties.

## Revision 1 — border-contact filter

**Visible pattern.** Each training input contains several separate, uniformly
colored 4-connected objects. The output preserves an object exactly when at
least one of its cells lies on the outermost row or column, and replaces every
interior object cell with background 0.

Evidence across the three examples:

- Example 1 keeps the color-8 object touching the left edge and color-6 object
  touching the bottom edge; the color-4 and color-1 objects are one cell away
  from every edge and disappear.
- Example 2 keeps only the color-8 object touching the right edge.
- Example 3 keeps the color-2 singleton touching the top edge and color-1
  object touching the bottom edge.

**Implementation.** Flood-fill each same-color 4-connected component. Copy it
to a zero grid only when any component cell touches a border. Same-color
connectivity is used so merely adjacent objects of different colors remain
independent.

**Predicted tests.** Test 1 should keep the right-edge color-4 domino and the
left-edge color-9 bar, deleting color 6. Test 2 should keep the left-edge
color-7 domino and bottom-edge color-9 object, deleting colors 6 and 2.

**Remaining uncertainty.** The visible examples do not distinguish 4- from
8-connectivity for diagonally touching same-color cells. ARC object conventions
and every displayed object favor 4-connectivity, so I use that minimal rule.
