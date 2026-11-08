# Passive shortcut teaching coverage

This standalone diagnostic counts actual labelled counterexamples to every
`CANONICAL_SHORTCUTS` declaration recorded in a public
`arcpuzzles-lesson-census-v1` JSON or JSON.gz. It reports each shortcut in each
complete lesson, plus aggregate minima and gaps. Rival names are discovered
from the evidence and checked against the exact generator declaration; there
is no built-in list of puzzle-specific rivals.

The added criterion is teaching coverage: every declared shortcut should be
contradicted by at least one demonstration. A `survived_all` status, including
a shortcut that also answers the current query correctly, receives **zero
teaching credit** when all demonstrations agree with it.

For one-query rotations, the tool also counts contradictions across the
entire window. With four demonstrations and one query, at least **two
refuting pairs among the five** are necessary and sufficient to leave at
least one demonstration refutation regardless of which single pair becomes
the query. The report records all five resulting demonstration counts. It
does not confuse an answer-correct current query with evidence that teaches
why the shortcut fails.

## Run

These commands use the packet root as the current directory. Python 3.10+
and the exact source tree bound to the saved census are required; the CLI
itself uses only the standard library.

```sh
.venv/bin/python WORK/checks/tooling/shortcut_coverage/shortcut_coverage.py \
  WORK/checks/final/lesson-census.json.gz \
  --root WORK/repo \
  --out WORK/checks/tooling/shortcut_coverage/new-final-result.json
```

For historical evidence with an explicitly saved, exactly matching generator:

```sh
.venv/bin/python WORK/checks/tooling/shortcut_coverage/shortcut_coverage.py \
  WORK/checks/schedule-census.json \
  --root WORK/repo \
  --generator WORK/checks/intermediate-source/v3-initial/generator.py \
  --out WORK/checks/tooling/shortcut_coverage/new-archived-result.json
```

The `--root` argument accepts a library checkout or the corresponding portable
runtime. `--generator` selects explicitly supplied historical generator bytes;
all other files still must match the saved manifest. It does not waive source
validation. Omit `--out` to print full JSON; output files must be new and are
never overwritten by the diagnostic.

| Exit | Meaning |
| --- | --- |
| 0 | All evaluated declarations meet both coverage criteria, or the evidence declares no canonical shortcuts (reported separately). |
| 1 | Complete scored evidence contains a demonstration or rotation coverage gap. |
| 2 | Blocked source/schema check, incomplete labelled evidence, prediction error, or disagreement with saved rival outcomes. |

An approval consumer must require `status == "coverage_complete"`, a nonempty
inventory, and the intended lesson count; exit 0 alone is insufficient.
`no_canonical_shortcuts` means this criterion was not assessed, not that an
undeclared hypothesis inventory passed.

## Evidence and source checks

The available census schema saves labelled instances and aggregate rival
statuses, but not the per-pair predictions needed to count refutations. The
CLI therefore recomputes only declared shortcut outputs against the saved
Racket-labelled outputs. It never samples new instances, invokes `generate`,
runs Racket, executes the puzzle tests, or edits the source tree.

Before loading shortcut code it verifies the embedded runtime manifest hash
and every listed file hash, including the selected generator. Current source
is loaded through public `reviewer_support.load_selected_generator`. An
explicit archive is compiled from its exact, verified bytes using the same
verified local dependencies; no replacement source tree is fabricated. The
generator hash, declared rule hash and shortcut inventory must match the
census. The generator is checked again after scoring. A stale source blocks
the run instead of reinterpreting old evidence with current code.

Saved instance hashes and accepted input hashes, when present, are checked.
Every scored lesson needs materialized demonstration outputs and exactly one
labelled query. A malformed or missing label is incomplete evidence.
Predictions run on independent copies of inputs. A shortcut exception or
invalid output is reported as unknown, with no refutation credit; it cannot
produce a passing overall result. Saved rival outcomes are compared with
recomputed outcomes as an additional consistency check.

Loading a generator executes its module body, as the public helper normally
does. Run this tool only on the authorized, trusted review packet. This is a
passive diagnostic of its public evidence, not an isolated code sandbox.

## Measured ordinary evidence

The delivered results below are ordinary saved census evidence, rescored
against matching source. Both verified all **254 manifest-listed files**.

| Result | Lessons | Declared shortcuts | Shortcut/lesson rows | Demo gaps | Rotation gaps | Errors or outcome mismatches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `final-lesson-result.json` | 300/300 | 5 | 1,500 | 0 | 0 | 0 |
| `archived-schedule-result.json` | 15/15 | 5 | 75 | 0 | 0 | 0 |

Both runs returned `coverage_complete` and exit 0. The minimum refutation
counts were the same in both runs:

| Actual declaration | Minimum among demonstrations | Minimum across all five pairs |
| --- | ---: | ---: |
| `bbox_area_neighbor` | 1 | 2 |
| `first_neighbor` | 1 | 2 |
| `largest_neighbor` | 3 | 4 |
| `last_neighbor` | 1 | 2 |
| `unmasked_bbox` | 1 | 2 |

The final generator SHA-256 is
`4b188d05f3c1b39b65cc288a07b39bef527b623df6a759f6facde2cda9cab75b`.
The exact archived generator SHA-256 is
`94cac27c1c440c14ece7957892b7a99a0b49b62f78cbc38e6feafba3dd444760`.
The saved rule source identity for both is
`5af80c67d3907183931a179f7ff8ad18fc3c41ab97c1030589b0a4649a5ca7c7`.
This last identity is retained from the original census; the diagnostic does
not claim to have rerun the reference.

`stale-source-guard-result.json` retains an intentional blocked run: giving
the archived census the current generator without `--generator` exits 2
and reports the exact hash mismatch before rescoring.

## Explicit synthetic demonstration

`fixtures/synthetic_windows.json` contains four tiny counting examples. Their
reference is identity on a one-cell grid; the rival always predicts zero.
The all-zero window does not expose the rival's error, even though a one-cell
input containing 1 does. This makes the distinction between current support
equivalence and demonstrated teaching failure directly inspectable.

```sh
.venv/bin/python WORK/checks/tooling/shortcut_coverage/synthetic_demo.py \
  --out WORK/checks/tooling/shortcut_coverage/new-synthetic-result.json
```

| Synthetic five-pair values | Demo refutations | Full-window refutations | Current query matches | Every single holdout covered |
| --- | ---: | ---: | --- | --- |
| 0, 0, 0, 0, 0 | 0 | 0 | Yes | No |
| 0, 0, 0, 0, 1 | 0 | 1 | No | No |
| 1, 0, 0, 0, 0 | 1 | 1 | Yes | No |
| 1, 2, 0, 0, 0 | 2 | 2 | Yes | Yes |

The saved `synthetic-result.json` is labelled synthetic and is not passed
off as a native census or source-compatible generation result. Its expected
exit is 1 because three windows have rotation gaps. The focused tests also
exercise a synthetic saved `survived_all` status and require a coverage gap;
that fixture is tested through the pure counting core, not the source-bound
CLI loader.

## Focused verification and receipts

```sh
.venv/bin/python -m pytest -q WORK/checks/tooling/shortcut_coverage/tests
```

The 12 focused tests cover 0/1/2 refutations, every single query holdout,
query-correct surviving shortcuts, exceptions, input mutation isolation,
dynamic declaration discovery, gzip, changed source bytes, instance
corruption, missing query labels and inventory mismatch. The initial test
run failed because the implementation was not yet present; that actual
failure is retained along with the subsequent passing run.

`receipts/index.json` indexes exact commands, working directories, exit
codes and stdout/stderr logs. All evidence paths in those receipts are
relative to `WORK`. `record_command.py` is a small local receipt helper;
give each invocation a fresh receipt label.

## Interpretation limits

This adds a measurable candidate gate: require a positive demonstration
refutation count for every declared canonical shortcut and at least two
full-window refutations when claiming single-query rotation robustness.
It evaluates the declared candidate inventory and materialized windows
only. It cannot establish completeness of that inventory, canonical fit of
a newly declared rival, coverage of unsampled generator behavior, or improved
Qwen9 performance. Those are separate questions. In particular, a passing
result here measures teaching evidence against these five rivals; it is not
a language-model quality measurement.
