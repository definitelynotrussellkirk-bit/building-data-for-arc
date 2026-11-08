# Native transform-script order family

This task-local family preserves the selected canonical rule exactly and adds
one episode-fixed nearby rule. It is a prototype for native qualification; it
does not alter the production generator, accept a family, or admit data to
training.

## Settings

| `script_order` | Behavior |
|---|---|
| `left_to_right` | Read nonzero instruction codes from row 0 left-to-right and apply all corresponding transforms in that order. This is the byte-exact selected Racket source. |
| `right_to_left` | Read the same visible instruction cells right-to-left and apply all transforms in that reversed order. |

The family has a real sequential dependency:

1. **Step A:** read the nonzero instruction cells in the episode-selected
   direction.
2. **Intermediate:** the ordered sequence of transform codes.
3. **Step B:** crop the nonzero motif below row 0 and fold every listed transform
   over the current result in that order.

The transform group is generally noncommutative on the asymmetric sampled
motifs. Forcing the opposite code order changes the protected-Racket output; the
causal witness is built from a qualified noncanonical episode.

## Episode contract

`adapter.py` exports `program(settings)` and
`generate(seed, settings, demos, queries)`. Supported requests use 2–6
independently prefix-stable demonstrations and 1–4 independently prefix-stable
queries. Inputs are deterministic and identical across settings for the same
seed/count request. The first two demonstrations distinguish both declared
orders and the fixed sequence shortcuts in `audit.py`, including sorting,
deduplication, adjacent-collapse, first-only, last-only, and ignoring the script.

The fourth query is a 30×30 input. Its connected, asymmetric 28×30 body has more
than 500 colored cells and touches the left, right, and bottom boundaries.

`native.public_turn(episode, index)` returns all visible demonstrations and one
answer-masked query input. It excludes the setting, source program, future
queries, query answers, seed, and total-query hints; its first turn is identical
to a one-query request.

The named rivals are a finite diagnostic family, not a proof of unique induction
against every possible program.

## Reproduce scoped checks

From the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/8096ecc43d5a/tests/test_native_parametric_8096ecc43d5a.py

python3 review.py run python3 \
  generators/8096ecc43d5a/workspace/parametric/audit.py \
  --public-dir generators/8096ecc43d5a/workspace/parametric/evidence/current/public \
  --out generators/8096ecc43d5a/workspace/parametric/evidence/current/self-audit.json

python3 review.py run python3 -m arcpuzzles parametric qualify 8096ecc43d5a \
  --seed 0 --seed 17 --demos 2 --queries 4 \
  --out ../checks/8096ecc43d5a/qualification --summary
```

The audit and qualification require the bundled protected Racket runtime. Saved
public files are content-addressed from visible bytes only. Current source hashes,
reported checks, and compact evidence are bound by
`workspace/parametric/evidence/manifest.json`.
