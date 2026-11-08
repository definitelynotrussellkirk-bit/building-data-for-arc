# Uniform rows and longest uniform bands

Native parametric proposal for `2a5919c40197`. The production generator and its
canonical rule are unchanged. Qualification is reviewer evidence; acceptance
on the integrated exact source remains an owner operation.

| Private episode setting | Transformation |
| --- | --- |
| `mode=all_uniform` (default) | Every fully uniform row becomes gray (`5`); every mixed row becomes black (`0`). `canonical.rkt` is the exact selected canonical source. |
| `mode=longest_uniform_run` | Discover maximal consecutive bands of uniform rows, ignoring the colors of adjacent rows. Keep all bands with maximum length in gray; paint all other rows black. Retain all ties. |

The alternative requires an input-dependent intermediate: row-uniformity flags
and maximal band intervals/lengths. Only then can the rule select the globally
longest bands. A wrong-intermediate witness replaces each positive run length
with one while preserving the selection stage; this changes the final output.

## Generate and check

From the packet's outer directory containing `review.py`, using its passing
Python interpreter (the delivered check used `WORK/.venv/bin/python`):

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/2a5919c40197/workspace/parametric/audit.py \
  --out ../checks/2a5919c40197/new-self-review
```

This is a reusable bounded authoring tool: it executes labels and declared
shortcut rivals through protected Racket, records source hashes and actual
counterexamples, checks the public projection, and saves two four-query examples.
Choose a new output directory each time. Its public challenge files are
controller-side collections of masked queries; `next_turn` exposes just the
current query to the model. The first turn matches single-query evaluation.

Focused contract and semantic tests:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/2a5919c40197/tests/test_parametric_2a5919c40197.py
```

Native qualification, after building a current source inventory:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  2a5919c40197 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/2a5919c40197/new-qualification --summary
```

`adapter.generate(seed, settings, demos, queries)` returns complete `train`,
`test`, and `program_solution`. Its Python labels are claims, independently
re-executed by the native worker. `adapter.program(settings)` returns a complete
`rule!` expression for both modes. The native promotion contract supports
**2–6 demonstrations** and **1–4 queries** independently; ordinary qualification
uses three demonstrations and four queries. Seeds are exact integers in
`0..2**63-1`, matching the native parametric API.

## Teaching and diversity

The first demonstration has tied length-two bands and a losing singleton. The
second has a unique length-four or length-five winner, a shorter band, and a
singleton. Together they distinguish both settings and reject the simple rule
“keep bands above a fixed threshold, or keep all uniform rows if none qualify.”
A losing band in the second example occupies 3/10 or 4/12 of its grid height,
more than a winning band's 2/7 share in the first. This also rejects any fixed
fraction-of-height cutoff; a protected pre-repair witness records the concrete
20% shortcut that otherwise matched the old demos and changed 180 query cells.
A 3×3 canonical-scale demonstration is added at count three. Four independent
queries have sizes 3×3, 17×12, 24×23, and 30×30.

Uniform rows span their full width. Mixed rows include late interior changes,
last-column changes, alternating patterns, splits, and random textures. Winning
bands change color internally, while one shorter band can repeat a single
color, distinguishing uniformity bands from monochrome components. Run order,
spacing, palettes, top/bottom contacts, and unique/tied query winners vary with
the seed. Large queries contain substantive bands and distractors across the
canvas. Inputs are identical across settings for matched requests. Demo/query
prefixes remain stable when either count changes, and all inputs are distinct.

The semantic validator admits rectangular exact-integer ARC grids with each
dimension 3–30; both rules also handle all-uniform and all-mixed inputs. The
sampler is deliberately narrower: it constructs informative mixed/uniform
scenes at the documented profiles. It does not claim uniform sampling over
every admitted grid, arbitrary shape overrides, or rotations into a different
column-based rule. The canonical generator retains its original 3–18 bounds.

## Evidence and limits

The return includes the current native `evidence/manifest.json`, protected
qualification/execution, causal witness/replay, focused test log, and bounded
audit results under `WORK/checks/2a5919c40197/`. The inventory uses existing native
helpers. No approval hash is rewritten by this prototype.

The self-review covers its explicitly named rivals and exercised seeds/counts.
It establishes neither universal uniqueness nor measured model-learning gains.
Native owner acceptance and downstream training admission remain separate.
