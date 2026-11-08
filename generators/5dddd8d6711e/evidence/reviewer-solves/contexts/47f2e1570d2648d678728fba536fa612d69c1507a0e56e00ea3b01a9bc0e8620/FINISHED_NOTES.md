# Solve work log

I had not opened this task's generator, Racket rule, canonical answer, prior solve notes, or any assigned repair material before this attempt. I used only the visible examples printed by `review.py blind prepare` and `challenge.json`.

## Initial observations and hypothesis

The border and interior separator lines use one wall color (1 in the training examples; 9 in test query 0). Color 7 appears only where a separator has a doorway. Colors 2 and 3 occur once each inside rooms; colors 4 or 6 are distractor tokens. The output removes all non-structural tokens and fills with 8 exactly the room sequence connecting the room containing 2 to the room containing 3.

Train example 0 supports a three-room route: the 2-room connects through a vertical doorway to the next room, then through a horizontal doorway to the 3-room. Other doors form branches and are not filled. Train example 1 is another three-room route. In train example 2, the 2-room and 3-room lie in disconnected parts of the room graph, so no room is filled and all tokens are erased.

## Program design

1. Use the top-left border value as the wall color and color 7 as the door color.
2. Find room interiors as four-connected components after excluding wall and door cells.
3. For every 7 cell, connect the two adjacent room components when exactly two exist.
4. Breadth-first search from the component containing color 2 to the component containing color 3.
5. Clear every non-background, non-wall, non-door token to 0. If a route exists, fill every interior cell of each room on that route with 8; preserve walls and 7 doorway cells.

The main uncertainty is tie-breaking if a future puzzle contains two equal-length routes. The visible examples have a unique relevant route, so the implementation uses deterministic component ordering for a shortest route.
