# Perimeter rank direction: proposed prototype

This is a runnable, task-local **prototype** for `c78d339cf2f2`. It does not
replace the selected `generator.py`, change the canonical ledger, extend the
shared API, or approve either rule variant. Its labels are computed by the
included real Racket bridge. There is no Python rule mirror supplying labels.

## Parameter and domain

| Parameter | Allowed values | Original/default | Effect |
| --- | --- | --- | --- |
| `rank_order` | `ascending`, `descending` | `ascending` | Rank any-nonzero 4-connected components by exposed-edge perimeter in that direction, then paint ranks with 2, 3, 4. |

The default materialized program is byte-for-byte the canonical record's
`program_solution`. Its exact UTF-8 SHA-256 is
`ea2222b6763c9e504ccce7e1d84a4377a62ea86e64ed1e97bf5615d9145b0692`.
The alternate program changes exactly its perimeter comparison from `<` to
`>`. Both preserve row-major component discovery and stable ties, any-nonzero
connectivity, zero background, and the fixed rank palette. No alternate palette
is proposed.

Both settings use the same input constraints: exactly three separate nonzero
components, with at least two different perimeters in every generated pair.
Three disjoint 8x8 placement cells, separated by a zero row or column, prevent
merging. Grids have 19 through 22 rows and columns. Foreground colors are drawn
from 1, 5, 6, 7, 8, 9 and can differ within a connected component. The first
demonstration contains three area-6 shapes with perimeters 10, 12 and 14, which
distinguishes the setting immediately and separates perimeter from area. The
second shape triplet includes a hole and disagrees with area ranking. The third
includes equal perimeters to exercise stable tie behavior.

`generate_episode(seed, executor)` samples `rank_order` **once** from the seed,
then generates three demonstrations and two labeled authoring queries. All
five pairs execute the same selected program. Input draws use a separate
deterministic stream. An explicit `rank_order=` creates matched-input
counterfactuals. `materialize_program()` defaults to the canonical ascending
setting.

## Run from the outer packet directory

The packet wrapper selects the included offline Racket and sets imports. With
the packet's Python 3.12 environment and its `numpy`, `Pillow` and `pytest`
dependencies installed, these commands run from the directory containing
`review.py`:

```bash
python3 review.py setup
python3 review.py run "$PWD/WORK/.venv/bin/python" \
  generators/c78d339cf2f2/workspace/parametric/prototype.py \
  --out ../checks/parametric/reproduced --seeds 0 1 2 3 4 5 6 7
python3 review.py run "$PWD/WORK/.venv/bin/python" -m pytest -q \
  generators/c78d339cf2f2/tests/test_parametric.py
```

Choose a new `--out` directory for each run; the prototype refuses to overwrite
evidence. Seed lists must include both declared settings. The retained run uses
`WORK/checks/parametric/evidence/`; its actual wrapper command, exit code and
logs are recorded in `WORK/checks/parametric/commands.json`.

The official rule wrapper needs `scripts.comment_solutions`, while the packet
keeps that source in `shared/tools/`. The prototype temporarily maps that
package name to the included directory while wrapping programs, then restores
the process's prior modules. It uses the official normalization function and
does not modify shared files. This adaptation is local to the single-process
prototype; a shared import fix remains separate work.

The focused tests execute Racket by default. They do not skip when a dependency
or the Racket runtime is missing; missing prerequisites fail visibly. Their
coverage is the workspace prototype, independently of canonical generator
repair tests. They compare the original program with all five canonical pairs,
check mixed-color connectivity and stable ties under both settings, test
deterministic complete episodes, and detect a known ambiguous demonstration.

## Evidence and public/private boundary

Each evidence run writes:

- `public/episode-NNN.json`: only demonstration inputs/outputs and query
  inputs. No seed, hidden setting, reference, or query answer appears here.
- `authoring/episode-NNN.json`: full labeled authoring episode and executed
  rival checks. Both declared settings are evaluated on every demonstration.
- `authoring/programs/`: exact materialized Racket text and the runtime's
  wrapped callable for each setting. Their hashes are named separately.
- `authoring/bridge-receipts.json`: actual inputs, outputs, program/callable/
  application hashes and error status for every bridge evaluation.
- `authoring/counterfactual.json`: one lawful input with both executed outputs
  and the count of changed cells.
- `authoring/ambiguity-control.json`: a deliberately insufficient fragment
  with three equal-perimeter singletons. Both settings survive its rival
  check. This fragment is retained as authoring evidence and is excluded from
  generated episodes.
- `authoring/canonical-checks.json`: direct execution against all five given
  canonical input/output pairs.
- `manifest.json`: seeds, settings, exact programs, source/file hashes,
  runtime identity, actual counts and limitations. This is authoring evidence.

Only the `public/` JSON files are model-visible challenges. All other output,
including the manifest and this source workspace, is authoring material.

This finite witness constructor demonstrates a meaningful rule parameter and
the required episode discipline. It does not establish broad diversity, solve
difficulty, arbitrary-seed correctness of the selected generator, production
integration, approval, or model-training eligibility. The fixed three-shape
template vocabulary is an explicit prototype limitation.
