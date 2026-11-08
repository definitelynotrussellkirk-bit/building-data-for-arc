# Prototype-controlled stamp transform family

Native authoring adapter for `274345a1792c`. The production generator and its
selected canonical Racket rule are unchanged. This workspace is reviewer-ready
authoring evidence only; owner qualification/acceptance on integrated live bytes
and any later training admission remain separate decisions.

## Episode-fixed rule parameter

`transform_family` is private and fixed across every demonstration and query in
an episode:

| Setting | Visible controls `1..4` |
| --- | --- |
| `mixed` (default) | Exact canonical rule: identity, clockwise quarter-turn, left-right reflection, then left-right reflection followed by clockwise quarter-turn. |
| `rotations` | Identity, clockwise quarter-turn, half-turn, and three-quarter-turn. |

Both settings use identical sampled inputs for a given seed and requested
counts. The default program is copied byte-for-byte from the selected Catalog
authority. Inputs contain one connected asymmetric maroon prototype, five
magenta anchors, every control code, and a repeated code. Every output is
independently re-executed by protected Racket during native qualification.

## Required sequential dependency

**A:** discover the complete connected maroon component and normalize its exact
occupied-cell geometry. **Intermediate:** that input-dependent normalized cell
set. **B:** only after that geometry is known, transform it according to each
anchor's visible control and the episode setting, then stamp the resulting cells
cyan at that anchor.

The retained wrong-intermediate witness substitutes a fixed four-cell L for the
actual prototype while leaving the setting, controls, anchors and input fixed.
Protected Racket produces a different final query grid. Thus B cannot be chosen
from the controls alone; it consumes A's recovered geometry.

## Sampling, counts and size stress

Requests support 2–6 demonstrations and 1–4 queries independently. Stable
prefixes let a controller request one query without changing the first-turn
bytes from a four-query episode. Geometry RNG is separated from the setting, so
matched settings share exact inputs; all inputs within an episode are distinct.

The six demonstration profiles range from 13×15 to 24×24. The four queries are
30×30, 24×30, 30×24 and 27×29. The 30×30 visible input—not merely its hidden
answer—touches all four boundaries: the prototype occupies the bottom-right
3×3 box while control/anchor groups reach the top and left edges. Other anchors
and distractor spacing exercise long-range extraction and repeated application
without empty-padding a canonical scene.

## Bounded self-review

`audit.py` executes the intended rule and twelve complete Racket rival programs.
Rivals include the other setting, fixed-L intermediates, identity-only,
code-3/code-4 exchange, counterclockwise code 2, reversed code-4 composition,
hybrid code 3, partial-anchor application, once-per-code application, bounding-
box fill and anchor preservation. Candidates fit demonstrations only; query
predictions are examined only after fitting. A pass is finite evidence against
those named programs and samples, not universal rule uniqueness.

The retained review uses seeds 0 and 17, two and three demonstrations, four
queries, both settings, and 677 protected-Racket evaluations. No rival survived
all visible demonstrations in any of the eight jobs.

## Reproduce in the issued packet

Run from the outer folder containing `review.py` after `python3 review.py setup`:

```sh
python3 review.py run python3 -m pytest \
  generators/274345a1792c/tests/test_parametric.py -q

python3 review.py run python3 \
  generators/274345a1792c/workspace/parametric/audit.py \
  --seed 0 --seed 17 --demos 2 --demos 3 --queries 4 \
  --out ../checks/274345a1792c/fresh-self-audit.json

python3 review.py run python3 -m arcpuzzles parametric qualify 274345a1792c \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/274345a1792c/fresh-qualification --summary
```

Output destinations are intentionally refused when they already exist.
Regenerate the task-local manifest after any adapter, prototype, program, test or
retained-evidence change, then rerun qualification.

## Public/private boundary

`public_turn` returns all demonstrations plus exactly one selected query input.
It omits settings, programs, query answers, seeds, future queries, query counts
and turn markers. Altering those private fields does not alter the serialized
public challenge or its content hash. This helper documents and tests the
existing controller projection; it does not implement a new turn loop.
