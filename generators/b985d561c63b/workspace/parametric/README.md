# Native parametric family for `b985d561c63b`

This workspace is an opt-in native adapter. It does not change the approved
production generator or the selected canonical Racket rule.

## Episode-fixed parameter

`stamp_anchor` has two values:

- `top_left` — the exact canonical program, byte-for-byte. Copy the complete
  colored-source bounding box, including its internal zero, into the upper-left
  corner of every gray target.
- `hole_corner` — first locate the source crop's unique zero-valued corner, then
  align the complete crop to that same corner of every larger gray target.

The alternate setting has a real sequential dependency:

1. **Step A:** locate the unique zero inside the source bounding box and classify
   it as `top_left`, `top_right`, `bottom_left`, or `bottom_right`.
2. **Intermediate:** the input-dependent corner name.
3. **Step B:** use that corner to choose the destination origin inside every gray
   rectangle, then copy the complete source crop.

A fixed anchor cannot be selected before Step A without failing the minimum
lesson. The first two demonstrations use `top_right` and `bottom_left` cues.

## Native files

- `prototype.py` — deterministic episode construction, guarded Racket source
  materialization, Python claim labels, public projection, and feature helpers.
- `adapter.py` — thin native `program(settings)` / `generate(...)` boundary.
- `promotion.json` — two settings, 2–6 demonstrations, and 1–4 queries.
- `rules/hole_corner_anchor.rkt` — exact guarded alternative rule.
- `rules/fixed_bottom_left.rkt` — bounded wrong-intermediate counterfactual used
  by the causal witness.
- `audit.py` — finite protected-Racket label check plus plausible shortcut audit.

The four query profiles include changed geometry, border contacts, and a dense
30×30 case with four 9×9 gray targets. Inputs are independent of the setting;
demonstration and query prefixes are deterministic and independent of requested
counts.

## Focused checks

From the extracted packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/b985d561c63b/tests/test_parametric_anchor.py -q

python3 review.py run python3 \
  generators/b985d561c63b/workspace/parametric/audit.py \
  --seed 0 --seed 17 \
  --out generators/b985d561c63b/workspace/parametric/evidence/current

python3 review.py run python3 -m arcpuzzles parametric qualify b985d561c63b \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/b985d561c63b/qualification --summary
```

The audit and native qualification are bounded evidence only. Owner exact-source
acceptance and any downstream training admission remain separate actions.
