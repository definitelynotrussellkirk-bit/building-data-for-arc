# Pack-then-rank output-color family

This task-local family keeps the selected canonical rule byte-for-byte as the
`original` default and adds one episode-fixed setting, `rank`.

## Rules

- **`original`**: find the nonzero 4-connected components, crop each component,
  rank crops by `(enclosed holes descending, foreground area descending, color
  ascending)`, then pack them top-aligned from left to right with one blank
  column between adjacent crops.
- **`rank`**: perform the complete canonical packing first; on that
  input-derived intermediate, recompute the packed components from left to
  right and recolor them `1, 2, 3, 4`. Stage B therefore consumes the order and
  geometry produced by Stage A. `skip_pack.rkt` is the protected-Racket
  counterfactual that applies Stage B directly to the source layout.

The two settings use matched inputs. Supported demonstration counts are 2–6;
every episode retains exactly four distinct query pairs. Query 4 is a substantive
30×30 boundary-touching scene. The controller exposes one shuffled query input
per turn; settings, programs, future inputs, and query answers remain private.

## Constructive teaching controls

The minimum two-demo lesson is intentionally constructed rather than accepted by
retry luck:

- teaching colors are permuted until pure color sorting disagrees with the real
  component order;
- equal-area/one-hole components have different geometry, so the ascending color
  tie-break remains observable after rank recoloring;
- tied demonstrations align source rows and reverse horizontal placement, so
  scan order cannot substitute for area or color tie-breaks;
- the two fixed teaching profiles separately expose the area and color portions
  of the lexicographic key.

These controls were added after concrete failures at seed 286 (pure color order),
a reversed-color tie hidden by duplicate geometry, and a stable holes-only sort
that exploited source scan order.

## Reusable authoring probes

Run from `WORK/repo` through the packet launcher so the protected Racket runtime
and isolated Python imports are used:

```sh
python3 ../../review.py run python3 \
  generators/06789067e67f/workspace/parametric/semantic_sweep.py \
  --seeds 200 --out ../checks/06789067e67f/semantic-sweep.json

python3 ../../review.py run python3 \
  generators/06789067e67f/workspace/parametric/adversarial_probe.py \
  --out ../checks/06789067e67f/adversarial.json
```

`semantic_sweep.py` cheaply checks many seeds against Python mirrors of sort,
packing, and rank bypasses. `adversarial_probe.py` executes the corresponding
program bank through protected Racket, retains one concrete counterexample per
wrong program, checks 2- and 6-demo boundaries, exercises the 30×30 query, and
attacks malformed contracts plus public/private leakage.

The probes are finite falsification, not a universal uniqueness proof. This is a
reviewer-authored proposal only; owner source review, native qualification and
acceptance, training admission, and training activation remain separate.
