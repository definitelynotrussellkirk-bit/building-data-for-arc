# Native parametric candidate for b98cdd1751a7

`adapter.py` is the promotion entrypoint and loads the exact adjacent
`native.py`. The candidate keeps the production generator and canonical
reference separate: qualification and owner acceptance are still required.

## Episode-fixed parameter

`bottom_order` has two values:

| Value | Rule |
|---|---|
| `left_right` (default) | The exact canonical Racket program: split objects by the midpoint of the first/last top rows, then order both groups left-to-right. |
| `match_top_left_color` | Preserve the canonical upper order, bind the top-left object's observed color, and put the unique lower object of that color before the other lower object. |

The default source is read from the selected canonical ledger and returned
byte-for-byte. The alternative performs one guarded replacement of the
canonical lower-row binding. Both rules are total on the admitted grammar.

The alternative has a genuine sequential dependency: operation A selects the
top-left upper object and binds its color; operation B uses that intermediate
to order the lower pair. Replacing A with the top-right object changes the
intermediate color and reverses the lower pair.

## Constructive grammar

- Exact integer seeds `0..2**63-1`; booleans and floats are rejected.
- Independent requests: 2–6 demonstrations and 1–4 queries.
- Every input contains four separated, exact-3×3-extent 8-connected objects:
  two upper and two lower objects under the canonical first/last midpoint.
- The two upper colors are distinct. Each occurs exactly once in the lower
  pair, so the alternative has a unique partner.
- The first mandatory demo places the cue-color partner on the left and makes
  the cue color numerically larger. The second places it on the right and
  makes the cue color numerically smaller. Together they reject literal
  spatial order, unconditional reversal, numeric-color order, and top-right
  cue variants.
- Demonstration and query streams are independent and prefix-stable. Inputs do
  not depend on the selected setting.
- Four-query support uses 15×19, 21×25, 26×28, and 30×30 scenes. The 30×30
  case places substantive objects in all four quadrants and touches every
  board edge.

## Labels and public projection

`generate` executes every label through `RacketBridge` and requires the
protected Racket backend. `public_turn` uses the shared canonical serializer,
showing demonstrations and one masked query only; it exposes no setting, seed,
program, future query, or query answer.

`native.py --out DIR --seed 17 --demos 3` writes private four-query episodes
and exact-byte, SHA-256-named first-turn public challenges.

## Focused verification

From the outer packet directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/b98cdd1751a7/tests/test_generator_b98cdd1751a7.py \
  generators/b98cdd1751a7/tests/test_native_parametric.py

python3 review.py run python3 \
  generators/b98cdd1751a7/workspace/parametric/native.py \
  --seed 17 --demos 3 --out ../checks/b98cdd1751a7/examples

python3 WORK/check_public_exports.py \
  WORK/checks/b98cdd1751a7/examples/public --demos 3 --queries 1
```

A finite self-audit and native qualification bind the exact current sources;
they do not establish universal identifiability, measured learning benefit,
owner acceptance, or training admission.
