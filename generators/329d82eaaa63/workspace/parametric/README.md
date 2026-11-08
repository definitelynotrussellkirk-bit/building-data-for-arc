# Proposed odd-row branch policies

This task-local prototype preserves the canonical top-row seed inference and
changes one episode-fixed rule parameter:

| `branches` | Executed transformation |
|---|---|
| `both` (canonical default) | Paint both one-cell diagonal branches on odd rows. |
| `left` | Paint only the branch one column left of each seed. |
| `right` | Paint only the branch one column right of each seed. |

Inputs are identical across settings. Each episode has 2–6 demonstrations and
1–4 queries independently; retained checks use four distinct queries. The
query profiles include a substantive 30×30 grid with eight separated seeds
spread across the width. The default program is byte-for-byte the selected
canonical Racket authority. The production generator and approval remain
unchanged; this family is proposed evidence only, not accepted training data.

`episode_io.py` is a strict reusable sequential exporter. It emits one
hash-named public challenge per query, containing all demonstrations and one
query input only. Settings, seed, program, answer, query index, and total query
count remain private. It refuses duplicate visible challenges and existing
destinations, writes atomically, and verifies exact hashes and projection.

Run focused evidence from the packet outer directory:

```bash
python3 review.py run pytest -q generators/329d82eaaa63/tests/test_parametric.py
python3 review.py run python3 \
  generators/329d82eaaa63/workspace/parametric/probe.py \
  --out generators/329d82eaaa63/workspace/parametric/evidence/current
```
