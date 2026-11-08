# Component histograms with an inferred size threshold

This native adapter extends `dc91f4798e24` without changing its canonical
generator or reference. `promotion.json` declares the two episode-fixed modes:

| Mode | Rule |
| --- | --- |
| `all` (canonical default) | Count four-connected monochromatic components of colors 1, 2 and 3. |
| `blue_count_threshold` | First count blue components to obtain k. Count each target-color component only if its actual cell area is at least k. |

Both rules draw the original three left-aligned histogram rows. Colors 4–9 are
ignored. The alternate's threshold depends on the input, rather than on a hidden
constant or a directly visible pixel count. Its two minimum teaching examples
use k=2 and k=4; diagonal contacts, a foreign-color bridge, and an L triomino
distinguish connectivity and cell-area reasoning. Blue sizes differ from their
count in the first example, excluding a largest-blue-size threshold shortcut.

## API and input grammar

`adapter.program(settings)` returns exact Racket source;
`adapter.generate(seed, settings, demos=3, queries=4)` returns labeled `train`
and `test` pairs plus `program_solution`. Python outputs are claims until the
native worker has replayed them through protected Racket.

- Settings are exactly `{"mode": "all"}` or `{"mode": "blue_count_threshold"}`.
- Seeds are exact integers in 0..2**63-1; booleans are rejected.
- Demonstrations: 2–6, default 3. Queries: 1–4, default 4.
- Counts are independent, all episode inputs are distinct, and each split's
  prefix is unchanged when its requested count changes.
- The same seed and counts produce identical inputs for both settings.
- Query dimensions are 7×8, 12×16, 24×24 and 30×30. The last query has 45 target
  bodies, target content in all four quadrants, target contact with all four
  borders, and 50 distractor cells. It is not a padded small scene.
- Shapes grow through the unchanged canonical placement helper, with independent
  component areas and deterministic random streams. A placement has at most 256
  attempts and raises on exhaustion; requested areas are never silently reduced.

## Reproduce focused checks

From the outer packet folder, after `python3 review.py setup` and Python dependency
installation, use the packet-local interpreter:

```bash
WORK/.venv/bin/python review.py run python -m pytest \
  generators/dc91f4798e24/tests -q

WORK/.venv/bin/python review.py run python \
  generators/dc91f4798e24/workspace/parametric/verify_evidence.py audit \
  --out ../checks/dc91f4798e24/recheck
```

The evidence command uses the existing native worker and live protected Racket.
It checks two settings, seeds 0 and 17, and the 2/6 demonstration boundaries with
four queries. It checks the 3/4/5 counts as Python requests, matched inputs,
single-query first-turn equivalence, and finite Racket rivals. A surviving rival
is acceptable only when it agrees on every query. Fixed cutoff 1 is equivalent
to the canonical rule on this grammar. Wrong rules that already disagree on a
demonstration need no private query answer to eliminate them.

The output's `public/` directory contains only demonstration pairs and query
inputs. File names hash the shared serializer's exact visible bytes. Keep the
other evidence files controller-side: they contain settings, programs and query
labels. `visible_bytes(episode, query_index=0)` produces the first-turn view
with one query and no future-query or total-count information. The existing
consumer owns turn sequencing; this prototype does not create another controller.

## Qualification and owner handoff

Use the existing `arcpuzzles parametric manifest` command to update the task-local
inventory after source/evidence changes. Then, from the outer packet folder:

```bash
WORK/.venv/bin/python review.py run python -m arcpuzzles parametric qualify \
  dc91f4798e24 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/dc91f4798e24/qualification

WORK/.venv/bin/python review.py run python \
  generators/dc91f4798e24/workspace/parametric/verify_evidence.py witness \
  --qualification ../checks/dc91f4798e24/qualification/qualification.json \
  --evidence ../checks/dc91f4798e24/audit-v1/report.json \
  --out ../checks/dc91f4798e24/sequential-witness.json
```

Choose new output paths on reruns. The witness command checks the qualification's
task, status, current native source binding, contract and setting/program hash,
then freshly executes both the true and wrong-threshold programs through protected
Racket. A stale report cannot be promoted by changing its status field.

The return is reviewer-ready after passing native qualification. The owner must
integrate, freshly qualify and accept the exact live source before using native
`parametric generate` or `parametric export`. Nothing here changes acceptance,
training admission, dataset weights or model deployment. The finite teaching
checks do not establish universal rule uniqueness or all-seed sampler totality.
