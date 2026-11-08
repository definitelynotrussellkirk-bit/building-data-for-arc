# Inward legend / enclosed-region family

`adapter.program(settings)` returns exact Racket text. `adapter.generate(seed,
settings,demos=3,queries=4)` returns private claim labels. Settings:
`{"fill_scope":"all"}` (byte-exact reference) and
`{"fill_scope":"largest_per_color"}`. Counts: demos 2..6, queries exactly four.

A: read the edge legend, flood background pockets and measure exact enclosed cells.
Intermediate: region cell lists, boundary colors, areas and directed legend entries.
B: select all or all per-color maximum-area ties, then fill only those region cells.
A bounding-box-area foil changes the alternative's selection and final output.

From the outer packet folder, choose a fresh output after source changes:

```
python3 review.py run python3 generators/public_eval_dbff022c/workspace/parametric/audit.py --seeds 32 --out ../checks/public_eval_dbff022c/audit.json
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_dbff022c --root . --out ../checks/public_eval_dbff022c/preflight
python3 review.py task-tests public_eval_dbff022c --phase after --timeout 180 --out ../checks/public_eval_dbff022c-tests
```

The public controller reveals one content-hash-named file at a time. Never expose
its manifest, private answer bank, presentation order, settings or programs.
