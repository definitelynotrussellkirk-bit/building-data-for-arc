# Native color-order parametric adapter

Status: **reviewer-ready; exact-source owner acceptance pending**. This native
adapter does not modify the production generator, canonical Racket authority,
`RULE_HASH`, or training state.

## Contract

- Parameter: `color_order = ascending | descending`.
- Default: `ascending`, byte-identical to the canonical Racket program.
- Demos: independently selectable from 2 through 6.
- Queries: independently selectable from 1 through 4; qualification uses four.
- Inputs: deterministic and setting-independent for the same seed/counts.
- Labels: executed through the protected Racket bridge and mirrored in Python.
- Public projection: demonstrations are labeled; query inputs are revealed
  sequentially without settings, future inputs, total-count hints, or answers.

`ascending` processes numeric colors from low to high. `descending` reverses only
that list. Each color fills still-zero cells inside the bounding box of its two
anchors, so the first processed color claims overlap cells and the second color
must consume the accumulated intermediate grid.

The native family uses overlapping, boundary-contacting boxes across a fixed
shape schedule. The first two demonstrations alternate whether the high or low
color is first in row-major order, which defeats a first-seen shortcut while
preserving the intended numeric-order rule. The first query is independent of
query count and is a dense 30×30 instance.

## Files

- `adapter.py`: native entry points and promotion contract implementation.
- `native_family.py`: deterministic input construction and Python label mirror.
- `promotion.json`: native adapter declaration and supported bounds.
- `audit_native.py`: reusable bounded protected-Racket rival audit.
- `evidence/manifest.json`: source-bound native inventory.
- `evidence/native-ready/`: compact focused/full-suite/audit evidence.

## Reproduce from the extracted packet root

```bash
python3 review.py run python3 -m pytest -q \
  generators/021fb6acf24f/tests/test_parametric_native_adapter.py

python3 review.py run python3 \
  generators/021fb6acf24f/workspace/parametric/audit_native.py \
  --seed 0 --out ../checks/021fb6acf24f/self-audit.json

python3 review.py run python3 -m arcpuzzles parametric qualify 021fb6acf24f \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/021fb6acf24f/qualification --summary
```

The retained qualification covers both settings at seeds 0 and 17 and records
four demonstrations-independent queries per job. The bounded self-audit rejects
opposite order, row-major first occurrence, late overwrite, and identity from
two visible demonstrations. These are finite checks, not a universal induction
proof. Owner acceptance and training admission remain separate required steps.
