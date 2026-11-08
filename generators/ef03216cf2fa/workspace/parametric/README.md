# Orient, measure, rank, and stack

This opt-in native adapter preserves the exact canonical `ranking=perimeter`
program. Its alternative, `ranking=normalized_top_edge`, sorts by the number of
occupied cells in each crop's top row **after** clockwise rotation of tall
crops. Both settings use descending score, original row-major ties, left-aligned
vertical stacking, and one blank separator row. Settings stay fixed per lesson.

## Design and checks

The alternative changes one existing decision: which object measurement supplies
the ranking. A geometric chain of stack anchors was considered, but it would
introduce additional positioning conventions and a larger output-width bound.
Here orientation changes the measured edge, which can reverse the ordering of
two objects. The causal ablation ranks the unrotated edge but displays the same
normalized crops, isolating the intermediate measurement's effect on order.

The implementation plan follows the packet's existing native contract: implement
the rule and deterministic sampler against independent literal regressions;
execute chosen labels and demo-only rivals in Racket; check public projection;
build the source inventory; qualify the native adapter; retain a protected
counterfactual witness and return the delta for owner acceptance.

`prototype.py` supplies `program(settings)`, `generate(seed, settings, demos,
queries)`, and finite-rival programs. `adapter.py` loads that exact adjacent
module. `check.py` is the reusable protected-Racket check/export tool. The
canonical generator, selected authority, and approval records are unchanged.

## Supported grammar

- Exact integer seeds in `0..2**63-1`; independently requested 2–6 demos and
  1–4 queries. Ordinary qualification uses 3 demos and 4 queries.
- Distinct nonzero colors identify separated same-color four-connected objects;
  bounding boxes do not overlap. Shapes include sparse crosses, corner-Ls,
  frames, combs, and dense bridges. Split top edges separate count from span.
- The same seed/count request produces identical inputs under both settings.
  A bounded search of at most 48 candidates chooses two demonstrations jointly
  refuting 16 declared rivals for each setting. Queries play no part in that
  selection; failure is explicit, never a shortened lesson.
- Four query profiles: 10×12 with 3 objects, 16×20 with 4, 24×25 with 5, and
  30×30 with 6. Large objects are spread across six slots and contact opposite
  borders. Normalized object heights are at most four, so output height is at
  most 29. Canonical production remains at its original 10–14 size limits.
- The first query is identical for a one-query and four-query request. Additional
  demonstrations do not alter query inputs. Input profiles vary shape, density,
  palette, position, ties, and tall versus wide orientation across seeds.

## Run from the packet's outer folder

```sh
WORK/.venv/bin/python review.py run python3 \
  generators/ef03216cf2fa/workspace/parametric/check.py \
  --out ../checks/ef03216cf2fa/focused --seed 0 --seed 17 --demos 3

WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/ef03216cf2fa/tests/test_parametric.py \
  generators/ef03216cf2fa/tests/test_parametric_literal.py \
  generators/ef03216cf2fa/tests/test_parametric_public.py -q
```

Choose a fresh output directory. The check tool verifies Python claims against
executed protected Racket, stores exact private programs and labeled episodes,
and checks demonstration-only rejection of every listed rival within two demos.
It writes one-query visible projections using the shared public-byte helper.

Give the consumer one public challenge at a time, after the preceding answer.
The four-query episode and all settings, programs, and answers remain private.
Each projection has the original demos and only its selected query, without
ordinals, total-count hints, or future inputs. Filenames hash exactly the visible
bytes. This tool does not implement a turn controller or training loop.

## Admission and limits

The native source inventory and returned `qualification.json`/`execution.json`
are reviewer evidence. Owner integration must freshly qualify and accept the
exact live source. No training admission is granted. Native qualification checks
the two parameter settings; the task-local check additionally attacks 16 finite
shortcuts. These checks do not establish universal rule uniqueness or measured
learning benefit. Unrelated canonical batteries are outside this prototype scope.
