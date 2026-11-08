# Demonstration recolor-copy diagnostic

This optional reviewer prototype detects a narrow shortcut in a native ARC
lesson: a query input is exactly one demonstration input under a bijective
color substitution, with background color 0 fixed. It predicts by recoloring
that demonstration's output. It uses only the supplied JSON and Python's
standard library; it imports no generator, canonical data, solver, or reference
runtime. It is separate from the selected and shared source trees.

## Run

From `WORK/checks/tooling/demo-copy`:

```bash
python3 -B -m unittest -v test_demo_copy.py
python3 -B demo_copy.py witnesses.json
python3 -B demo_copy.py /path/to/native-lesson.json
python3 -B demo_copy.py /path/to/native-lesson.json --out /path/to/new-report.json
```

Use `-` as the input path, or omit it, to read stdin. The JSON must be one native
lesson object or a list of lessons. Each lesson has nonempty `train` and `test`
lists. Train pairs require integer-grid `input` and `output`; test pairs require
`input`, with optional `output`. Grids must be nonempty, rectangular, and contain
integer colors 0..9; bool values are rejected. No output directory is created.
An existing `--out` path is never overwritten.

Exit 0 means a diagnostic was produced, regardless of matches or agreements.
Exit 2 means invalid input or a file error. Reports do not admit or reject data.

## Interpret the JSON

- `input_match_count` counts matching demonstration inputs.
- Every match retains its demonstration index and witnessed color map.
- `prediction_count` counts predictions that can be safely formed.
- A demonstration output containing a nonzero color absent from its input has
  `prediction_status: "unmapped_output_colors"`, a null prediction, and null
  agreement. The tool does not invent the missing color mapping.
- Missing query labels produce `label_status: "unscored"`, null per-match
  agreement, and null `actual_agreement_count`. Available predictions remain
  visible, but their correctness is not asserted.
- Present labels are compared directly with each available prediction. A count
  of zero can mean no matching input, no available prediction, or actual
  disagreement; consult the other fields to distinguish these cases.
- All candidate demonstrations are retained, including conflicting predictions.

Identity tasks and legitimate recoloring tasks can match and agree. Even a
correct copying prediction is only evidence for reviewer inspection, not proof
of a generator defect. A missing match excludes only exact input recoloring;
it does not exclude translated, rotated, cropped, approximate, or other
shortcuts, and does not establish generalization. The tool checks no lesson
identifiability or reference correctness. It does not execute supplied code.

## Retained reproduction

`witnesses.json` is a two-lesson list, extracted without modification from:

1. `WORK/checks/distribution-before.json`, `copy_rival.witness.instance`.
2. `WORK/checks/distribution-after.json`, `copy_rival.witness.instance`.

These witness outputs were labelled by the selected Python mirror in the task
distribution probe. The diagnostic's observed agreement is therefore agreement
with the supplied label, not independent Racket verification.

`witness-results.json` records **one matching demonstration, one available
prediction, and one actual agreement for the before witness**. The after
witness has **zero input matches and zero available predictions**. This is a
two-witness reproduction, not a rerun of the 60-episode distribution panel.

`tests.log` retains the test-first red run against a placeholder (9 tests,
12 failed assertions including subtests, no test errors), followed by the green
run (all 9 tests pass). The tests cover correct and wrong labels, geometric
mismatch, inconsistent/nonbijective mappings, background preservation, unknown
output colors, unlabelled queries, legitimate matches, multiple candidates,
and malformed grids. `commands.json` records the exact commands and evidence.

This is an optional local prototype. It has not been integrated into shared
tools or made an automatic quality gate.
