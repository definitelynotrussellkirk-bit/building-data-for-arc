# 22304ccc509c native parametric prototype

The default `gravity_policy=down` returns the exact canonical Racket program.
The alternative `edge_directed` policy first locates the unique color-1 marker
on one non-corner border cell, converts that edge to the intermediate direction
`up`, `down`, `left`, or `right`, and then stable-packs every corresponding
column or row in that direction.

Input sampling is independent of the selected setting. Two demonstrations are
enough to separate the policies and the declared rivals; requests may use 2–6
demonstrations and always contain four distinct queries, one for each direction.
The final query is a substantive 30×30 case with at least 80 foreground cells
and contact on all four boundaries.
