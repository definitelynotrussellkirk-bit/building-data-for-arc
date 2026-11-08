# Reflection and join: proposed parametric prototype

This is an **unapproved prototype** for `d89cff1052a2`, originally
`training:4c4377d9`. It does not replace the selected generator, change the
canonical Racket authority, add a production parameter API, or grant training
admission. The code uses the repository's included protected Racket executor for
every example output and every parameter-rival prediction. There is no Python
transformation used as a label fallback.

## Parameters and unchanged reasoning

Choose both values once per episode. Every demonstration and query then uses
that same exact program. The solver still reflects the entire input and joins
the reflection to the original; direction and the ordering of the two copies
are the only changes to the reasoning.

| Parameter | Allowed values | Default | Meaning |
|---|---|---|---|
| `axis` | `vertical`, `horizontal` | `vertical` | Vertical reflection and vertical joining, or horizontal reflection and horizontal joining |
| `order` | `reflected_first`, `original_first` | `reflected_first` | Which copy is first: top for a vertical join, left for a horizontal join |

The exact four executable Racket programs are:

| Setting | Program |
|---|---|
| `vertical__reflected_first` | `(rule! (vconcat (flip-ud g) g))` |
| `vertical__original_first` | `(rule! (vconcat g (flip-ud g)))` |
| `horizontal__reflected_first` | `(rule! (hconcat (flip-lr g) g))` |
| `horizontal__original_first` | `(rule! (hconcat g (flip-lr g)))` |

The first program preserves the selected canonical program **byte for byte**.
Evidence generation checks its full SHA-256 against the selected canonical
ledger and executes it on all five labelled canonical pairs, including the
vertically symmetric query. Symmetric inputs remain lawful; they can make the
two order settings answer-equivalent for that particular input.

## Input and output bounds

Inputs are rectangular integer grids with colours in `0..9`. Each contains
exactly 2–4 colours, with every colour appearing at least twice.

| Setting axis | Input height | Input width | Output shape | Maximum output |
|---|---:|---:|---|---|
| `vertical` | 3–15 | 3–30 | `2H × W` | 30 × 30 |
| `horizontal` | 3–30 | 3–15 | `H × 2W` | 30 × 30 |

Ordinary complete episodes share the same input support for all four settings.
They contain three small demonstrations (`3×4`, `4×7`, `6×5`) and a larger
`15×15` query. These four distinct shapes also prevent duplicate-input removal
from dropping a demonstration. The same seed gives identical inputs under every
setting, so every parameter rival is executable on every pair without exceeding
the size bounds. The query output reaches side length 30. Separate probes cover
the full axis-specific input boundary (`15×30` or `30×15`), each producing a
`30×30` output.

Ordinary draws are asymmetric on both axes, with colours and cell arrangements
varying by seed. Each pair therefore distinguishes the two order settings, and
output shape distinguishes the axis settings. Holding out any one pair still
leaves three distinguishing demonstrations. This is checked using all three
other Racket programs, not inferred only from a sampler flag.

## Run it

Use Python 3.12+ and the packet's included Racket runtime. The bridge requires
NumPy and Pillow; the tests additionally require pytest. The prototype itself
has no additional third-party dependencies. The wrapper establishes all local
runtime import paths and fails if real Racket cannot run.

From the packet's `WORK/` directory, use the same absolute interpreter path for
the wrapper and payload. The examples assume the provided `.venv` is prepared.
An absolute path is needed because the payload runs from `WORK/repo/`:

```bash
REVIEW_PYTHON="$(pwd)/.venv/bin/python"
"$REVIEW_PYTHON" run_with_racket.py "$REVIEW_PYTHON" \
  generators/d89cff1052a2/workspace/parametric/prototype.py evidence \
  --seeds 0 17 20261022 --out ../checks/parametric/replay
```

The absolute-path form above is the portable command used by the retained
execution receipts. Output directories must be new; reruns refuse to overwrite
earlier evidence. The command returns 0 only when canonical agreement, all four
settings, all query rotations, boundary probes, and the negative diagnostic
checks meet their stated conditions. Runtime failures remain failures, and an
early exception leaves an `incomplete` receipt when materialization has begun.

To materialize one fixed setting:

```bash
"$REVIEW_PYTHON" run_with_racket.py "$REVIEW_PYTHON" \
  generators/d89cff1052a2/workspace/parametric/prototype.py episode \
  --seed 17 --axis horizontal --order original_first \
  --out ../checks/parametric/one-episode
```

Omitting `--axis` and `--order` selects the canonical default. To choose the
episode's setting deterministically from its seed, use `--sample-parameters`
instead of either fixed parameter option. Parameter selection and input draws
use independent SHA-256-derived local RNG streams. No global random state is
used, and no rule parameter is resampled per pair.

Run the focused prototype tests from `WORK/`:

```bash
"$REVIEW_PYTHON" run_with_racket.py "$REVIEW_PYTHON" -m pytest -q \
  generators/d89cff1052a2/tests/test_parametric.py
```

These are prototype checks. The generator's pre-existing canonical tests and
the canonical review battery remain separate.

## Retained output and public isolation

`evidence` writes a compact authoring bundle:

- `report.json`: source and program hashes, executable/runtime identity, seed
  list, exact payload command and working directory, canonical replay,
  distinguishing input, boundary pairs, evidence paths, counts and limitations.
- `private/programs/*.rkt`: exact program bytes for all four settings.
- `private/episodes/*.json`: complete labelled episodes, fixed parameters, seed,
  exact Racket source and program hash.
- `private/audits/*.json`: rival status for the production split and every
  single-pair query rotation, linked to episode and program hashes.
- `private/diagnostics/*.json`: two deliberately ambiguous labelled fixtures
  and their rejected audit results.
- `public/episode-NNNN.json`: only `train` input/output pairs and `test` inputs.

Only the `public/` directory is intended for a solver. Public files omit hidden
parameter values, seed metadata, programs, source hashes, private query outputs,
and audit conclusions. Their neutral filenames do not name the chosen setting.
Public serialization uses an explicit field whitelist and independent copies.
Everything else in the authoring bundle must stay private.

Hash conventions are explicit. `json_hash_algorithm` defines the compact,
sorted-key UTF-8 JSON representation used by `public_sha256`, `episode_sha256`,
`audit_sha256`, input/output hashes, and diagnostic `sha256`. These content hashes
are independent of saved JSON whitespace. The separate `file_sha256` values
hash the exact pretty-printed JSON file bytes, including the final newline.
Source-file and Racket-program hashes also refer to exact file bytes.

The surrounding `checks/parametric/` directory also retains actual wrapper
commands, effective working directories, return codes and stdout/stderr logs.
Its final `evidence/` report is bound to the source bytes that were actually
executed. Earlier red-test and intermediate receipts are diagnostic history;
they do not override the final source-bound result.

## A reusable finite-rival lesson checker

`racket_episode.py` accepts arbitrary fully labelled episodes and a map of
candidate names to exact executable `(rule! ...)` programs. It has no knowledge
of this family's sampler, parameter names, or intended transformation. Authors
can import it from this directory and call:

```python
from racket_episode import RacketOracle, score_episode

with RacketOracle() as oracle:
    audit = score_episode(
        labelled_episode,
        {"reference": reference_program, "rival": rival_program},
        "reference",
        oracle=oracle,
    )
```

The scorer first re-executes the reference on every supplied label. A wrong
label or a candidate execution failure produces `status: error`. It then
classifies each rival:

| Rival result | Interpretation |
|---|---|
| `refuted_by_demonstrations` | At least one visible demonstration disproves the rival |
| `ambiguous_query` | The rival fits every demonstration but differs on a query |
| `survived_all` | The rival agrees on every supplied answer; no different query answer has been demonstrated |
| `execution_error` | The rival could not be evaluated; this is an error, not a successful refutation |

`parameters_identified` is stricter than absence of query ambiguity: it requires
every declared rival to be refuted by the demonstrations. Both results are
recorded for the original split and for all single-pair holdouts.

The two negative fixtures have three inputs symmetric about both axes, followed
by an asymmetric query. For a fixed axis, the two order settings fit all three
demonstrations but disagree on the query. The scorer must report
`ambiguous_query`, retain the exact differing prediction, and identify the same
problem when that query position is held out. These are authored diagnostic
counterexamples, **not failed solve attempts** or failures of ordinary generated
episodes. They illustrate why checking a transformation on individual pairs
does not establish that its demonstrations identify the requested query rule.

## Limits

The checks cover finite seeds and the four declared parameter settings. They do
not prove identifiability against every possible program or demonstrate model
mastery. The ordinary sampler intentionally avoids symmetric inputs to teach
order; diagnostics and canonical replay cover symmetry separately. Large queries
test dimension generalization within this simple reflection-and-join family;
they do not introduce sequential state, contextual gating, or new composition.

The helper reuses the included `ArcExecutor` rule loader and private grid
application adapter. It requires pure, deterministic candidate programs and is
serial. Caching stores actual Racket results under the program and input hashes;
it is not a substitute evaluator. Moving this helper into a shared supported
interface would require a separate reviewed change.
