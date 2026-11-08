# Solve notes

## Visible-rule hypothesis

The grids are mazes: 8 is a wall, 2 is the start, 5 is a mandatory checkpoint,
3 is the final goal, and route cells are painted 4 while all markers remain
unchanged.  The path appears to be the shortest route in a state space that
tracks whether 5 has been visited.

Colors 6 and 7 occur in pairs.  The second training example rules out a symmetric
portal: its top corridor would trap a path that teleported in both directions.
Instead, entering the first occurrence in row-major order jumps to the second;
the second endpoint can be entered normally.  This also explains the long jump
in training examples 1 and 3.

I use BFS over `(row, column, checkpoint_seen)`, cardinal moves in the apparent
up/down/left/right tie order, and the directed portal transition.  Reconstruction
paints only zero-valued landing cells; portal endpoints and 2/3/5 remain intact.

## Revision 2

The first program matched examples 1 and 3 exactly but missed only the zero cell
between the two 6 endpoints in example 2.  A merely optional portal would choose
the shorter non-portal continuation, so the visible output shows that each
present directed portal must be used, not merely available.  I therefore add a
portal-use bitmask to the BFS goal condition while retaining the same visible
movement and painting rules.
