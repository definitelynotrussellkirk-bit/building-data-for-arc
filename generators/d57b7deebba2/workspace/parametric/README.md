# Native parametric adapter for `d57b7deebba2`

This directory contains a source-bound two-setting family built around the
unchanged canonical anti-diagonal-span rule.

## Settings

- `relay_policy=fill_only` uses `canonical.rkt` byte-for-byte. It groups
  nonzero cells by `(color, row + column)` and fills each anti-diagonal span.
- `relay_policy=activated_projection` first performs that same fill. Exactly
  one color-8 relay is then adjacent to a cell that changed from zero to a
  span color. The relay takes that color and projects it away from the newly
  filled neighbor through cells still zero after the fill, stopping at a
  completed object or the grid boundary.

The second setting is deliberately sequential: the relay, touched color, and
projection direction are not determined until the canonical fill creates the
activation cell.

## Adapter contract

`adapter.py` supports 2–6 demonstrations and 1–4 sequentially revealed
queries. For a fixed seed and count, the two settings expose identical inputs.
The public projection omits settings, programs, seeds, future queries, query
answers, and any total-query-count hint.

## Reproduce the bounded authoring audit

Run from the packet root, not directly from this directory, so the protected
runtime and imports are supplied by `review.py`:

```bash
python3 review.py run python3 \
  generators/d57b7deebba2/workspace/parametric/audit.py \
  --seed 20261025 \
  --out ../checks/d57b7deebba2/authoring-audit \
  --sweep-seeds 50
```

The audit executes both selected Racket programs and six executable nearby
rivals, exports content-addressed public challenges, checks sequential masking,
materializes a wrong-intermediate causal case, and sweeps both settings across
all demonstration counts for 50 seeds.

## Scope

The teaching result is finite: it distinguishes the two declared settings from
six authored rivals on retained lessons. It is not a proof against every
possible hypothesis. Owner exact-source integration, a fresh owner-side native
acceptance replay, and training admission remain separate decisions.
