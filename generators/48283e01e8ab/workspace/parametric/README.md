# Connectivity rule prototype — unapproved

This task-local prototype varies **connectivity ∈ {4, 8}** once per episode.
The original/default rule setting is **4**. Connectivity 8 additionally joins
color-6 cells that touch diagonally. The proposal is separate from the selected
canonical generator and has no production registration or approval.

## What stays invariant

Find components of color 6, count their cells, inspect the bounding dimensions
for three-cell straightness, and recolor every cell of each component in place.
The output dimensions and every non-6 cell are preserved. The complete color
table is unchanged:

| Component | Output color |
|---|---:|
| 6 cells | 5 |
| 5 cells | 3 |
| 4 cells | 8 |
| 3 cells, all in one row or one column | 2 |
| Other 3-cell component | 4 |
| 2 cells | 9 |
| Any other size | 6 |

“Straight” retains the canonical axis-aligned definition. A diagonal three-cell
chain is therefore one non-straight component under connectivity 8 and becomes
color 4; under connectivity 4 its isolated cells stay 6.

`materialize_program(4)` returns the exact canonical ledger text, including its
whitespace. The alternative changes one BFS neighbor-list expression by appending
the four diagonal neighbors. It refuses unexpected canonical source structure.
The materialized files retain the `(rule! (lambda (g) ...))` form. `RacketLabeler`
uses the included public `RacketBridge` to execute that exact lambda body; it
does not compute labels with a Python mirror.

## Input and lesson contract

The executed transformation accepts rectangular 1–30 by 1–30 integer ARC grids
with colors 0–9. Emitted episodes additionally pass the selected canonical
generator's `self_check`. Their background is 7 and their target color is 6.
No input constraint, layout stream, size, or foreign-color draw depends on the
chosen connectivity.

The bounded sampler uses six task-local scene templates, random dihedral
transforms, band-dependent padding, and five random preserved colors in the
foreign-cell template. Easy grids are 9×9, medium grids 9×10, and hard grids
10×10. Each template contains a meaningful diagonal contact: separated objects
are merged at connectivity 8, changing the size-based recoloring. Every emitted
scene is checked against the current canonical input validator.

Every episode has **three demonstrations and one query**. Demonstrations are a
seeded permutation of all-class, preserved-foreign-cell, and unknown-size scenes.
The query is drawn from the domino, straight-three, or bent-three contact scenes.
Every pair separates the two parameter settings. The checker nevertheless
executes both Racket programs and records the exact refuting demonstration
indices for production and all four leave-one-out query choices.

`generate_episode(seed)` chooses connectivity once from a tagged deterministic
seed stream. Passing `connectivity=4` or `connectivity=8` forces a controlled
comparison while retaining identical input draws for the same seed and band.
`materialize_program()` and `RacketLabeler.apply(grid)` default to the original
setting, 4. Each function uses local randomness and leaves Python's global
random state alone.

## Exact runnable commands

From the **outer packet directory**, with the packet environment activated:

```bash
. WORK/.venv/bin/activate
python3 review.py run python3 generators/48283e01e8ab/workspace/parametric/connectivity.py --out ../checks/parametric/final --seeds 0 1 17 83 --difficulties easy medium hard
python3 review.py run python3 -m pytest generators/48283e01e8ab/tests/test_parametric_connectivity.py -q -rA
```

The wrapper selects the included offline Racket runtime and runs its payload
from `WORK/repo/`. Use a fresh `--out` directory for every evidence run; an
existing directory is rejected. The equivalent payload can run through
`python3 run_with_racket.py` from `WORK/`. Required dependencies are Python 3.12+,
the included repository runtime and its NumPy/Pillow dependencies, Racket, and
pytest for the focused tests. No external checkout or network is required.

## Retained evidence

The command explicitly exercises both settings for each seed and difficulty:
24 complete episodes, each with three demonstrations and one query. The report
counts all 24 production lessons and 96 holdouts separately; it also records
unique inputs so paired parameter settings are not mistaken for new inputs.

| File in the evidence directory | Contents |
|---|---|
| `connectivity_4.rkt`, `connectivity_8.rkt` | Exact executed rule text, one file per setting |
| `canonical_equivalence.json` | Every usable canonical labeled occurrence, actual default-Racket output, exact comparison and validator result |
| `separating_witnesses.json` | Six lawful inputs and actual outputs under both settings |
| `episodes_private.jsonl` | Parameters, seeds, profiles, complete pairs including query answers, and program identities |
| `challenges_public.jsonl` | Only demonstration input/output pairs and query inputs |
| `report.json` | Source/rule/runtime hashes, sample policy, counts, parameter-rival refutations, commands and limitations |
| `files.json` | File sizes and SHA-256 values for the other evidence files |

Rows in the public and private JSONL files correspond by row order. Only the
public file is a challenge handoff. It contains no hidden parameter, seed,
reference program, query answer, or other metadata. Public projection also
copies the grids so editing a challenge does not mutate its private episode.

The authoring report checks that prototype, canonical program, and selected
generator source remain unchanged throughout the run. Running it again after a
canonical repair produces new evidence bound to the new generator bytes.

## Scope and limitations

This is an **unapproved prototype**, not a new canonical rule authority or a
production parametric API. Exact default equivalence follows from retaining the
canonical lambda; the canonical-pair checks separately document empirical
agreement. Alternative-setting evidence is bounded to the declared seeds,
bands, and scene templates.

Identifiability is claimed only against the declared parameter rivals
`connectivity=4` and `connectivity=8`. It does not establish unique inference
against arbitrary color tables, shape-class rules, or memorization of the six
templates. The contact-heavy sampler deliberately makes the nearby rule change
visible; it is not offered as a representative sampler of all lawful grids.
Canonical repair tests and canonical lesson contracts remain separate.
