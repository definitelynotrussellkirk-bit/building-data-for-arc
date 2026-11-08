# Native direction-policy family for `e99db71ae23d`

This directory adds a promotion-ready, episode-parametric family without changing the approved production generator or canonical Racket rule.

## Parameter

`direction_policy` has two settings:

- `gray_toward_red_away` — the exact canonical program, byte-for-byte.
- `gray_away_red_toward` — the same component discovery, missing-corner intermediate, colors, clipping, and green-last collision precedence, with the color/direction assignment swapped.

Every seed produces the same visible input stream under both settings. Episodes support 2–6 demonstrations and exactly four distinct queries. The fourth query is a constructed 30×30 stress scene with 16 L-trominoes, all four orientations in both source colors, boundary clipping, both policy-specific collision motifs, and source coverage in every quadrant.

## Sequential dependency

A. Find each color-2 or color-5 connected component and its missing corner in the component's 2×2 box.

Intermediate. The input-dependent opening vector `(dr, dc)` for each L-tromino.

B. According to the episode setting and piece color, keep or negate that vector, project all three cells with clipping, then apply yellow before green so green wins collisions.

The retained protected-Racket witness replaces all per-piece opening vectors with a fixed southeast vector and changes the final output on a qualified query.

## Files

- `adapter.py` — native adapter entry points.
- `prototype.py` — deterministic sampler, Python mirror, bounded rivals, scene analysis, and stress construction.
- `audit.py` — reusable protected-Racket audit of both settings and six plausible rivals; writes public challenges separately from private settings and answers.
- `promotion.json` — native promotion contract.
- `evidence/manifest.json` — source/evidence inventory bound to the current adapter.

## Reproduction

From the packet's outer directory:

```sh
python3 review.py task-tests e99db71ae23d --phase after --out ../checks/e99db71ae23d-tests-new
python3 review.py run python3 generators/e99db71ae23d/workspace/parametric/audit.py \
  --out generators/e99db71ae23d/workspace/parametric/evidence/recheck
python3 WORK/check_public_exports.py \
  WORK/repo/generators/e99db71ae23d/workspace/parametric/evidence/recheck/public \
  --demos 3 --queries 4
python3 review.py run python3 -m arcpuzzles parametric qualify e99db71ae23d \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/e99db71ae23d/qualification-new --summary
```

Use fresh output paths; the native tools intentionally refuse to overwrite evidence.

## Limits

The retained checks establish exact default preservation, finite sampler robustness, protected-Racket parity, and finite learnability against the declared alternate plus six authored plausible rivals. They do not prove universal hypothesis uniqueness, measured learner improvement, owner acceptance, or training admission.
