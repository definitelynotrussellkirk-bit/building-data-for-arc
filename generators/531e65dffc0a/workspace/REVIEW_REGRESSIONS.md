# Focused review regressions

## Final v2.1 candidate

The final source SHA-256 is
`704565e2cac3d04a427b95e0550d6461d948626144a5eb9598968a60554d1e58`.
The full task suite produced **104 passed in 1.76 seconds**, exit 0, with
`--import-mode=importlib`. The exact command, working directory, exit code,
source hash, and test hashes are retained in
`checks/regressions-v21/pytest.txt` and `checks/regressions-v21/run.json`.
The primary reviewer handles the official task-test stage and fresh-packet
replay separately. Every earlier 101-pass result below is intermediate.

## Test contracts

`../tests/test_review_regressions.py` checks the selected generator in both
the library and the portable runtime. It uses `reviewer_support.find_root`
and `canonical_pairs`, and reads exact override values directly from pixels.
The tests require one monochrome 4-connected prototype, isolated rotation
anchors, valid ARC integer cells, canonical-input acceptance, strict controls,
determinism, fresh returns, and exact requested counts on a small canvas.
Lawful shapes with an empty top-left bounding-box cell are accepted.

`../tests/test_review_semantics.py` independently normalizes and rotates shape
coordinates, reproduces all three public outputs, verifies that declared
canonical shortcuts fit every public pair, and checks the declared teaching
schedule against those shortcuts. It also independently constructs all twelve
single-code mapping rivals by recoding an input anchor and applying the
independent transform. Every teaching scene must defeat those twelve rivals.
At each of four starting positions, all four choices of query within a
four-pair window must contain no surviving rival that disagrees on the query.

## Retained baseline and intermediate results

Before repair, source SHA-256
`1e23bb1c7e683034cf28ac6c354b9b3e8a9f43ef3310d8244a82d08fbb1c03bb`
produced **62 failed, 8 passed**. Library and relocated portable runs agreed.
The retained packet-level logs are `checks/regressions-before/pytest.txt`,
`checks/regressions-before/portable-pytest.txt`, and
`checks/regressions-before/portable-run.json`.

After the color-control and semantic contract was settled, the expanded suite
produced **87 failed, 14 passed** against the same baseline bytes. Its library
and relocated portable logs are `checks/regressions-before/expanded-pytest.txt`
and `checks/regressions-before/expanded-portable-pytest.txt`; source/test hashes
are in `checks/regressions-before/expanded-portable-run.json`.

The first integration run against v2 produced **3 failed, 98 passed**, retained
in `checks/regressions-intermediate/`. Those failures came from a test requiring
an unagreed public `rule_mirror` API. Removing that assertion retained the
independent expected-output comparison against every declared rival. The
intermediate suite produced **101 passed** in both the library and the official
portable runtime against the intermediate source SHA-256
`ba5017212fbecd2853c5bdeb8a1a0638d73a6ce68a6888fc2d1473628ac8e1bf`.
Logs and command/cwd/exit/hash receipts are in `checks/regressions-after/`.
The portable run started from `/tmp` with `PYTHONPATH` and `PYTHONHOME` removed.
An earlier launcher attempt disabled the user site and could not import pytest;
its error is retained separately as `launch-error.txt` and `launch-error.json`.

The next intermediate source changed only prototype-color axis metadata to the
existing checker's `color` type and pipe-delimited domain. Its SHA-256 was
`3d5acb565e4eb85a561c32a3a507d0a7f6f09e690eebc22fceef1951d7d2837d`.
After expanding the lesson-window regression to make each of the four pairs
the query in turn, the intermediate task suite produced **101 passed**, exit 0.
`checks/regressions-final/pytest.txt` and `checks/regressions-final/run.json`
retain that intermediate command, working directory, exit code, and hashes.
The intermediate portable result predates that metadata change and expanded
query-rotation test.

### Mapping defect and correction

An additional audit found that three-anchor teaching scenes omitted a rotation
code. Single-code mapping rivals could therefore survive demonstrations and
disagree on a later query. Tests added before the repair independently exposed
this defect: **6 failed, 98 passed** against source `3d5acb565e4e...`, retained
in `checks/mapping-regressions-before/`. For example, window seed 93001,
start 0, query index 1 leaves `code_2_uses_4` fitting every demonstration and
disagreeing on the query in all three difficulty bands.

The v2.1 teacher uses four distinct anchors, covering every rotation code, and
requires distinction from the six canonical shortcuts and twelve code-mapping
competitors. The final 104-pass suite confirms those independent mapping and
cyclic-window regressions. Odd draws retain canonical-profile and broad-domain
coverage; distribution rates are evaluated separately from these tests.

### Portable import correction

The earlier portable runs used pytest's default import mode. The official
task-test stage uses `--import-mode=importlib`, which exposed a sibling import
failure. The original collection error, exit 2, is reproduced in
`checks/importlib-regressions-before/`. The semantic test now loads its sibling
support file through an explicit `Path(__file__)`-anchored importlib spec, with
normal module registration. Focused runs in both default and importlib modes
then collected successfully and reached the expected unresolved mapping
failures: **6 failed, 7 passed**, retained in
`checks/importlib-regressions-fixed/`. The final v2.1 run uses importlib mode.

## Running the tests

Run explicitly from a library root:

```bash
python -m pytest -q --import-mode=importlib generators/531e65dffc0a/tests
```

In a portable runtime, copy both test files to `tests/531e65dffc0a/` and run:

```bash
python -m pytest -q --import-mode=importlib tests/531e65dffc0a
```

The independent transform checks the public rule and the declared rivals.
These tests do not certify Racket parity or canonical distribution frequency.
