# Solve work log

I had not opened the blind task's generator, rule, notes, solutions, audit records,
or the assigned repair generator before this solve. I used only `challenge.json`
and local Python/visual inspection of those visible grids.

## Revision 1 — connected green-majority regions

The blue lines partition each input into rectangular rooms. Orange `7` cells on
walls connect the rooms on their two sides. A maroon `9` can occur at a wall
intersection; I treat it as connecting every incident room, which is consistent
with the third training example.

I reduced each room to counts of red `2` and green `3` cells and computed connected
components through `7`/`9` wall marks. The visible examples then have component
(red, green) totals:

- example 1: `(4,5)` and `(14,12)`, giving 4;
- example 2: green-majority components include `(2,3)`, `(1,2)`, `(1,4)`, and
  `(3,5)`, whose largest red count is 3;
- example 3: the `9` joins two orange components into `(4,11)`, while the other
  is `(2,4)`, giving 4.

Hypothesis: choose the largest red count among connected regions with strictly
more green than red, then encode that positive count as a single `8` in a row of
length one less than the number of rooms. Remaining uncertainty is whether `9`
at an intersection should connect all incident rooms or only a conventionally
selected pair; the training example favors all incident rooms because it gives
the shown count cleanly.
