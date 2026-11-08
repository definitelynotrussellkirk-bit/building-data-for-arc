# Post-repair visible solve work log

Earlier exposure: **yes**. I reviewed and repaired this generator before this
solve episode. During the solve itself I used only the visible challenge and did
not reopen the generator, Racket rule, private labels, or reference solution.

Visible hypothesis:

1. Read every 2/3/4/5 in row 0 from left to right as commands.
2. Ignore row 0 while finding nonzero 4-connected body objects. Select the object
   with largest area; the left/top object wins the visible equal-area ties.
3. Crop the original body to that object's bounding box. This preserves the
   disconnected contrasting cell inside the box, which is visible in every output.
4. Command 2 is identity, 3 clockwise quarter-turn, 4 half-turn, and 5
   counter-clockwise quarter-turn.
5. Place the transformed crops left-to-right in command order with one blank
   column between copies, top aligned.

All four examples provide all four command codes in differing orders, and the
internal contrasting pixel makes rotation direction and crop semantics directly
observable. I stopped after one implementation because it matched all visible
examples exactly.
