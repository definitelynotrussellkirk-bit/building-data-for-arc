# Source-side parametric prototype

This proposed family preserves the source task's guide reflection reasoning. A
full-height color-5 guide is visible in each input, and the episode-fixed
`source_side` setting (`left`, canonical default; or `right`) determines which
side's nonzero, non-5 cells are copied across the first guide. Both sides contain
sources and identical inputs are used for both settings, so demonstrations—not
surface grammar—identify the rule.

The prototype accepts 2–6 demonstrations and exactly four queries. Query shapes
are 12×15, 16×20, 24×27, and 30×30. Cases cover multiple guides, occupied mirror
targets, clipping, and literal color 5 filtering. The certificate also refutes
“mirror both sides” and “move rather than copy.” Settings, programs, query answers,
and evidence metadata stay private; public bytes contain demonstrations and query
inputs only. This is proposed authoring evidence, not qualification, acceptance,
or training admission.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/cddbee92b2f3/workspace/parametric/prototype.py \
  --all-settings --seed 0 --demos 3 --queries 4 \
  --out ../checks/cddbee92b2f3-parametric-example

python3 review.py run python3 -m pytest -q \
  generators/cddbee92b2f3/tests/test_parametric_source_side.py
```

The export stores the complete four-query container under `controller/`; it is
controller data and must not be shown wholesale. `manifest.json` is controller
metadata too and must not enter model context. Files under `public/` contain
the demonstrations plus exactly one query, with opaque visible-byte IDs, no
query totals or future inputs, and an identical first turn for one-query use.

The CLI uses the bundled protected Racket runtime to execute every retained label
and the alternate rule on demonstrations before writing the evidence export.
