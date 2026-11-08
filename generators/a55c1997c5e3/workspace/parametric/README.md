# Parametric tie-order family for `a55c1997c5e3`

This proposed family leaves the approved canonical generator unchanged. Every
input still requires finding all maximal simple paths from the red block,
retaining the maximum-node candidates, and painting one candidate. The private,
episode-fixed `tie_order` parameter controls the final lexicographic choice:

- `right_down_left_up` — the exact canonical Racket program and default.
- `up_left_down_right` — the reverse total direction order, with no other Racket
  source change.

Inputs are sampled independently of the private setting. Requests support 2–6
demonstrations and exactly four distinct queries. The final query is a substantive
30×30 graph whose objects touch every canvas boundary. The first two
Demonstrations identify either setting against all 24 constant direction orders;
this is a finite audit, not a proof against arbitrary programs.

The causal chain is not cosmetic: **A** enumerates the input-dependent set of
maximum-node paths, producing their coordinate paths/direction sequences;
**B** consumes that set and the episode tie order to choose which path to paint.
B cannot select a path before A has found the tied candidates.

From the outer review packet, the native four-query qualification command is:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify a55c1997c5e3 \
  --demos 3 --queries 4 --out ../checks/a55c1997c5e3/qualification --summary
```

Qualification executes every saved label with protected Racket. The prototype's
Python mirror is only a construction/audit aid. Hidden settings, exact programs,
and query answers belong only in private evidence; public challenges contain
visible demonstration pairs and masked query inputs.
