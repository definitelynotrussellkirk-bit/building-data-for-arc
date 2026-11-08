# Contact-color relay parametric family

This task-local family preserves the selected canonical rule as the default and
adds one nearby, episode-fixed alternative.  It is reviewer-ready source for
native qualification; it is not owner-accepted or training-admitted.

## Settings

| `relay_mode` | Rule |
|---|---|
| `columns_only` | Exact canonical source: each nonzero top-row marker fills its complete column on a fresh zero grid. |
| `contact_color_rows` | Perform the canonical column expansion, then find the unique lower color-9 probe newly touching one expanded marker column.  Its contacted marker color selects remote lower payload rows of that color, which are filled completely. |

The alternative has a real input-dependent sequence:

1. **A — column expansion:** expand every top-row marker into its full column.
2. **Intermediate:** identify the marker color newly touching the unique active
   color-9 probe and the remote payload rows carrying that color.
3. **B — row relay:** fill those selected rows with the intermediate color while
   retaining the expanded columns.

B cannot be selected from the original input: every probe has zero horizontal
neighbors before A.  `wrong_order.rkt` deliberately reads the probes before A;
it therefore leaves only the canonical columns, while the qualified alternate
fills additional rows.

## Generation contract

- One private setting is fixed across the episode.
- The two settings receive byte-identical inputs for the same seed and counts.
- Demonstrations: independently selectable from 2 through 6.
- Queries: exactly four stored, revealed publicly one at a time.
- Query shapes: 11×14, 14×18, 22×25, and a substantive 30×30 boundary case.
- Public IDs hash only canonical public bytes.  Settings, programs, future query
  inputs, total-query hints, and query answers are omitted.
- The minimum two demonstrations constructively separate both declared settings
  and the finite shortcut set in `prototype.RIVALS`.

## Reproduce the bounded authoring audit

From `WORK/repo`:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/5419b6df2873/workspace/parametric/audit.py \
  --seed-count 64 \
  --out generators/5419b6df2873/workspace/parametric/evidence/current/self-audit.json \
  --public-dir generators/5419b6df2873/workspace/parametric/evidence/current/public
```

The retained sweep covers 64 seeds, both settings, demonstration counts 2, 3,
and 6, all four queries, 14 declared shortcuts, both contact sides, and sizes
through 30×30.  It is a finite Python-reference audit, not native execution.
Protected-Racket labels are established separately by the packet's native
`parametric qualify` command and the retained qualification receipts.

Public-file structure is checked with the packet-local
`WORK/check_public_exports.py`.  Evidence includes a positive eight-file check
and a negative leaked-answer challenge that the checker rejects.

## Native files

- `adapter.py` — native `program(settings)` and `generate(...)` entrypoint.
- `promotion.json` — settings, defaults, supported counts, and resources.
- `canonical.rkt` — exact selected canonical source bytes.
- `contact_color_rows.rkt` — alternate sequential rule.
- `wrong_order.rkt` — protected-Racket causal ablation.
- `prototype.py` — deterministic sampler, Python claims, finite rivals, and
  one-query public projection.
- `audit.py` — reusable bounded authoring and export audit.
- `evidence/manifest.json` — source-bound inventory.

The finite rival audit does not prove universal identifiability or measured
training benefit.  Owner acceptance must rerun native qualification against the
exact integrated bytes before any downstream use.
