# Diagonal components with an episode-fixed gap policy

This opt-in native prototype extends task `59a7762bc6da`. Its default is the
exact canonical Racket program. The alternative repairs one-cell diagonal gaps
before applying the original component rule. Neither setting changes the
canonical generator or grants production acceptance or training admission.

## Rule and causal dependency

Inputs contain gray `5` on orange `7`. The original rule finds 8-connected gray
components and recolors a whole component cyan `8` exactly when it contains a
consecutive straight diagonal run of at least three cells, in either slope.

| Episode parameter | Behavior |
| --- | --- |
| `gap_policy="keep"` | Apply the exact original program, leaving gaps untouched. |
| `gap_policy="bridge_once"` | Simultaneously fill an orange cell gray when its two immediate opposite diagonal neighbors are gray in the original input, then apply the original program to the filled grid. |

The alternative is simultaneous, not iterative: newly inserted cells do not
trigger another insertion. The parameter is fixed for all demonstrations and
queries. Inputs and their ordering are sampled independently of it.

**A** derives the bridge cells from the original input. Its **intermediate** is
the filled grid, including newly joined gray components. **B** recomputes
8-connectivity and diagonal runs on that grid, then recolors qualifying whole
components. A bridge can join two pieces, create a qualifying run, and cause
an attached off-diagonal branch to change color. Thus B's object membership
and qualification cannot be obtained from the original grid alone.

The native causal witness compares the qualified `bridge_once` program with
the exact canonical program as a `skip_a` counterfactual. The retained recipe,
witness and replay live in `checks/59a7762bc6da/` in the review return. They
verify final labels; the interpretation of the intermediate remains a
reviewer argument for the owner to assess.

## Constructive lessons and sampling

`adapter.py` exports `program(settings)` and
`generate(seed, settings, demos, queries)`. Seeds are exact integers in
`0..2**63-1`, demonstrations are independently selectable in `2..6`, and
queries in `1..4`. Ordinary examples and qualification request three
demonstrations and four queries. Invalid values, including booleans passed
as counts, are rejected. Calls do not change the global Python RNG.

The first two demonstrations carry complementary evidence:

| Demo | Required contrasts |
| --- | --- |
| First | A broken diagonal with an orthogonal tail; an intact diagonal of the other slope with a branch; a dense two-row negative; an orthogonal gap that must remain unfilled. |
| Second | A broken diagonal of the opposite slope; an intact diagonal longer than three; a bent diagonal near miss; a gap pattern distinguishing one simultaneous pass from iterative closure. |

The cascade contrast starts with gray cells at local coordinates
`(0,2), (2,0), (3,3)`. A single pass inserts `(1,1)` but leaves `(2,2)` orange.
Consequently the last gray cell remains unchanged. Iterating the gap fill
would incorrectly insert `(2,2)` and join that cell to the cyan component.

Sampler dimensions range independently from 16 through 30 in each direction.
Every scene uses separated regions containing positive and negative motifs;
larger grids contain additional substantive motifs throughout the canvas.
Boundary placement, branches, dense negatives, gaps and both slopes remain
represented. The 30-by-30 examples are not padded small puzzles.

Dimensions for six potential demonstrations and four potential queries are
distinct within an episode. Geometry uses independent streams by seed, split
and index. This makes query novelty constructive and keeps prefixes stable:
requesting more demonstrations does not change existing demonstrations or
queries, and requesting more queries does not change the first query.

`sample_input(seed, split, index, height=..., width=...)` permits explicit
size stress within the same bounds. `bridge_once` and `transform` support
the semantic grid domain of rectangular 1..30 grids containing only 5 and 7;
they also permit minimal witness grids outside the scene sampler's size range.

## Private evidence and one-query projection

The audit retains private programs, settings, seeds, answers and teaching
checks. Its public challenge files contain demonstration input/output pairs
and exactly one query input. Filenames are SHA256 digests of only these public
bytes, produced through `reviewer_support.public_challenge_bytes` and
`public_challenge_id`. Private settings, query answers, ordering metadata and
future query inputs never enter a public view.

The four views are controller-side assets, with their order in a private map.
The existing consumer should select one view for each turn; do not expose the
directory listing or the private map. The first view is byte-identical to a
single-query request. This prototype does not implement a turn controller.

## Reproduction

Run these commands from the outer review extraction. Payload paths resolve
from `WORK/repo`, and `../checks` refers to `WORK/checks`.

```sh
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/59a7762bc6da/tests/test_native_parametric.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/59a7762bc6da/workspace/parametric/audit.py \
  --out generators/59a7762bc6da/workspace/parametric/evidence/current

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  59a7762bc6da --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/59a7762bc6da/qualification --summary
```

The audit uses the same-checkout protected Racket runtime for labels and finite
rivals. A failed or malformed rival execution is an audit failure, not a
refutation. Demo-only rival elimination establishes the tested distinctions;
it does not establish universal uniqueness. The native inventory binds the
source, tests and retained evidence. The owner must requalify and accept the
exact integrated bytes before this family can be called accepted.
