# Native three-panel rotation family

`right_policy=fixed_half_turn` is the exact selected canonical program: preserve
the source panel, put its clockwise quarter-turn in the middle, and its half-turn
on the right. `right_policy=marker_row_control` adds a real sequential dependency:

1. construct the clockwise middle panel;
2. locate its unique color-8 marker and retain that marker row;
3. use the row to choose the right transform: upper half keeps the half-turn,
   lower half uses the counter-clockwise quarter-turn.

The first two demonstrations deliberately cover both branches. Every source has
eight distinct D4 transforms, inputs are setting-neutral and count-prefix stable,
and the four-query bank reaches the maximum lawful 9×29 strip (a 30-wide strip
would violate the canonical `3*n+2` shape). Native authoring preflight executes
all labels under protected Racket; owner review and acceptance remain separate.
