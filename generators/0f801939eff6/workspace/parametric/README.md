# Merge before area ranking

This task-local family has two episode-fixed settings:

| Setting | Executed rule |
| --- | --- |
| `{"merge":"none"}` | Exact canonical Racket program: extract same-color four-connected components, rank by descending area and ascending color, and emit area-length color runs. |
| `{"merge":"2_into_1"}` | Recolor every 2 to 1, recompute the component partition and areas, then apply the same ranking and encoding. |

The original `generator.py`, canonical rule and approval are unchanged. The
default program is byte-identical to the selected canonical authority. This is
a native-qualified proposal; owner acceptance after integration remains required.
No training admission or activation is claimed.

## Run in the review packet

Use the Python interpreter that passes `review.py python-check`. From the outer
directory containing `review.py`, create a new output directory:

```bash
python3 review.py run python3 generators/0f801939eff6/workspace/parametric/prototype.py \
  --seed 17 --demos 3 --queries 4 --merge both --out ../checks/new-component-episodes
```

This writes two episodes, one per setting, with matched input draws. The writer
uses Python label claims. Verify labels through native qualification and the
protected-Racket audit before using a newly generated batch as evidence:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 0f801939eff6 \
  --out ../checks/new-component-qualification --summary
python3 review.py run python3 generators/0f801939eff6/workspace/parametric/audit.py \
  --qualification ../checks/new-component-qualification/qualification.json \
  --out ../checks/new-component-audit --export ../checks/new-component-verified
```

The audit exports the native qualification's four verified episodes, checks count
boundaries, executes the finite rivals, and saves a protected-Racket causal
witness. It can be reused after changes; regenerate the native manifest first
when any bound source or declared evidence changes. Existing output directories
are refused deliberately. See `docs/parametric-promotion.md` for owner acceptance.

## Teaching and supported requests

`generate(seed, settings, demos=3, queries=4)` accepts exact integer seeds
`0..2**63-1`, 2–6 demonstrations and 1–4 queries. Four queries are the training
request. Counts and random streams are independent, inputs are matched across
settings, and queries are distinct from all demonstrations and one another.

The first two demonstrations deliberately show a merge that changes ranking,
a merge that does not create the largest component, disconnected occurrences
of the same color, a diagonal contact, conflicting position/color tie-breaks,
and an isolated color-2 component. The isolated component repairs a concrete
teaching hole: locally recoloring only the foreground cluster containing color 1
otherwise fitted both demonstrations and failed a separated query.

`teaching_check` fits named rivals using demonstration inputs and labels only:
other setting, color aggregation, position tie-break, eight-connectivity,
bounding-box ranking, color ranking, scan order, target-color-first, and, for
the merge setting, rank-then-recolor and local-cluster-only recoloring. Passing
means only these finite rivals are excluded, not universal rule uniqueness.

Each four-query request includes an 8×11 lower-bound case, a 21–29-side case,
a separated source/target case and a 30×30 case. The latter places 30 occupied
cells across all four corners, with actual merges, repeated colors and ties.
The task's single-row output is capped at 30 cells, so this is spatial-extent
stress, not dense-grid stress. These are prototype sampling guarantees, not new
production `grid_h`/`grid_w` overrides. The canonical controls remain unchanged.

## Visibility and reuse

`public/<sha256>.json` contains the demonstration pairs and the first query input
only. IDs hash the exact visible bytes. Settings, seeds, programs, all query
answers and future query inputs remain in `private/<same-id>.json`. The private
record is the controller's complete query bank. `public_challenge(episode, i)`
projects exactly one selected query; it includes no query count or final-turn
hint. Asking for one query or four produces identical first-turn content.

The writer validates and serializes all public and private bytes before creating
the destination, rejects duplicate visible first turns, and refuses overwrite.
It does not implement the consumer's conversation controller.

Current qualification is `checks/0f801939eff6/qualification-v3/qualification.json`
in the returned packet, with its sibling `execution.json`. The source-bound
90-evaluation audit and causal witness are in `checks/0f801939eff6/audit-v3/`;
the retained before/after teaching repair was separately replayed in 10 Racket
evaluations. Focused tests cover 80 cases. The 72/72 sampling result is Python
evidence over seeds 0–11 and demo counts 2/3/6, not an additional Racket census.
