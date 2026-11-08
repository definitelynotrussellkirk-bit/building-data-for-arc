# Proposed `blocker_policy` parameter

This task-local prototype preserves the canonical generator, reference program,
object grouping, midpoint alignment, bounding-box geometry and cyan bridges.
One policy is fixed for every demonstration and query in an episode:

- `same_color`: canonical/default; a third box blocks a bridge only when its
  color matches the endpoint boxes.
- `any_color`: proposed alternative; any intersecting third box blocks it.

Inputs come from the canonical generator. Every retained label is executed by
the exact materialized Racket program. The default builds both settings with
**two demonstrations and four distinct queries each**. Queries differ from one
another and from all demonstration inputs.

## Run from an extracted review packet

From the outer directory containing `review.py`:

```bash
python3 review.py setup
python3 review.py run python3 generators/cfadc43e5098/workspace/parametric/prototype.py \
  --seed 17 --demo-count 2 --query-count 4 \
  --out ../checks/parametric/four-query-export
```

Choose a new output directory for each run. Existing targets, including empty
directories, are refused before any artifact is written. Python dependencies are
those of the packet; focused tests also require pytest.

`--demo-count` and `--query-count` are independent: each supports 1 through 16,
with a combined maximum of 24. A request such as `--demo-count 1 --query-count 4`
uses the same visible demonstration set for all four queries. The generator
searches at most 5,000 candidate inputs; exhaustion raises an error instead of
returning duplicates or silently reducing the requested count.

## Public export contract in version 1.1.0

Share only the `public/` directory. Each file contains exactly `train` and `test`:
demonstration inputs/outputs and query inputs. Its exact UTF-8 bytes are produced
by `reviewer_support.public_challenge_bytes`, including the final newline, and
its filename is `episode-<full SHA-256 of those bytes>.json`.

All public payloads are prepared before writing. Duplicate visible payloads are
rejected before creating the output directory, and public files are written in
sorted public-ID order. Changing the private setting, seed, program metadata,
query answers, cached projection, or settings iteration order while preserving
visible content cannot change the public filenames or bytes. Parameter values
and query labels remain private. The metadata-bearing `public_challenge()`
Python return value remains available for callers; those metadata fields are
not serialized into model-visible files.

`private/` retains complete labeled episodes and the exact two Racket programs.
`report.json` and `manifest.json` are controller evidence, not public prompts.
Manifest entries hash the exact written files. The batch is separate from
existing dataset identities.

## Identifiability and label checks

The analyzer executes both bounded policy settings. Only demonstration outputs
select surviving settings. Each query is ambiguous exactly when surviving
settings disagree on its answer; multiple surviving settings that predict the
same answer are acceptable. Private query labels are checked against the
selected exact Racket program, separately from selecting survivors. Corrupted
labels produce `invalid_labels`; they cannot create a successful receipt.
Duplicate query inputs, including matches to demonstrations, produce
`invalid_episode`.

These checks cover the two declared policy settings. They do not establish
identifiability against every possible puzzle rule, performance on ARC, or
approval of a new production/training variant.

## Focused tests and retained examples

```bash
python3 review.py run python3 -m pytest -q \
  generators/cfadc43e5098/tests/test_parametric_blocker_policy.py \
  generators/cfadc43e5098/tests/test_public_export_revision.py
```

`rules/` contains the exact unchanged proposed programs. The checked-in
`examples/seed-17/` and `evidence/reviewer-reported/` predate version 1.1.0 and
retain the old export format; treat them as historical evidence. The current
`evidence/manifest.json` binds version 1.1.0 to `evidence/private/export-v1.1.0.json`,
which contains both complete private episodes and their recorded Racket verdicts.
The return retains the exact fresh public/private batch under
`checks/parametric/four-query-export/`. Use the command above to reproduce it. This remains a **proposed prototype**, with
canonical rule approval and trajectory admission unchanged.
