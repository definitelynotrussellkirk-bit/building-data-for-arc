# Native period/phase component-selection family

This family keeps the selected production generator and canonical rule unchanged.
It varies the periodic positions chosen after the input's non-background
4-connected components are ordered from left to right:

```text
component_index % period == phase
```

Supported settings are `(2,0)`, `(2,1)`, `(3,0)`, and `(3,1)`. The default
`(3,0)` program is byte-for-byte the selected canonical Racket program.
`adapter.py` supports 2–6 demonstrations and 1–4 queries independently; native
qualification uses three demonstrations and four queries. Inputs are matched
across settings, query source profiles are shuffled before prefix selection, and
the four-query bank contains a dense 30×30 row-order trap.

The sequential dependency is substantive: step A discovers and orders whole
components from the input; step B applies the episode-fixed periodic schedule to
positions in that ordered intermediate. `wrong_order.rkt` sorts by top row
instead. The retained protected-Racket witness shows this changes which whole
objects are recolored.

Run the bounded self-review from the packet root:

```sh
python3 review.py run python3 \
  generators/bc0816632908/workspace/parametric/audit.py \
  --out generators/bc0816632908/workspace/parametric/evidence/current/audit.json
```

This is reviewer authoring evidence. Owner exact-source acceptance and any
training admission remain separate.
