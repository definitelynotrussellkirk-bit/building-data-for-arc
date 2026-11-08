# Historical P1: color priority within one row survives the teaching lesson

This evidence retains an actual failure of generator version 3.0.0 at SHA-256
`a3e21d4ea25700280832635bb9af391686399b3b7926cc8944f16d7ee6ae4d14`.
It does not claim that a later selected generator has the same defect.

The rival uses the canonical connected-component template, bounding-box anchor,
clipping, and stamping behavior, but orders singleton markers by
`(row, -color, column)`. It fits all four canonical pairs. With default seed 0,
medium difficulty, and start 23, it also fits demonstrations 23, 24, and 25,
but changes query 26 at zero-based cell `(3, 4)` from canonical color 5 to 3.

The fixed historical witness places its two same-row markers in descending
color order. Its evidence cannot distinguish that tie breaker from row-major
ordering. The historical `lesson_identifiable` hook returns `[]` for this lesson
because the additional rival was absent from its finite declaration inventory.

## Contents and provenance

- `prior_generator.py`: exact captured historical selected source.
- `source_identity.json`: original path, version, rule identity, and source hash.
- `captured_inputs.json`: inputs captured before the selected source was edited.
- `reproduce.py`: independent flood fill and rival, replay of captured source,
  canonical fitting checks, and fresh public `Catalog.apply` Racket execution.
- `racket_apply.json`: unmodified public API result from the retained reference run.
- `lesson.json`: full four-pair lesson, authoritative outputs, rival outputs,
  differences, hashes, and canonical rival-fit evidence.
- `summary.json`: bounded failure result.
- `commands.json` and command logs: actual command, working directory, outcome,
  and the meaning of the deliberately nonzero reproduction exit code.

`input_generator_sha256` always identifies the captured historical source.
`reference_runtime_generator_sha256` identifies the selected generator copied
by the public reference API at the time of its call. The latter may be newer;
the reproducer executes only the captured generator to recreate inputs. Labels
come from the unchanged canonical Racket rule `c3118b3e9e62`, whose text SHA-256
is `97956adc1e0ffa6b5119dd32ae21c67264b86a3119f2cbdc179e98c6ed31f232`.

## Replay

From the outer review packet directory, using the packet's supported Python and
Racket environment:

```sh
python3 review.py run python3 -B ../checks/review-p1/reproduce.py
```

The expected exit code is **1**, accompanied by
`"status": "teaching_defect_reproduced"`. It means the historical three matching
demonstrations and one differing query were reproduced. Exit 2 reports a source,
evidence, or reference-runtime problem and is not evidence of this defect.

The first retention run uses `--record`; it refuses existing evidence files.
Normal replay compares fresh Racket labels against the retained full lesson.
The finding is bounded to this source and lesson. It is not a lesson census or
a claim of universal identifiability.

## Bounded resolution verification

The intermediate repaired source SHA-256 tested in this directory is
`50210d202b830b2e8726ed0f28ab905d0a465512b9297fccf16bef55b116ffa2`.
`resolution_check.json`, `resolution_racket_apply.json`, and `resolution.log`
retain five freshly labeled reference inputs from that source: the same four
default sample indices 23–26 and the fixed n=4, size-4 witness at seed 138,
sample index 1, medium difficulty, height 7, width 9.

The historical rival now agrees with those four default pairs in the pattern
`[false, true, false, false]`. Both witness demonstrations refute it, while the
query still distinguishes its prediction from Racket. Every one-pair query
holdout retains a refuting demonstration. The fixed composite witness refutes
all 19 declared canonical-fitting rivals against its independently executed
Racket output. The bounded check exited 0.

`verify_resolution.py` is the exact one-time recording script used for that
check, preserved for source provenance. It refuses existing output paths.
Use `reproduce.py` for repeatable historical-defect replay. The final generator's
task tests and census, retained elsewhere by the repair author, provide broader
checks; this directory's resolution result covers only the population above.

The repair author subsequently added entry validation for seed and sample-index
types and negative sample indices, reporting final source SHA-256
`616644a1bffebb2adc85789f699373fa3be15ca499b99137fc2547f41f17b631`.
That validation change does not alter the recorded valid integer calls. The
reference receipts here still bind the actually executed intermediate source,
not the later final hash. Final-source battery, control, witness, and census
evidence belongs to the repair author's separate runs.
