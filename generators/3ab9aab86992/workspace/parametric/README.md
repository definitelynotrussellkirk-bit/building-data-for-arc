# Corner basis — proposed parametric prototype

This task supports one small semantic parameter, `corner_basis`, with bounded
values `occupied` and `missing`.

- `occupied` is the original/default behavior and uses the byte-exact canonical
  Racket program. The occupied vertex of each tiny L selects the output corner.
- `missing` changes only that semantic choice. The absent cell in the tiny L's
  2×2 bounding box selects the output corner, which is diagonally opposite.

Both settings retain the original reasoning structure: find monochrome L
triominoes, classify orientation, map each orientation to a corner, and draw a
same-color enlarged border L. This is a task-local **prototype**, separate from
production `generator.py`; it does not change canonical authority, `RULE_HASH`,
or approval.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 generators/3ab9aab86992/workspace/parametric/prototype.py \
  --out ../checks/parametric/corner-basis-seeds-0-7 --seeds 8
python3 review.py run python3 -m arcpuzzles check 3ab9aab86992 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

The evidence output directory must not already exist. The wrapper activates the
included offline Racket runtime and runs the payload from `WORK/repo/`.

## Episode and teaching contract

`choose_corner_basis(seed)` selects one hidden setting once per episode. All
three demonstrations and the query use that exact Racket program. Input streams
are independent of the setting. The bounded prototype requests exactly one L
component from the selected generator for each pair; therefore `occupied` and
`missing` disagree on every retained input, each demonstration refutes the
other declared setting, and all four possible query rotations remain
identifiable against that two-setting rival set.

The one-object restriction is deliberate evidence scope, not a proposed
production distribution. With multiple objects and repeated colors, symmetric
assignments can make both settings produce the same output. Such pairs are
lawful but cannot by themselves identify this parameter, so a future production
API would need an episode-level distinction check or resampling policy.

## Evidence and confidentiality

`private/racket-executions.json` stores exact Racket text, program hashes,
runtime receipts, inputs, and outputs. `private/episodes.json` stores complete
labeled episodes. Public episode files contain only demonstration inputs and
outputs plus an unlabeled query; they omit the seed, hidden parameter, program,
and query answer. `report.json` binds source hashes, canonical agreement,
parameter draws, pair distinction, and production/all-rotation results.

This finite census checks only the declared `occupied`/`missing` rival over the
retained seeds. It is not a proof of uniqueness against arbitrary programs and
is not approval of the proposed alternative.
