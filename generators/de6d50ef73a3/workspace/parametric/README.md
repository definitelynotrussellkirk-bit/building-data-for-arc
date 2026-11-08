# Top-left / marker-corner crop-placement prototype

This proposed family preserves the exact canonical global nonzero crop as its
default and adds one input-dependent placement setting.

| Setting | Transformation | Authority |
| --- | --- | --- |
| `top_left` | Tight global nonzero crop pasted at canvas top-left | Exact canonical Racket bytes |
| `marker_corner` | Find the unique singleton marker's corner inside the crop and paste the full crop at the corresponding canvas corner | Protected Racket alternate rule |

The parametric sampler intentionally uses a narrower teaching grammar than the
canonical task: one fully interior, 4-connected, multicolor object; one uniquely
least-frequent color appearing once at a tight-bounding-box corner; and at least
two repeated body colors. This restriction makes the marker semantic observable.
It does not narrow the repaired canonical generator or its validator.

Inputs are deterministic and independent of the selected setting. The first two
demonstrations use marker corners `top_right` and `bottom_left`; together they
separate both settings from fixed top-right, bottom-left, bottom-right, and
identity rivals. Four query profiles cover all marker corners in this order:
`top_right`, `bottom_left`, `bottom_right`, `top_left`. The last is a substantive
30×30 canvas with a 20×21 crop.

Every retained label is executed by the packet's protected Racket bridge and
checked against an independent Python oracle. Teaching uses demonstrations only;
query labels are checked after the setting is identified. The evidence establishes
only finite-rival authoring compatibility. It is not owner acceptance, canonical
approval of the alternate, or training admission.

Run from the outer packet directory:

```bash
python3 review.py run pytest -q \
  generators/de6d50ef73a3/tests/test_generator_contract.py \
  generators/de6d50ef73a3/tests/test_parametric_placement.py
python3 review.py run python \
  generators/de6d50ef73a3/workspace/parametric/probe.py \
  --out generators/de6d50ef73a3/workspace/parametric/evidence/new-run
```

`adapter.py` exposes native `program(settings)` and
`generate(seed, settings, demos, queries)`. Requests require exact integer seed
`0..2^63-1`, 2–6 demonstrations, 1–4 queries, and exactly one placement setting.
`promotion.json` declares the default, parameter values, limits, and source files.
