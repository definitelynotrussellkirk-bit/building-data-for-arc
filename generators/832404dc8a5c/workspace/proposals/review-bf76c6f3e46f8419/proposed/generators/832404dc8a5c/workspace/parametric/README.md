# Endpoint threshold — proposed prototype

This task-local prototype extends original task `d2acf2cb` with one hidden,
episode-wide parameter, `endpoint_threshold ∈ {1, 2}`. The default **2** uses
the canonical Racket source byte for byte. The alternative **1** activates a
row or column with at least one boundary 4 marker. Both settings swap `0↔8`
and `6↔7` once on the union of active lanes. Markers and nonlane cells stay
unchanged. No production generator, runtime interface, canonical authority, or
approval is changed by this proposal.

The input grammar deliberately adds single boundary markers alongside complete
paired lanes. Both settings use the same input distribution: a dense 0/6 field,
complete paired interior lanes, single markers at noncorner boundary positions,
and 7/8 confined to complete lanes. Grid dimensions remain inside 6..13 by
8..12. This grammar extension is necessary to make the threshold observable;
the canonical inputs alone contain only complete pairs and cannot distinguish
the two settings. At default 2, the single marker is ignored and its incomplete
lane stays unchanged unless it crosses a complete active lane.

Each deterministic episode has three demonstrations and one query. The first
demonstration has complete and incomplete rows with inverse swaps; the second
has complete and incomplete columns with forward swaps; the third and query
mix rows and columns. All settings share the same seeded input draws. A separate
seeded stream selects the parameter once when `--endpoint-threshold sample`
is used. Every retained demonstration distinguishes 1 from 2, including both
row and column roles, and every single-pair query rotation is checked against
the two declared parameter rivals.

## Exact commands

From the extracted packet's outer directory, using its prepared environment:

```bash
review_python="$(pwd)/WORK/.venv/bin/python"
"$review_python" review.py run "$review_python" generators/832404dc8a5c/workspace/parametric/prototype.py evidence --out ../checks/parametric/evidence
```

The absolute payload interpreter path accounts for the wrapper's directory
change. The retained run used this exact command:

```bash
/workspace/scratch/3931e20c94d7/arc_review/WORK/.venv/bin/python review.py run /workspace/scratch/3931e20c94d7/arc_review/WORK/.venv/bin/python generators/832404dc8a5c/workspace/parametric/prototype.py evidence --out ../checks/parametric/evidence
```

From `WORK/`, a portable equivalent is:

```bash
review_python="$(pwd)/.venv/bin/python"
"$review_python" run_with_racket.py "$review_python" generators/832404dc8a5c/workspace/parametric/prototype.py episode --seed 23 --endpoint-threshold sample
```

`python3 run_with_racket.py python3 ...` also works when the selected interpreter
is available on `PATH` and has the required installed dependencies.

The `episode` command prints only public challenge JSON: train input/output
pairs and a query input. `--private-out PATH` separately retains the hidden
parameter, exact program, hashes, query answer, rival outputs, and rotations.
The `evidence` command refuses an existing destination to preserve earlier
receipts; use a fresh directory when rerunning it.

## Evidence and limits

`WORK/checks/parametric/evidence/report.json` binds the source hashes, exact
commands, runtime details, seeds, program hashes, 4/4 canonical parity, two
complete episodes, and an exact distinguishing witness. `private/programs/`
contains exact materialized Racket text for both settings; `private/` retains
all labels, checks, and different-cell coordinates. `public/` contains only
challenge JSON and omits seed, parameter, source, and query answer.

All outputs and alternative predictions come from the included live
`RacketBridge`, not a Python rule mirror. The bridge removes only the outer
`rule!` registration marker, then applies the unchanged grid lambda. The test
file `tests/test_parametric_endpoint_threshold.py` checks default parity,
single row/column activation, a crossing swapping once, unchanged nonlanes,
deterministic episodes, parameter inference, public redaction, and strict
parameter validation. These tests cover the prototype separately from any
canonical repair tests.

The bounded evidence tests only the declared parameter rivals 1 and 2 and the
retained seeds/profiles. It does not prove identifiability against every
possible competing rule, exhaust the input space, or approve the extension.
