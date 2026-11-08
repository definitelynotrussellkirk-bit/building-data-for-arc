# Big-side secondary relay

This native family keeps the source task's exact count-and-pack rule and varies
one private episode-fixed parameter:

| `secondary` | Rule |
|---|---|
| `next_repeated` | Exact selected canonical Racket source, byte-for-byte: after the largest foreground mass, pack the largest remaining repeated mass. |
| `big_side_relay` | Select the largest mass, derive its square side, then pack the unique remaining color whose count equals that derived side. |

The sampler is setting-neutral and supports 2–6 demonstrations plus 1–4
queries independently. The first two demonstrations constructively distinguish
both settings and a finite bank of count, color, position, component, bounding
box, and density shortcuts. Four query prefixes cover 10×12, 18×20, 23×17,
and a substantive 30×30 scene with more than 400 non-background cells and
content on all four boundaries.

## Sequential dependency

**A:** count all non-background colors, select the unique largest mass, and
compute its integer square side. **Intermediate:** that input-derived side.
**B:** select the unique remaining color whose count equals the intermediate,
then pack its square beside the largest square. B cannot know its target count
before A has selected and square-rooted the largest mass.

`fixed_four_relay.rkt` is a private wrong-intermediate counterfactual. On the
retained protected-Racket witness, the true intermediate is 9; substituting 4
selects another color and changes the final output.

## Public projection

`family.public_turn(episode, query_index)` exposes all demonstrations and only
the current unlabeled query input. Exact public bytes and IDs come from
`reviewer_support.public_challenge_bytes` and `public_challenge_id`; settings,
programs, query answers, future inputs, and total-count hints remain private.
The first turn is byte-identical for one-query and four-query requests.

## Reproduce

From the outer packet directory:

```bash
python3 review.py run python3 -m pytest \
  generators/b5b012cd97d9/tests/test_parametric_family.py -q

python3 review.py run python3 \
  generators/b5b012cd97d9/workspace/parametric/audit.py \
  --out generators/b5b012cd97d9/workspace/parametric/evidence/new-run \
  --seeds 0,17 --sweep 64

python3 review.py run python3 -m arcpuzzles parametric qualify b5b012cd97d9 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/b5b012cd97d9/qualification --summary
```

All evidence is bounded. It does not establish universal uniqueness, measured
learning benefit, owner acceptance, or training admission.
