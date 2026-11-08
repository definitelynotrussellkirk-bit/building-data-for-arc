# Rectangle-to-cross cascade

Native parametric candidate for `13507b4f7614`. Reviewer qualification and owner
acceptance are separate: this workspace does not approve or activate the family.
Production generator version 2.0.0 and its canonical reference are unchanged.

## Two episode-fixed rules

| `selection_rule` | Transformation |
| --- | --- |
| `all_odd` (default) | Exact canonical program: turn every solid yellow rectangle with both dimensions odd into its middle row and middle column. Leave even-sided rectangles unchanged. |
| `cross_area_cascade` | A: find the unique largest odd-by-odd yellow rectangle and reduce it to a cross. Count that cross's occupied cells in the updated grid. B: find the unique remaining solid rectangle whose area equals that count and reduce it to a cross. Preserve other rectangles. |

The default source is read from this checkout's canonical ledger and checked
against SHA256 `812105731900a688cc0c44d666e50dd11f6cabdb8858f3d633e471c1dacf4936`.
It is returned byte-for-byte. The new rule remains recognizable as the original
rectangle reduction, adding selection based on the result of a prior reduction.

The sequential dependency is substantive: B cannot identify its target until
the input-selected anchor's transformed occupancy is known. The Racket program
actually paints A, then counts cells in `after-a`; it does not count the original
solid area. The private counterfactual retains A but substitutes the original
area for this intermediate. That changes B's target and the final grid.
This is a bounded object-transform/count/selection composition, not a claim of
arbitrary iterative simulation or universal algorithmic depth.

## Admitted input grammar and teaching

Inputs contain four or five separated solid color-4 rectangles on background 0.
There is one unique largest odd rectangle and exactly one other odd rectangle
whose area equals the cross occupancy `height + width - 1`. Odd decoys and
even-sided distractors make both selection and the canonical parity guard
visible. Rectangles may touch the canvas boundary. This separate prototype
extends the production sampler's narrower margins, object counts and sizes;
it does not change the production validator or its approval.

The first two demonstrations use different anchor/target areas and ranks.
Layout, reflection, transposition and placement offsets vary deterministically
with the seed. A bounded, demonstration-only selector chooses two layouts that
refute the declared finite wrong rules under both settings. It tests at most
64 candidates per recipe (128 candidates total), then raises explicitly if no
teaching pair exists. It never inspects query inputs or answers when selecting
demonstrations, and never changes the requested demonstration count.

`rivals.py` contains independent Python diagnostics for 35 plausible rules:
parity omissions, fixed target counts, wrong count calculations, skipped or
wrong anchors, position, distance, aspect and size shortcuts. Python diagnostic
outputs select inputs only. Every delivered answer comes from protected Racket.
`self_audit.py` compares the intended diagnostic transformations to actual
Racket labels, checks every 2..6-demo prefix, tests all declared rivals, and
retains wrong-intermediate Racket witnesses. A new rival can be added to the
registry; if the two recipes cannot teach it within the budget, generation fails
visibly and the curriculum must be strengthened. The finite registry is not a
proof of unique induction against every possible program.

The 30x30 query uses five substantial rectangles across all four quadrants.
Other queries include canonical-scale 9x12 (or 12x9 after transpose), 21x29 and
25x30 canvases, so stress is not just empty padding. Every scene has a valid B
match. The finite recipe grammar varies placement and orientation, not arbitrary
rectangle dimensions, counts, colors or arbitrary spatial topologies.

## APIs and public/private contract

`adapter.py` loads the exact adjacent `native.py`, avoiding ambient modules
called `native` or `prototype`. The `promotion.json` contract exposes:

```python
program({"selection_rule": "all_odd"}) -> str
generate(seed, settings, demos=3, queries=4) -> {
    "train": [{"input": grid, "output": grid}, ...],
    "test": [{"input": grid, "output": grid}, ...],
    "program_solution": exact_racket_source,
}
```

Seeds are exact integers 0..2**63-1, demonstrations 2..6 and queries 1..4;
booleans, floats and unknown settings are rejected. Three demonstrations are
the ordinary default. Input generation does not depend on the hidden setting.
The query stream is separate from demonstration selection. Changing requested
counts preserves existing prefixes; all inputs within an episode are distinct.

`sample_inputs(seed, demos, queries)` returns only input grids.
`teaching_metadata(seed)` exposes private construction-budget diagnostics.
`public_turn(episode, query_index=0)` projects only demonstration input/output
pairs and one query input, stripping extra private fields. It returns no query
index, total count, final-turn flag, future input, setting, seed, program or
query answer. Its first turn is identical for one-query and four-query requests.
The existing consumer controls when subsequent queries are revealed.

`write_examples(out, seed=17, demos=3)` refuses an existing destination, writes
two public first-turn files using the exact shared canonical public bytes, and
retains all four labeled queries and private metadata in `private/`.
`challenge-<sha256>.json` hashes the actual saved bytes, with no setting or seed
in public names. Keep `private/` and `report.json` out of model-visible input.

## Reproduce from the outer packet directory

Use Python 3.12+ with NumPy, Pillow and pytest. `review.py setup` selects the
bundled Racket executable; the wrapper also selects the same-checkout runtime.

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/13507b4f7614/tests/test_native_parametric.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/13507b4f7614/workspace/parametric/native.py \
  --seed 17 --demos 3 --out ../checks/13507b4f7614/examples

WORK/.venv/bin/python review.py run python3 \
  generators/13507b4f7614/workspace/parametric/self_audit.py \
  --seeds 0 2 3 17 --out ../checks/13507b4f7614/self-audit.json

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  13507b4f7614 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/13507b4f7614/qualification --summary
```

Use a fresh output directory when rerunning qualification or example generation.
The source/evidence inventory is `evidence/manifest.json`, produced by the native
manifest helper after focused verification. Exact commands and evidence are in
the return's `RESULTS.json` and `checks/13507b4f7614/`. Native qualification must
be repeated if bound source changes. The owner must integrate and accept exact
live bytes; reviewer readiness does not grant training admission.
