# Proposed parametric tie-break prototype

This directory is **not** part of the selected canonical execution path. The
catalog task remains pinned to rule hash `c701ff882260`, whose equal-height
objects use `color_asc`.

The prototype has one bounded hidden parameter:

| Parameter | Values | Original/default |
|---|---|---|
| `tie_break` | `color_asc`, `color_desc` | `color_asc` |

The setting is selected once per complete 3-demonstration/1-query episode and is
shared by every pair. Every materialized input contains an equal-height pair, so
both settings produce different outputs on every demonstration and query. The
rest of the transformation—height descending, crop preservation, left-aligned
vertical packing, and one-row gaps—does not vary.

Run from the outer packet directory:

```bash
python3 review.py run python3 \
  generators/87388eaff4ce/workspace/parametric/verify.py \
  --out ../checks/parametric/87388eaff4ce-tiebreak.json
```

The verifier writes exact Racket programs to `programs/`, complete retained
episodes and answer-masked public challenges to `episodes/`, executes every
stored output with the included Racket bridge, and checks the alternative
setting against all demonstrations and queries.

Evidence is intentionally bounded: two retained seeds cover both declared
settings. This demonstrates feasibility and teaching separation; it does not
approve a generic/parametric production API or establish all-seed behavior.
