# Proposed parametric family: `860cbb625ca0`

This task-local prototype exposes the orientation policy already implemented by
the selected canonical Racket program:

- `exact` — the original byte-for-byte canonical rule (`mode 0`)
- `rotations` — exact plus 90/180/270-degree rotations (`mode 1`)
- `dihedral` — rotations plus reflected orientations, de-duplicated (`mode 2`)

`match_mode` is selected once per episode.  Every episode contains 2–6 visible
demonstrations and exactly four distinct queries.  The final query is a
substantive 30×30 case with stamps spanning every board boundary.  Inputs are
shared across settings; each demonstration distinguishes every rival setting.

Racket generates and verifies private labels.  `prototype.py` also contains an
independent Python mirror for diagnostics, public/private projection helpers,
first-turn projection, and an atomic evidence writer.  `adapter.py` deliberately
emits Python claims without starting Racket so a promotion worker can replay
those claims in its own protected runtime.  This remains proposed and
unapproved; `promotion.json` is a bounded opt-in contract, not catalog approval.
