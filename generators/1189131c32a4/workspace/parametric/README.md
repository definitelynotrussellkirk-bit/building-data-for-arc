# Proposed frequency-ring parameter family — 1189131c32a4

This directory is a **task-local, unapproved prototype**. It does not change the
selected production generator, approve any variant, or admit data to training.
The canonical rule remains the authority for task `1189131c32a4`.

## Parameters

The hidden settings are selected once per episode and remain fixed for every
demonstration and query.

| Parameter | Values | Original/default | Effect |
| --- | --- | --- | --- |
| `frequency_order` | `most_outside`, `least_outside` | `most_outside` | Places the highest- or lowest-frequency non-7 color on the outside ring. |
| `tie_break` | `descending_numeric`, `ascending_numeric` | `descending_numeric` | Orders equal-frequency colors by decreasing or increasing color number. |

All four Cartesian settings preserve the original reasoning structure: ignore
background 7, count every other color globally, rank those colors, then paint one
concentric square ring per ranked color. With `n` colors the output is still a
`(2n-1) x (2n-1)` square. Geometry and component placement remain irrelevant.

`program(DEFAULT_SETTINGS)` is byte-for-byte equal to the selected canonical
Racket program. The prototype pins both authorities and fails closed on drift:

- canonical program SHA-256:
  `cb24e365264238c0be9d5cd2e869bbb19a300270ad43bf90ddef138a66986722`
- selected generator SHA-256:
  `563d9029027d65a06a2c7c01716171eb39685c7284cdb16d6024f6181cb74c8d`

The other three programs replace only the guarded color-ranking expression.

## Setting-neutral input grammar

The prototype reuses the selected generator rather than forking its sampler. It
requests its `hard` `tie_two_way` and `tie_three_way` profiles, alternating them
through a deterministic, bounded retry schedule. These inputs have:

- dimensions in the selected generator's hard range (normally 10..14 per side),
- modal background 7,
- exactly four non-7 colors from `1,2,3,4,5,6,8,9`,
- one compact component per foreground color,
- counts `[2,2,4,6]` or `[3,3,3,6]` in seeded color order.

The input schedule is generated without consulting the hidden setting. For a
fixed seed and requested counts, every setting receives identical inputs in the
same order. Demonstration and query schedules occupy separate index regions, so
changing either requested count does not perturb the other's prefix. A bounded
64-attempt retry per slot rejects invalid, duplicate, or non-distinguishing
inputs; exhaustion raises instead of returning a partial episode.

This is intentionally narrower than the full canonical grammar. In particular,
it does not sample color 0, 2/3/5/6-color lessons, scattered components, or the
four exact public inputs. Those remain covered by the selected canonical
generator, not claimed by this prototype sampler.

## Demonstration-only identifiability

Every sampled input contains both an unequal frequency and a numeric tie. Thus:

- reversing `frequency_order` changes which frequency class occupies the outer
  and inner rings;
- reversing `tie_break` changes the relative rings of tied colors.

Consequently each retained demonstration distinguishes all four declared
settings. `fit_settings` is passed demonstrations only, so its survivor
certificate does not inspect query inputs or query labels. The focused tests
also require every query to have four distinct candidate outputs.
This is finite identifiability within the four declared programs, not a proof
against every imaginable shortcut.

The adapter supports **2..8 demonstrations** and **1..8 queries** independently.
The normal evidence example uses three demonstrations and four distinct queries.

## Label and evidence boundary

`generate_episode`/`adapter.generate` return an authoring record containing
train and test labels. It is not a public challenge: do not expose its test
outputs to a solver. Promotion qualification re-executes every claimed label
through protected Racket and owns public/private projection if the family is
ever accepted.

The task-local verifier independently executes all four exact Racket programs on
all generated demonstration and query inputs, compares each result with the
Python diagnostic mirror, checks the selected labels, fits candidates using only
demonstrations, and verifies four-way-distinct query predictions. It additionally
runs the exact default program on every labelled canonical pair. The Python
mirror is a check, not approval authority.

## Run retained evidence

From the outer packet directory, where `review.py` lives:

```bash
python3 review.py run python3 \
  generators/1189131c32a4/workspace/parametric/prototype.py \
  --seed 17 --all-settings --demos 3 --queries 4 \
  --out ../checks/parametric-frequency-rings
```

Choose a new output directory for a replay; a nonempty destination is refused.
The command writes one private episode per setting plus `summary.json`. For this
configuration it executes 4 settings x 7 pairs x 4 candidate programs = 112
variant applications, then checks the four labelled canonical pairs under the
exact default program.

Run focused tests through the same supported environment:

```bash
python3 review.py run python3 -m pytest -q \
  generators/1189131c32a4/tests/test_parametric_frequency_rings.py
```

The focused tests cover exact canonical bytes, all four distinct programs,
matched setting-neutral inputs, distinct demonstration/query prefixes,
demonstration-only identification, independent count prefixes, all canonical
pairs in Racket, every retained label under every candidate Racket program, and
invalid seed/count/setting rejection.

## Promotion files

`adapter.py` is a thin exact-adjacent loader exposing `program(settings)` and
`generate(seed, settings, demos, queries)`. `promotion.json` declares the four
settings and bounded counts. These files make the prototype reviewable by the
native qualification worker; they do not themselves qualify or accept it.
