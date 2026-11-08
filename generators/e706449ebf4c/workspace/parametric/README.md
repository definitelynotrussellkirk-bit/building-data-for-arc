# Aura radius-delta prototype

Status: **proposed prototype**, separate from canonical repair and not approved for production.

The fixed-per-episode parameter is `radius_delta`, measured in doubled Manhattan-distance units:

- `0` — canonical/default. The complete Racket source is byte-for-byte the pinned canonical rule.
- `2` — proposed variant. Expand each aura by one grid cell while keeping red-bar extraction, inclusive bar length, doubled half-cell centers, clipping, overlap, and red preservation unchanged.

The setting is selected once from the episode seed (`0` for even seeds, `2` for odd seeds) and held across three demonstrations and one query. The demonstrations are chosen so the other declared setting is refuted before the query. Public episode files contain labeled demonstrations and an unlabeled query only; they omit the hidden parameter, seed, Racket source, and query answer.

From the outer extraction directory, execute both exact Racket rules and create retained evidence:

```bash
python3 review.py run python3 \
  generators/e706449ebf4c/workspace/parametric/prototype.py \
  --seeds 0 1 \
  --out ../checks/parametric/radius-delta-v1
```

Run the portable focused tests through the task-test stage:

```bash
python3 review.py run python3 -m arcpuzzles check e706449ebf4c \
  --stage task_tests --timeout 600 --phase after \
  --out ../checks/task-tests
```

Evidence is finite: two settings, two seeds, four scheduled inputs, all labeled canonical pairs for the default, and the single declared parameter rival. It does not approve the variant or prove identifiability against every conceivable rule.
