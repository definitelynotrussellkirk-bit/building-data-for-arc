# Marker-side parametric prototype

This proposed family keeps the source task's row-selection reasoning but places
one magenta marker on each horizontal border in different rows. The episode-fixed
`marker_side` setting (`left`, canonical default; or `right`) decides which marker
selects the payload row and which marker column is dropped. Identical input
streams are used for both settings, so the rule must be learned from demonstrations.

The prototype accepts 2–6 demonstrations and exactly four queries. Query shapes
are 9×11, 13×17, 20×24, and 30×30. Rows have equal nonzero density and unique
payloads, refuting fixed-row and density shortcuts. Settings, programs, query
answers, and evidence metadata remain private; public bytes contain demonstrations
and query inputs only. This is proposed authoring evidence, not qualification,
acceptance, or training admission.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/d07a6cba78c7/workspace/parametric/prototype.py \
  --all-settings --seed 0 --demos 3 --queries 4 \
  --out ../checks/d07a6cba78c7-parametric-example

python3 review.py run python3 -m pytest -q \
  generators/d07a6cba78c7/tests/test_parametric_marker_side.py
```

The export stores the complete four-query container under `controller/`; it is
controller data and must not be shown wholesale. `manifest.json` is controller
metadata too and must not enter model context. Files under `public/` contain
the demonstrations plus exactly one query, with opaque visible-byte IDs, no
query totals or future inputs, and an identical first turn for one-query use.

The CLI uses the bundled protected Racket runtime to execute every retained label
and the alternate rule on demonstrations before writing the evidence export.
