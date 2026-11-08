# Proposed symmetry/order rule prototype

This task-local prototype leaves the selected production generator and canonical
Racket authority unchanged. It chooses two bounded hidden parameters once per
complete episode:

| Parameter | Values | Original/default | Effect |
|---|---|---|---|
| `reflection_mode` | `dihedral`, `rotations_only` | `dihedral` | Match the full rotation/reflection orbit, or rotations only. |
| `column_order` | `left_to_right`, `right_to_left` | `left_to_right` | Resolve same-row overlapping candidates in canonical or reversed column order. |

The default `(dihedral, left_to_right)` program is byte-for-byte the canonical
Racket authority. Each input is an approved selected-generator draw with one
isolated 2×4 color-3 overlap motif. The original stencil/copy roles, geometric
matching, and greedy non-overlap reasoning remain intact. The motif makes the
column-order choice observable, while the generator's reflection-only copy makes
the reflection choice observable.

Each retained episode contains **3 demonstrations and 4 distinct queries** under
one fixed setting. Every individual pair has four distinct outputs across the
four settings, so the demonstrations reject all three alternate settings before
any query answer is considered.

Run the exact Racket-backed materialization from the outer packet directory:

```bash
python3 review.py run python3 \
  generators/195dfcc5b541/workspace/parametric/verify.py \
  --seed-base 20261023 \
  --artifact-dir ../checks/parametric/195dfcc5b541-symmetry-order \
  --out ../checks/parametric/195dfcc5b541-symmetry-order-report.json
```

The verifier executes the canonical default on all five canonical labels, checks
28 stored labels and 84 rival labels through the matching Racket programs, checks
48 query/rival identifiability cases using demonstrations only, and writes four
answer-masked public challenges. Public filenames are SHA-256 IDs of the exact
visible bytes; settings, seeds, programs, private metadata, and query answers do
not affect their names.

Run the bounded adversarial pass (sampler/retry boundaries, 16+16 count boundary,
public-ID privacy invariants, and an independent second Racket seed base):

```bash
python3 review.py run python3 \
  generators/195dfcc5b541/workspace/parametric/adversarial_probe.py \
  --seed-start 0 --seed-count 32 \
  --out ../checks/parametric/195dfcc5b541-symmetry-order-adversarial.json
```

Scope: **proposed task-local prototype**. It does not modify or reapprove the
canonical generator/rule, resolve the historical audit in production, or admit
any variant to training. Evidence is finite and compares only the four declared
settings.
