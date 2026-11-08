# Bounding-box selection and frame completion

Reviewer proposal for `47993d3762b9`; native owner acceptance remains pending.

## Design and contract

One episode-fixed `mode` selects `all_corners`, `largest_bbox_frame`, or
`smallest_bbox_frame`. The first mode returns the exact canonical Racket text.
The other modes group all cells by color, derive every color's bounding box and
area, choose the unique extreme-area color, and draw that box's perimeter on a
fresh zero canvas. This preserves color grouping and distributed extrema while
making the final action depend on an input-derived object selection.

The input grammar uses 2–4 nonzero colors, nondegenerate boxes, no overlapping
boxes, and unique box areas. Foreground counts deliberately need not rank with
box areas. Labels and private settings are separate from visible challenges.
The sampler uses the same input stream across settings, independently samples
demo/query streams, and supports 2–6 demos and 1–4 queries. The normal lesson is
three demos and four queries. Two constructive initial demos distinguish the
declared settings and targeted shortcuts; subsequent examples vary texture,
density, location and dimensions. Four-query profiles include substantive
30×30 content, including boundary contacts and distributed extrema. Profile
order is shuffled per seed independently of settings and requested counts, so
a particular size does not mark the final query.

Approaches considered: vary output decoration alone (too little sequential
reasoning); merge overlapping color boxes before recomputing corners (adds an
arbitrary color merge convention); select a box by its computed area and then
complete its frame (chosen, with the smallest change to the original reasoning).
This is contextual selection followed by geometry, not iterative state simulation.

## Verified scope and limits

- The final task test run passes all 14 tests: seven unchanged canonical tests
  and seven parametric tests. Counts, strict types, matched inputs, independent
  query prefixes, public privacy and shuffled size order are exercised.
- The retained audit passes 27/27 episodes at seeds 0, 17 and 43, with 2, 3 and
  6 demonstrations, all three modes and four queries. It uses 642 distinct
  protected Racket program/input evaluations. Every finite rival executes on
  every demonstration; no surviving rival disagrees on a sampled query.
- All 27 public files hash to their exact filenames using the shared serializer.
  The 30×30 cases have 330–384 foreground cells, four colors and contact with all
  four canvas boundaries. The audit records minimum profiles and distractors too.
- Native qualification passes three settings on seeds 0 and 17: six jobs,
  42 labeled pairs and 78 Racket evaluations. Its source inventory has 37 files.
- The native witness helper constructs and replays two counterfactual cases.
  In both frame modes, ranking by pixel count selects a different color and
  rectangle than ranking by box area, changing the protected Racket output.

Exact evidence is in the workspace's `evidence/final-audit/`, this workspace's
`evidence/manifest.json`, and returned `checks/47993d3762b9/qualification/` and
`checks/47993d3762b9/causal/`. The canonical mode also admits an equivalent
corner-drawing template in the finite audit; that is not a query disagreement.
Overlapping boxes, tied areas, arbitrary untested rivals and measured learning
benefit remain outside these claims. Owner native acceptance and training
admission have not been performed.

## Reproduce and qualify

From the packet's outer folder, use the Python interpreter that passed
`review.py python-check` (in this review, `WORK/.venv/bin/python`). Outputs must
be fresh paths. The native qualification and witness commands do not accept or
activate the prototype.

```sh
python3 review.py run python3 -m pytest \
  generators/47993d3762b9/tests/test_parametric_47993d3762b9.py -q
python3 review.py run python3 \
  generators/47993d3762b9/workspace/parametric/audit.py \
  --out generators/47993d3762b9/workspace/parametric/evidence/final-audit
python3 review.py run python3 -m arcpuzzles parametric manifest 47993d3762b9 \
  --evidence generators/47993d3762b9/workspace/parametric/evidence/final-audit \
  --include generators/47993d3762b9/tests/test_parametric_47993d3762b9.py \
  --reported-checks 'Use the actual audit and test results; finite scope only'
python3 review.py run python3 -m arcpuzzles parametric qualify 47993d3762b9 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/47993d3762b9/qualification --summary
```

`adapter.generate(seed, settings, demos, queries)` returns private episode data.
For example, `generate(17, {"mode": "largest_bbox_frame"}, 3, 4)` fixes the rule
across three demonstrations and four queries. `public_challenge(episode, 0)`
projects only the first query; subsequent indices are controller-side selections,
not public future-query files. A one-query request has the exact same first
projection as a four-query request. Python outputs are claims until Racket replay.

The audit produces compact Racket-backed examples, public first-turn files and
private proof records. To rerun it, select another evidence output directory; to
replace a manifest, first compare it and use the native exact-hash replacement
guard. Changing source after qualification requires fresh qualification.
