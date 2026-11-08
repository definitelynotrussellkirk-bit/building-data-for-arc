# Connectivity parametric prototype

This proposed family preserves the source task's component-size recoloring:
non-background objects of size 1, 2, and 3 become colors 3, 2, and 1; objects of
size 4 or more become 0. The episode-fixed `connectivity` setting (`4`, canonical
default; or `8`) chooses how objects are grouped. Every input contains diagonal
singleton–singleton and singleton–domino contacts, and the identical inputs are
used under both settings, so demonstrations must identify connectivity.

The prototype accepts 2–6 demonstrations and exactly four queries. Query shapes
are 10×10, 16×18, 24×26, and 30×30. Larger cases add many isolated pockets rather
than empty padding. The certificate refutes cellwise-singleton and no-op shortcuts.
Settings, programs, query answers, and evidence metadata stay private; public bytes
contain demonstrations and query inputs only. This is proposed authoring evidence,
not qualification, acceptance, or training admission.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/bb75d495c809/workspace/parametric/prototype.py \
  --all-settings --seed 0 --demos 3 --queries 4 \
  --out ../checks/bb75d495c809-parametric-example

python3 review.py run python3 -m pytest -q \
  generators/bb75d495c809/tests/test_parametric_connectivity.py
```

The export stores the complete four-query container under `controller/`; it is
controller data and must not be shown wholesale. `manifest.json` is controller
metadata too and must not enter model context. Files under `public/` contain
the demonstrations plus exactly one query, with opaque visible-byte IDs, no
query totals or future inputs, and an identical first turn for one-query use.

The CLI uses the bundled protected Racket runtime to execute every retained label
and the alternate rule on demonstrations before writing the evidence export.
