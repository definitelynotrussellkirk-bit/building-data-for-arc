# Proposed rectangle render variants

This task-local prototype keeps the canonical color-specific corner-marker
inference and changes one episode-fixed rule parameter:

| `render` | Executed transformation |
|---|---|
| `outline` (canonical default) | Draw the hollow perimeter of every color's bounding box. |
| `filled` | Fill every cell of every color's bounding box. |

Inputs are identical across settings.  Each episode has 2–6 demonstrations and
1–4 queries independently; retained checks use four distinct queries.  The
query profiles include a substantive 30×30 case with marker objects distributed
through all four quadrants.  The default program is byte-for-byte the selected
canonical Racket authority.  The production generator and its approval remain
unchanged; this proposed family is not accepted or training-admitted.

## Focused checks

From the packet outer directory after `python3 review.py setup`:

```bash
python3 review.py run python3 -m pytest -q \
  generators/a452b4b4f04a/tests/test_parametric.py
python3 review.py run python3 \
  generators/a452b4b4f04a/workspace/parametric/probe.py \
  --out generators/a452b4b4f04a/workspace/parametric/evidence/current
```

The probe executes every label through protected Racket for both settings at
seeds 0 and 17 with 2, 3, and 6 demonstrations and four queries.  It also writes
and verifies a compact sequential public/private bundle.

## Sequential public projection

`episode_io.write_bundle(...)` emits one hash-named public challenge per query.
Each public file contains the demonstrations and one query input only.  Settings,
seed, reference program, query answer, query index, and total query count stay in
`private.jsonl`.  Therefore the first public bytes from a four-query episode are
identical to a one-query episode with the same seed, setting, and demo count.
The helper refuses duplicate visible challenges and existing destinations, writes
atomically, and verifies file hashes and the exact public/private projection.

## Native handoff

`adapter.py` loads the adjacent prototype by exact path.  `promotion.json`
declares the finite setting/count contract.  After fresh evidence, inventory it
with:

```bash
python3 review.py run python3 -m arcpuzzles parametric manifest a452b4b4f04a \
  --evidence generators/a452b4b4f04a/workspace/parametric/evidence/current \
  --include generators/a452b4b4f04a/tests/test_parametric.py \
  --reported-checks 'Protected-Racket finite-setting checks, count boundaries, 30x30 query, and strict sequential export.'
```

Inventory and qualification remain authoring evidence, not acceptance or
training admission.
