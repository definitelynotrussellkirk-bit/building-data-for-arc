# Native skyline color selection

This separate native family keeps the approved production generator and exact
canonical program unchanged. `survivor_filter=all` keeps only the topmost nonzero
cell in every column. `modal_color` first constructs that same skyline, counts
its colors, and keeps every survivor whose color is tied for the maximum count.
Zero is background, ties retain all winning colors, and an empty input stays empty.

The alternative retains the source's column selection and adds an input-derived
selection stage. Counting original-grid colors or retaining all instances of a
winning color are different transformations. This is a dependency between two
selections; it is not an iterative simulation. The separate grammar admits exact
integer grids of 1..30 rows and columns, including dense and empty grids. The
approved production support remains its reviewed 5..14 sparse-column grammar.

## Implementation and verification plan

1. Pin exact canonical bytes; test strict grammar, plurality, ties, and empty or
   dense inputs. Materialize complete Racket rules for the alternative and rivals.
2. Construct three distinguishing demonstrations and a full four-query bank;
   support 3..6 demos and 1..4 queries with independent RNG streams and prefixes.
3. Check every retained label through protected Racket, fit finite rivals to
   demonstrations before inspecting query disagreements, and repair real findings.
4. Run native manifest and qualification, replay a causal counterfactual, and
   verify single-query public previews plus negative corruption cases.

Task-local `native_family.py` owns semantics, `sampler.py` owns input geometry,
`adapter.py` joins them without runtime side effects, and `audit.py` replays
bounded teaching checks. No predecessor checkout is an executable dependency.

## Sampling and teaching

`sample_inputs(seed, demos=3, queries=4)` supports exact integer seeds
0..2**63-1, 3..6 demonstrations and 1..4 queries. It builds all six demonstration
roles and all four query roles before taking prefixes. Layout, palette and query
presentation use separate local SHA-derived RNG streams. The setting never enters
an input RNG. Returned arrays are fresh and global RNG state is untouched.

The first three demonstrations teach a 4/3/2/1 skyline plurality (below half), a
3/3/2/1 partial tie, and five singleton colors on a canonical-scale 5x5 grid.
The first contrasts cell frequency with component frequency and raw-grid color
frequency. Lower copies of a winning color show that only column tops survive.
The query bank contains one tiny input (1..3 sides), 14x18, 24x26, and 30x30 inputs.
The complete bank is shuffled before selecting a one-query prefix.

An observed stress gap was repaired without adding demonstrations: the original
30x30 draws at seeds 0,17 and 2**63-1 had equally frequent skyline colors, so both
settings produced the same answer. The sampler now changes one top color only
when every color ties in that 30x30 role. It preserves every skyline color,
geometry, lower scatter and other roles; the new stage must act on the large grid.
Retained RED tests reproduce the earlier gap. This was a coverage defect, not a
wrong-label or demo-fitting/query-conflict finding.

## Reproduce from the packet outer folder

```sh
WORK/.venv/bin/python review.py run python3 -m pytest --import-mode=importlib \
  generators/b1e6ee6856bf/tests/test_native_family.py \
  generators/b1e6ee6856bf/tests/test_native_sampler.py \
  generators/b1e6ee6856bf/tests/test_native_adapter.py -q
WORK/.venv/bin/python review.py run python3 \
  generators/b1e6ee6856bf/workspace/parametric/audit.py --out ../checks/skyline-fresh
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  b1e6ee6856bf --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/skyline-qualification-fresh --summary
```

The adapter computes deterministic Python claims; the audit and native worker
execute the exact setting programs through protected Racket. `audit.py` is a
portable task-local runner: it reads its adjacent adapter and promotion contract,
uses the declared minimum demonstration count, fits rivals only to demonstrations,
and retains any surviving query disagreements. It caches exact program/input
pairs and checks that bound source files did not change. Copying it to another
family requires that family's `native_family.rivals(settings)` interface.

Current source-bound evidence is in `evidence/manifest.json`; the return carries
`checks/b1e6ee6856bf/`. The repaired focused suite passed 99 tests, the core audit
refuted 54 finite comparisons, and the maximum-seed/count probe checked 20 labels
through protected Racket. Independent review, native qualification, causal replay
and public projection results are retained with the same return.

Each saved public preview contains the demonstrations and one query input. The
complete bundle and directory listing are controller-only. Its private manifest
keeps the random presentation permutation paired with answers; early stop after
one query has the same first-turn bytes. Public names hash only that view's bytes.

Finite rivals and sampled seeds do not prove unrestricted identifiability or
learning benefit. Dense, tiny and empty inputs belong to this native extension;
the original production grammar is unchanged. A skyline has at most one survivor
per column, so even a dense 30x30 input produces at most 30 nonzero output cells.
Reviewer readiness does not grant owner acceptance or training admission.
