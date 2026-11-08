# Finite-rival lesson gate

This task-local gate checks whether supplied demonstrations eliminate the
selected generator's declared `LESSON_COMPETITORS` before each query. It reads
already labeled episodes from an official `arcpuzzles generate`/`apply` workflow.
It does **not** run Racket, reexecute the reference rule, independently verify
labels, approve a source, or establish uniqueness beyond the finite declared
rival set. Retain the upstream Racket labeling receipt with the input file.

The implementation uses only Python's standard library and the packet's
`reviewer_support` helper. `find_root(__file__)` binds it to its own repository
or copied runtime; `load_selected_generator` loads the exact selected source
and records its SHA-256. It neither modifies that source nor adds shared tools.

## Exact command from WORK

After retaining labeled production episodes at
`WORK/checks/lesson-gate/production-four-query.jsonl` and their actual upstream
generation/apply receipt at `WORK/checks/lesson-gate/upstream-receipt.json`:

```bash
python3 run_with_racket.py python3 generators/8b6a2892a064/workspace/lesson_gate/gate.py --task-id 8b6a2892a064 --input ../checks/lesson-gate/production-four-query.jsonl --upstream-receipt ../checks/lesson-gate/upstream-receipt.json --expect-demos 3 --expect-queries 4 --out ../checks/lesson-gate/production-four-query-gate.json
```

The output path must be new. Replace the two input paths with the actual
retained production paths; do not manufacture a receipt. The wrapper selects
the packet's local import environment; this gate itself starts no Racket
process. The receipt file is required, content-hashed, and identified in the
result; its contents and its relationship to the supplied labels are **not
independently verified** by this gate.

For a deliberately ambiguous witness, pass its labeled episode and actual
upstream apply receipt to the same command and choose a distinct output path.
Ambiguity writes a complete result and exits 1. In this family, demonstrations
containing only `six_long` scenes can leave `skip_short_lines` consistent; a
query with short lines can expose the unresolved distinction. The actual
recorded outputs must still come from upstream Racket execution.

## Scoring and failure behavior

1. Read a JSON episode object, a nonempty JSON array of episodes, or JSONL with
   one episode per nonempty line. Repeating `--input` processes multiple files.
   Every episode must have nonempty `train` and `test` lists, with valid ARC
   integer grids in **both** `input` and `output` for every pair.
2. Reject duplicate inputs anywhere within an episode, including duplicates
   across demonstrations and queries. Reject missing labels, empty pair lists,
   malformed grids, mismatched task IDs, and unavailable/invalid competitor
   declarations. Validate the optional expected counts exactly.
3. Execute every declared competitor on every demonstration. Record all
   refuting demonstration indices and prediction hashes. Freeze the names that
   agree with every demonstration. No query label enters this selection.
4. Execute only these frozen survivors on each query. A query is ambiguous
   when any survivor disagrees with its supplied label. A surviving rival that
   agrees with one query can still make another query ambiguous. Previously
   eliminated rivals are not reevaluated on queries.

No default demonstration or query count is imposed: actual `train`/`test`
lengths drive the check. `--expect-demos` and `--expect-queries` are optional
positive integers that catch an upstream short batch when exact counts were
requested. Repeating `--upstream-receipt` retains multiple receipt identities.
Duplicates across independent episodes are not prohibited by this gate.

Competitors receive deep copies. A competitor exception, malformed prediction,
or observed input mutation is an error, not an eliminated rival or a passing
lesson. The caller's original episode remains unchanged.

| Exit | Meaning |
|---:|---|
| 0 | Every supplied query passes the finite declared-rival teaching check. |
| 1 | At least one query is ambiguous; the result identifies the surviving rivals. |
| 2 | Invalid arguments, malformed/missing evidence, invalid source declarations, or competitor failure. |

Errors print structured JSON on stderr and do not write a partial successful
report. Pass/ambiguity reports contain the exact generator and gate source
hashes, raw input-file and upstream-receipt hashes, actual counts, labeled-pair
hashes, demonstration evidence, and each query's ambiguous rivals and refuting
demo indices. Indices are zero-based. All reports state `labels_reexecuted:
false`; a finite-rival pass is not a correctness certificate for supplied labels.

## Tests and scope

Run from `WORK/`:

```bash
python3 run_with_racket.py python3 generators/8b6a2892a064/tests/test_lesson_gate.py -v
```

The nine focused standard-library tests cover demonstration elimination,
surviving rivals that agree/disagree on different queries, query-label
independence of survivor selection, missing labels, exact counts, duplicate
inputs, malformed grids, nonmutation, JSON/JSONL preservation, and CLI exits
0/1/2 with source/input/receipt hashes. Test rivals and tiny test labels are
explicit synthetic fixtures; these tests make no Racket execution claim.

Tests resolve task workspaces through the copied runtime's source manifest and
reviewer helpers, with a task-only fallback for running the pure tests without
a full runtime. Keep upstream production/apply results and this gate's result
together as private authoring evidence.
