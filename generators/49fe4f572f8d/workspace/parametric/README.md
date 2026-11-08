# Column gravity with one clearing pass

This separate native adapter proposes two episode-fixed `mode` settings:

| Mode | Rule |
| --- | --- |
| `down` (default) | Pack each column downward, preserving its nonzero values' top-to-bottom order. Its program is byte-for-byte the canonical authority. |
| `settle_clear_once` | Settle downward; find all same-color four-connected components of at least three cells in that settled grid; erase their cells simultaneously; settle downward again. Stop after this one clearing pass. |

Zero is the background. The composition preserves the canvas dimensions. A group
created by the final settle remains, even if it now contains three or more cells.
Selection comes from one intermediate snapshot, so clearing one group and
re-settling before selecting the next would be a different rule.

## Why the sequence matters

Initial gravity creates contacts that were absent in the input. Those contacts
determine the groups to erase. Erasure then creates holes that the final gravity
closes. The first demonstration places one color above a vertical triple and next
to a retained two-cell group: removing the triple permits a new group to form
only after the final settle. The second demonstration combines a size-four group,
a size-three group whose connectivity would change under sequential clearing,
and a diagonal-only group that must survive four-connectivity.

Color relabeling, dimensions, offsets and cell scattering vary with the seed.
The first two demonstrations are selected using demonstrations alone against
both settings and the declared finite rival family. Neither private settings nor
query labels/counts select the visible inputs. Additional demonstrations and
queries use independent deterministic streams, so changing counts preserves all
shared prefixes. This is a finite teaching check, not a uniqueness proof against
all possible programs.

## Domain and public projection

- Exact integer seeds: `0..2**63-1`; booleans are rejected.
- Independent counts: 2–6 demonstrations and 1–8 queries; defaults 3 and 4.
- Extended prototype canvas: 6–30 rows, 7–30 columns, integer colors 0–9.
- First four query profiles: 6×7, 30×30, 6×30 and 30×7.
- The 30×30 case contains 360–720 foreground cells distributed over all thirty
  columns, with occupied cells on both the first and last row. It is substantive
  gravity/clearing work, not a small example surrounded by padding.
- `turn_bytes(episode, index)` emits the demonstrations and exactly one masked
  query. It exposes no private mode, seed, program, query answer or future count.
- Public filenames are SHA-256 hashes of canonical public challenge bytes.
  Private-only metadata changes therefore preserve the public file and its name.

The selected production generator retains its original smaller sparse domain.
The extension lives wholly in this workspace and is not selected automatically.

## Reproduce from the review packet root

The packet's `setup` / `python-check` commands provide the environment contract:
Python 3.12+, pytest, NumPy, Pillow, and the bundled protected Racket executable.
No sibling checkout or downloaded application code is required. Choose fresh
output directories for each run.

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/49fe4f572f8d/tests/test_parametric.py \
  generators/49fe4f572f8d/tests/test_parametric_verifier.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/49fe4f572f8d/workspace/parametric/verify.py \
  --out ../checks/49fe4f572f8d/focused-new

WORK/.venv/bin/python review.py run python3 \
  generators/49fe4f572f8d/workspace/parametric/prototype.py \
  --seed 17 --demos 3 --queries 4 --out ../checks/49fe4f572f8d/examples-new
```

`verify.py` is a reusable, bounded authoring tool. It checks count/shape/prefix
contracts, verifies labels and named alternative programs through live protected
Racket, fits alternatives on demonstrations first, and retains exact programs,
episodes, source hashes and first refutations. Runtime failures abort the check.
Negative tests prove that corrupted labels and a demo-fitting, query-changing
alternative are detected. Python predictions remain claims until executed.

`prototype.py` verifies every label before exporting. Hand learners only its
`public/` files or `turn_bytes`; the full episodes, query answers, program text
and verification evidence under `private/` are authoring material.

## Native evidence and admission

`promotion.json` declares the native contract. `evidence/manifest.json` binds its
source closure; the returned `checks/49fe4f572f8d/qualification/` and `causal/`
directories retain native qualification and counterfactual replay receipts.
These are reviewer checks. Exact-source owner acceptance after integration and
any training admission remain separate decisions.
