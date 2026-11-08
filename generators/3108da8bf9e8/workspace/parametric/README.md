# Whole-block ranking with an episode-fixed statistic

This task-local prototype exposes `rank_basis=cells|components_then_cells`.
`cells` returns the exact selected canonical Racket source and retains its
11×11 input grammar. `components_then_cells` sorts by the lexicographic pair
**(number of four-connected blue components, number of blue cells)**. Both rules
move complete blocks without rotating, repainting or changing their textures.
They place the three smallest keys left to right on the bottom macro-row, then
the middle three, then the largest three on top.

The production generator, canonical authority and approval are unchanged.
This proposed family requires the owner's native exact-source acceptance;
qualification, acceptance and training admission remain different decisions.

## Input and teaching contract

Every input contains a 3×3 array of equal square blocks using colors 1 and 2.
Full zero separator bands divide the blocks. There is no outer padding or zero
inside a block. The nine blue-cell counts are distinct, making every selected
sort key unique even when several blocks have the same component count.

All demonstrations have the canonical 11×11 geometry, and the same seed yields
identical demonstration inputs under both settings. The alternate rule is
therefore taught by changed outputs on matched inputs. The default's four query
inputs remain 11×11. The alternate's queries are 14×14, 20×20, 26×26 and 30×30;
their block side lengths are 4, 6, 8 and 9. The first three use separator widths
1 and 1. The last uses separator widths 1 and 2 on each axis: nine 9×9 blocks
occupy 729 cells, so this is substantive size stress rather than padded 11×11.
Larger inputs belong only to the alternate grammar; the exact canonical rule
is intentionally not relabeled as a general-size rule.

The constructor creates six demonstrations and four queries before slicing the
requested 2–6 demonstrations and 1–4 queries. Prefixes are stable, inputs are
distinct within each episode, and every retained pair uses the same rule.
Independent deterministic RNG streams isolate each split/index/attempt. The
bounded sampler permits 4,096 attempts per pair and fails explicitly on
exhaustion; its full-bank attempt counts are retained as private authoring data.

The sampler checks a finite teaching family, including cells versus components,
four- versus eight-neighbor connectivity, stable component-only sorting,
reversed area tie-breaking, red-component ranking, reversed primary order,
identity, row or column local sorting, fixed macro-row reversal, prefix
repainting and repeated position maps. Every sampled permutation includes a
cycle of length at least four. Such a cycle cannot fit inside any independent
three-position group, excluding the source task's three-triple local-sort
class. These chosen constraints are a synthetic breadth policy, not a claim
that all conceivable wrong programs are refuted.

## Causal dependency

Step A extracts each block and computes its input-dependent component count and
cell count. The intermediate is the nine lexicographic keys and their resulting
source-index rank order. Step B uses that rank order to choose which source
block to copy into each target slot. Replacing A with cell count, eight-neighbor
components or a wrong tie-break can change the block chosen by B. The supplied
native witness/replay records execute such counterfactuals through protected
Racket; they do not rely on the Python claim mirror alone.

## Runnable entry points

From the packet's outer directory, `review.py run` runs payloads in `WORK/repo`:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/3108da8bf9e8/tests

WORK/.venv/bin/python review.py run python3 \
  generators/3108da8bf9e8/workspace/parametric/audit_native.py \
  --out ../checks/3108da8bf9e8/audit-replay

WORK/.venv/bin/python review.py run python3 \
  generators/3108da8bf9e8/workspace/parametric/make_examples.py \
  --out ../checks/3108da8bf9e8/examples-replay --seed 17 --demos 3 --queries 4
```

Use the tools' `--help` for their bounded options, and use new output directories
for new source versions. The exporter writes controller-only `public/` records
with four queries, actor-safe `turns/` records with one query and no total-count
hint, and a separate private area for answers, settings, exact programs, source
hashes and execution evidence. Only `turns/` is the model-facing sequential
surface; exposing controller payloads would reveal future queries.

`adapter.py` supplies the native `program(settings)` and
`generate(seed, settings, demos=3, queries=4)` API. Adapter labels are deterministic
Python claims; the native worker independently executes every label through
the protected Racket runtime. `audit_native.py` fits declared rivals only to
visible demonstrations, then checks whether any survivor disagrees on a query.
Racket errors fail the audit and are never counted as successful refutations.

After source and evidence are final, use the existing native inventory and
qualification commands documented in `docs/parametric-promotion.md`. The returned
qualification is evidence for owner review; this workspace does not create an
acceptance record or authorize downstream training.
