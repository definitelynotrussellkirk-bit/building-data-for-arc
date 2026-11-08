# Native symmetry-axis family

This task-local family extends the retained prototype and preserves the exact
canonical `left_right` Racket program. The canonical `generator.py` is unchanged.

| Private episode setting | Executed rule |
| --- | --- |
| `left_right` (default) | Return `[[1]]` for whole-grid left-right reflection symmetry, else `[[7]]`. |
| `top_bottom` | Classify whole-grid top-bottom reflection symmetry. |
| `rotation_180` | Classify whole-grid half-turn symmetry. |
| `bbox_major_axis` | Measure the occupied bounding box; choose left-right when taller than wide, otherwise top-bottom (including square ties); classify that reflection of the whole original grid. |

The fourth setting adds input-dependent contextual gating: the measured box
determines which reflection is tested. It is not iterative state simulation.
A wide LR-only grid can return 7 under the derived TB choice but 1 under an
incorrect LR intermediate. The return's protected-Racket witness binds this
comparison to the qualified source.

## Native interface and teaching

`adapter.program(settings)` materializes the exact rule.
`adapter.generate(seed, settings, demos=3, queries=4)` returns labeled train/test
pairs and `program_solution` for the native worker to execute independently.
Settings, seeds and counts are strictly validated; booleans and coerced strings
are rejected. Counts are independent: **3–6 demonstrations and 1–4 queries**.
Three is the supported minimum, including the owner's native qualification
default. Two demonstrations are rejected rather than silently enlarged.

The foreground uses one nonzero color on a zero background, with dimensions
3–30; ordinary demonstrations use 9, 11 or 13 square canvases. Input geometry
is built from randomized reflection orbits, varied occupied extents and
placements. A positive/negative demonstration pair has the same foreground
count, color and canvas size. Four queries have mixed labels, distinct inputs,
and sizes 7×9, 13×17, 23×27 and 30×30 in seed-shuffled order. Large cases have
substantial occupied extent and density; they do not pad a small witness.

Demonstrations alone identify the selected setting among all four declared
programs. A finite extra-rival set tests constant/count/color/corner shortcuts,
wrong axis/tie choices, crop-first classification, bounding-box alignment, and
complements/unions of symmetries. Some extra rivals can remain consistent with
three demonstrations. The sampler screens queries against **all** such survivors
and records them, rather than claiming they were eliminated. Four/five/six-demo
requests add asymmetric/all-symmetric geometry and can eliminate more rivals.
This is conditional, finite teaching evidence; it is not global uniqueness.
The profile RNG is setting-independent, but curriculum choice and query screening
are setting-dependent; matched inputs across all settings are not claimed.

The old canonical sampler exposes a top-right-corner shortcut. This native
sampler does not reuse its schedule: executable corner rivals must be refuted
or agree on every retained query. Existing historical prototype evidence is
not fresh qualification evidence for these source bytes.

## Reproduce the focused authoring evidence

From the outer packet folder, with its passing Python environment:

```bash
python3 review.py run python3 -m pytest \
  generators/4b787be81422/tests/test_parametric_symmetry_axis.py \
  generators/4b787be81422/tests/test_native_symmetry_axis.py -q
python3 review.py run python3 \
  generators/4b787be81422/workspace/parametric/prototype.py \
  --out ../checks/4b787be81422/authoring --seeds 0 17 --demos 3 --queries 4
```

The writer executes selected labels and every declared/extra rival in protected
Racket, checks its independent Python computations, and retains complete private
program/output matrices. It also checks all eight official canonical pairs.
The output directory must be new. `checks.json` binds the compact results,
source hash, runtime identity and exact public/private evidence files.

Public filenames are SHA-256 hashes of the exact canonical visible bytes.
Public JSON contains demonstration pairs and query inputs only; seed, settings,
reference programs and query answers remain private. The full query list belongs
to the controller. Its consumer reveals one query per turn with no total-count
metadata. Restricting a lesson to its first query gives the same visible first
turn as requesting one query with the same seed, setting and demo count. No
training loop or interactive controller is introduced here.

After finalizing source and focused evidence, inventory it with
`arcpuzzles parametric manifest`, then qualify at the owner's defaults:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 4b787be81422 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/4b787be81422/qualification --summary
```

Return the sibling `qualification.json` and `execution.json`, the native
source inventory, and the causal witness/replay. Reviewer-ready is separate from
the owner's fresh exact-source acceptance and from training admission.
