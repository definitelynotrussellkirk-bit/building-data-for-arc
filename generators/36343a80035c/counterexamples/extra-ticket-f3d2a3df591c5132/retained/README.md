# Extra random ticket: 36343a80035c

**Built and tested a repair for a native lesson ambiguity.** The proposed
generator is v3.1.1. It is kept here as a separately reviewable patch because
this user-requested ticket is outside the packet's immutable three-target
assignment. The original return and assignment remain intact.

## Finding

The rule paints 8 on zero regions enclosed by nonzero walls, using cardinal
connectivity. The wrong rule instead paints every zero component of area at
most four, without checking whether it touches the border.

At **seed 17, hard difficulty**, the native command with its **automatic four
demonstrations and four queries** emits an underidentified lesson. The rival
fits all four demos and differs on all four queries. The native declared hook
and every previously registered rival pass. On the first query, the rival
incorrectly paints the zero at **[0, 0]** cyan. `native-default.jsonl` is the
exact native export; `native-audit.json` re-executes all labels and the rival
through protected Racket and confirms that the new gate detects this lesson.

The initial 12-lesson probe used three demos and one query. It found no
ordinary first-query ambiguity, six rotated ambiguities, and one lesson where
the rival survived all four pairs. The focused four-query follow-up exposed
the failure. This sequence is retained honestly: it was not a target reroll or
a claim that border examples were universally absent. Many original draws
already have a small border region.

## Repair

After embedding, if an input lacks a small border-connected zero region, add
two walls beside an empty physical corner. The remaining corner zero is a
singleton exterior component and must stay zero. The existing empty corner
of every base motif supplies a safe location under every D4 transform and zero
padding. The mutation leaves the enclosed cells, exact profile areas, palette,
and dimensions unchanged. It is applied after embedding so the new region
stays on the physical border.

The proposal also registers the size-only rival and its witness, preserves the
broad input grammar, bumps the version, and adds regression tests. **The version
bump changes keyed RNG seeds:** unchanged-answer claims concern direct mutation
of a frozen input, not equal-seed outputs compared across versions.

## What ran

| Check | Actual result |
| --- | --- |
| Random draw | One uniform target from 497 unused IDs; seed journal, pool, source and sampler hashes retained; replay returns the same target |
| New core regressions against baseline | Two expected failures, retained in `regression-red.xml` |
| Fixed before/after probe | Four fixed seeds × three bands × four inputs; after repair all 48 examples refute the new rival; zero grammar/mirror errors |
| Native default lesson | Four demos/four queries, no native rejections; all four query ambiguities reproduced in protected Racket |
| Frozen-input mutation | Seven original inputs re-executed in Racket; all answers preserved and rival refuted |
| Staged task tests | 75 passed: 15 existing tests and 60 new checks, with no parent repository source on PYTHONPATH |
| Focused geometry | 768 cases: all D4 codes, four profiles, three shape indices, eight padding/offset cases; 396 mutations, 372 no-ops, zero failures |
| Independent review | No functional blocker; one version-related test comment corrected |

The staged test receipt and log are in `delivery-verification/`. Earlier
verification receipts remain as executed history, including the comment-only
revision and the subsequently added native four-demo regression. No full
generator battery, native parametric qualification, or training experiment was
run for this bounded peer proposal.

## Apply and replay

`proposal.patch` contains five task-local files. `proposal-inventory.json`
binds their original and proposed hashes. The complete proposed files are in
`proposal/generators/36343a80035c/` for inspection. A maintainer can run
`git apply --check PATH/TO/proposal.patch` from the owner repository before
choosing whether to apply it. The packet's native source patch still contains
only its original three tasks; this extra patch is not automatically applied.

From this packet's outer root, use a new output path for each replay:

```bash
WORK/.venv/bin/python WORK/checks/additional-ticket-001/draw_one_ticket.py --work WORK
WORK/.venv/bin/python review.py run python3 \
  ../checks/additional-ticket-001/border_probe.py \
  --source ../checks/additional-ticket-001/proposal/generators/36343a80035c/generator.py \
  --out ../checks/additional-ticket-001/replay-after.json
WORK/.venv/bin/python review.py run python3 \
  ../checks/additional-ticket-001/verify_proposal.py \
  --out ../checks/additional-ticket-001/replay-verification
```

`ordered_lesson.py`, `native_lesson_audit.py`, and `corner_geometry_check.py`
reproduce the other bounded checks. They require the packet's normal Python
dependencies; the Racket checks use its verified protected runtime.

## Disposition and limits

**Reviewer-tested proposal; owner integration and acceptance pending.** Retain
the finding and proposed repair with task 36343a80035c. The native export's
inherited reviewed-safe label records the old catalog state; the now-known
underidentified lesson is alternative-answer research evidence, not a clean
single-answer training example. No approval metadata was edited and no
training admission is claimed.

This repairs one finite, executable rival. The generator still samples two
small holes from a finite motif family. The geometry check is bounded to its
listed factors, one canonical palette and one corner RNG seed; the 48 exact
axis tests separately cover all three palettes at the declared dimension
endpoints. Neither check proves arbitrary-program uniqueness or measured
learning benefit.
