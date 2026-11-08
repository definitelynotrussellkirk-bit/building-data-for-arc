# Connected network / room-core scope

Native authoring adapter for `9c75b1456763`. The production generator and selected
canonical authority remain byte-for-byte unchanged. Owner acceptance of the
integrated source is a separate step; these examples admit no training data.

## Rule and input-dependent sequence

`fill_scope` is fixed across an episode:

| Setting | Behavior |
| --- | --- |
| `all_interiors` (default) | Execute the exact canonical program: propagate each marked network's color to its complete-eight-neighbor interior cells. |
| `unmarked_rooms` | Form four-connected components of those eligible interior cells, identify the component containing the marker, and color the other components. |

Here **room core means a connected erosion component**, not an authored
rectangle or a radius around a marker. A notch and a neighboring corridor can
split one drawn rectangle into separate cores; a separated core is eligible
even when it lies inside that same rectangle. Blue-only components are ignored.

A: normalize nonzero colors for four-connected network discovery, recover that
network's marker, compute complete-eight-neighbor erosion, and partition the
erosion into four-connected cores. The input-dependent intermediate is the
marker-containing core and the network-local marker color. B: under the remote
setting, recolor all other cores with that color. Moving a marker changes which
core must be excluded; a positional shortcut cannot determine the intermediate.

The protected causal witness replaces core membership with distance greater
than two, using a qualified first demonstration whose marked core is long
enough for those decisions to differ. The actual programs, input and labels
are kept privately in `WORK/checks/9c75b1456763/causal/`.

## Sampling and teaching

The first demonstration always contains a woven network: an outer bent network
passes around interior chains, making its far room closer to another network's
marker by row, column and Manhattan distance. Its 5×7 marked room also makes
connected-core exclusion differ from radius-two exclusion. Other inputs mix
woven and striped networks, 2–3 distinct marker colors, variable room widths,
corner notches, straight and bent corridors, unmarked distractors and eight
rotations/reflections. Queries cover 18×18, 20×20 and two substantive 30×30 scenes.

The prototype's grammar is deliberately broader than the production checker;
new inputs are not claimed to pass the unchanged `generator.self_check`.
All output rules retain the original blue/black body/background conventions.
Sizes are limited to the supported square profiles; arbitrary rectangles,
multiple markers per network and markers outside an interior core are not
supported. Canonical source is untouched, including its narrower stripe sampler.

Requests support 2–6 demonstrations and 1–4 queries independently. The intended
lesson is three demonstrations and four queries. Geometry RNG streams ignore
settings and requested counts; matched requests therefore share inputs across
settings. There are no geometry retries. An exact duplicate input can retry at
most 32 times, then raises; the consumed count stays private.

## Reproduce in the issued packet

Run from the outer folder containing `review.py`, using the prepared interpreter:

```sh
WORK/.venv/bin/python review.py run python3 -m pytest -q generators/9c75b1456763/tests/test_parametric.py
WORK/.venv/bin/python review.py run python3 generators/9c75b1456763/workspace/parametric/audit.py --out ../checks/9c75b1456763/fresh-self-review.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 9c75b1456763 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/9c75b1456763/fresh-qualification --summary
WORK/.venv/bin/python review.py run python3 generators/9c75b1456763/workspace/parametric/export_examples.py --qualification ../checks/9c75b1456763/fresh-qualification/qualification.json --out ../checks/9c75b1456763/fresh-examples
```

`audit.py` is reusable and bounded: two scopes, one seed, two demonstrations,
four queries and nine named rival families. It fits candidates to demonstrations
only, checks surviving predictions, and checks the Racket rivals against Python
mirrors. Equivalent aliases are reported as equivalent, never hidden. Passing
only covers these declared alternatives and samples.

After source changes, rerun the affected checks and regenerate the task-local
native inventory with `arcpuzzles parametric manifest` before qualification.
Existing evidence/output destinations are refused. Source and rule resources
must travel with the adapter; no predecessor checkout is imported.

## Public/private boundary

`export_examples.py` validates a current native qualification and its hashed
execution before publishing. `public/` contains content-addressed JSON files
with demonstrations and **one** current query input. Give a model one selected
file, not the directory. Private labels, settings, programs, future queries,
turn ordering, source bindings and counts stay in `private.jsonl` and the
controller-side manifest. There is no query-count or final-turn hint in a
public file. The first turn is byte-identical when generation requests just
one query. This is an export projection for the existing controller, not a new
turn loop or a training admission mechanism.
