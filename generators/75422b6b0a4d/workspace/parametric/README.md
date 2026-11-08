# Native parametric family: flood, then optionally outline the largest chamber

Status: reviewer-ready prototype; owner integration, fresh qualification, and exact-source acceptance remain required.

## Episode-fixed parameter

`finish` has two values:

- `flood` — the exact canonical `75422b6b0a4d` Racket program, byte-for-byte.
- `outline_largest` — run the canonical flood, identify the unique largest filled chamber, then recolor only wall cells four-adjacent to that chamber with its seed color.

The sampler uses identical inputs for both settings. Only the program and labels change.

## Required sequential dependency

- **A:** flood every chamber from its single colored seed through cells originally equal to `0` or that seed color.
- **Intermediate:** the seed color and spatial cell set of the unique largest chamber after A.
- **B:** recolor the wall boundary touching that selected chamber with the intermediate seed color.

B cannot choose its color or wall locations before A identifies the selected filled region. The protected-Racket witness uses the same A but deliberately selects the smallest chamber as the wrong intermediate; the final spatial boundary changes.

## Sampling and reveal contract

- Demonstrations: exactly 2–6.
- Queries: exactly 1–4, with four materialized for qualification/export.
- Query sizes: `14x16`, `20x23`, `26x28`, and a substantive `30x30` case.
- Demonstration and query sequences are independent prefixes. A one-query request has exactly the same first query as a four-query request.
- Public IDs must be derived only from public challenge bytes. Settings, programs, and query answers are private.
- The construction has 3–4 irregular chambers, one wall color in 5–9, one seed per chamber, a unique largest chamber, and a largest-chamber seed touching at least one wall. The last property prevents the `outline_seed_touch_only` rival from collapsing to canonical flood.

## Bounded teaching audit

Every two-demo lesson distinguishes the selected setting from the other setting and from these finite rivals:

- outline the smallest chamber;
- outline the top-left chamber;
- outline the color-1 chamber;
- recolor all walls;
- omit the outside border;
- recolor only wall cells touching the selected seed.

This is a finite shortcut audit, not a proof of universal semantic uniqueness.

## Files

- `adapter.py` — native adapter entry point.
- `family.py` — exact programs, constructive sampler, transforms, and bounded audit helpers.
- `promotion.json` — native promotion contract.
- `evidence/manifest.json` — generated source/evidence inventory.

## Verification commands

From the packet outer directory:

```sh
python3 review.py run python3 -m pytest \
  generators/75422b6b0a4d/tests/test_parametric_largest_outline.py -q

python3 review.py run python3 -m arcpuzzles parametric qualify 75422b6b0a4d \
  --out ../checks/75422b6b0a4d/qualification --summary
```

The reviewer qualification is evidence for handoff, not owner acceptance. After integration, the owner must rerun qualification and accept the exact live source binding.
