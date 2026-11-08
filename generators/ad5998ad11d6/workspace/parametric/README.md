# Proposed `fill_color` rule parameter

This task-local prototype keeps the original topological reasoning intact:
find every black component that cannot reach the edge by 4-connectivity, preserve
the green walls and exterior black cells, and recolor all enclosed black cells.
The one episode-level parameter changes only that final recoloring value.

- Parameter: `fill_color`
- Allowed values: `4` (canonical/default), `2` (proposed nearby variant)
- Input constraints depending on the parameter: none
- Episode contract: choose one value once from the episode seed; use it for all
  three demonstrations and the query
- Production status: **prototype only**. The selected generator and canonical
  authority remain fixed to color 4.

The materializer executes the exact instantiated Racket rule for every selected
and rival label. It writes two complete private episodes, public versions with
the parameter/program/query output removed, exact `.rkt` files, a shared-input
witness, source hashes, runtime identity, and explicit limits.

From the packet's outer extraction directory:

```bash
rm -rf WORK/checks/parametric/fill-color
python3 review.py run python3 generators/ad5998ad11d6/workspace/parametric/prototype.py \
  --seed 73 --out ../checks/parametric/fill-color
```

Focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/ad5998ad11d6/tests/test_parametric_fill_color.py
```
