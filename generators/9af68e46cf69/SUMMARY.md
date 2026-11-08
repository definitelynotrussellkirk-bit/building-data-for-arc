# 9af68e46cf69 — enclosed-background objects

The input is a 9–30 by 11–30 grid with color 9 as background and several
4-connected color-1 objects. Recolor an entire object from 1 to 8 exactly when
one complete color-9 connected component lies strictly inside that object's
bounding box. Objects without such an enclosed region remain color 1.

Public exact controls are `grid_h`, `grid_w`, `n_holey` (1–3), and `n_solid`
(1–4). Every generated input contains both an irregular hole-bearing object and
an open-bounding-box no-hole decoy, so the examples refute the shortcuts
“rectangular frames only” and “any background pixel inside the bbox.”

Selected generator version: `3.0.0`. Selected rule hash: `7fd2884c3200`.
Approval remains derived from current code and retained evidence.
