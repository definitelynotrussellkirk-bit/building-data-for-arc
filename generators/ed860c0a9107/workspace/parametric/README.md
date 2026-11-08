# Overlay priority — task-local prototype

**Status: proposed prototype.** This extends the original `training:7c9b52a0`
family (`ed860c0a9107`) without changing its canonical rule, selected production
generator, runtime interfaces, or approval records.

## Parameter and invariant reasoning

| Parameter | Allowed values | Canonical/default | Meaning |
|---|---|---|---|
| `priority` | `first`, `last` | `first` | At each aligned local coordinate, return the first or last visible payload in row-major container order. |

Both settings identify the background from the top-left cell, extract separated
equal-sized non-background rectangles, align their bounding boxes, treat zero
and the background as transparent, and emit zero when no payload is visible.
Only the order used to select an overlapping visible color changes. A second
parameter is unnecessary for this bounded extension.

Input constraints are identical for the two settings and inherited from the
selected sampler: 14–22 rows/columns, 2–4 equal rectangles of 2–5 cells per side,
a nonzero outer background, and transparent zero plus colored payload in every
rectangle. The sampler additionally supplies a real distinct-color overlap in
every generated pair. The prototype checks actual Racket predictions instead
of trusting hidden construction state to establish priority identifiability.

`generate_episode(seed)` uses the canonical default. An explicit `priority`
pins the desired setting. `priority="sample"` selects exactly once from
SHA-256 of `ed860c0a9107:priority:v1:<seed>` and reuses that value for all three
demonstrations and the query. Input sampling receives the same seed and indexes
0–3 regardless of priority, so changing the rule alone changes labels.
Global Python random state is not used.

## Run from the packet's `WORK/` directory

The wrapper chooses the included offline Racket and runs payload paths relative
to `WORK/repo/`. Output directories must be new; existing evidence is retained.

```bash
python3 run_with_racket.py python3 \
  generators/ed860c0a9107/workspace/parametric/prototype.py evidence \
  --out ../checks/parametric/final
```

One complete episode, with canonical priority as the default:

```bash
python3 run_with_racket.py python3 \
  generators/ed860c0a9107/workspace/parametric/prototype.py episode \
  --seed 20261020 --out ../checks/parametric/one-default
```

Use `--priority last` for the alternate rule, or `--priority sample` for
deterministic episode-level selection. The optional difficulty is `easy`,
`medium`, or `hard` (default `medium`).

Focused prototype tests, from `WORK/`, using an environment with pytest:

```bash
PATH="$PWD/.venv-review/bin:$PATH" python3 run_with_racket.py python3 -m pytest -q \
  generators/ed860c0a9107/tests/test_parametric_ed860c0a9107.py
```

These tests use `reviewer_support.find_root` and
`reviewer_support.load_selected_generator`. They bind to their own repository or
copied task-test runtime; they do not import a predecessor checkout.

## Execution and exported files

`first` materializes the exact canonical program bytes. `last` changes just the
`find-first` search list from `boxes` to `(reverse boxes)`. Materialization fails
closed if the expected canonical expression changes. Both programs execute
through public `RacketBridge.define_grid` and `RacketBridge.eval_text` methods.
The host binds `g`, `h`, and `w` as specified for a `rule!` body, removes only
the outer `(rule! BODY)` marker, then executes that body. Authored program and
executed body have separate exact text hashes and retained `.rkt` files. No
private runner internals or Python-generated labels are used. The Python mirror
is only an independent comparison in the bounded probe. This adapter supports
this task's known body-form rule; it is not a new general Racket runner.

Each episode directory contains:

- `challenge.json`: only `train` input/output pairs and `test` inputs; no hidden
  priority, seed, reference code, query answers, or source metadata.
- `private.json`: parameters, seed, executed rule and its exact SHA-256,
  source hashes, all labels, both parameter predictions, and exhaustive
  leave-one-out query-role identifiability checks.
- `rule.rkt`: the exact executed materialized Racket source.
- `executed-body.rkt`: the exact body passed to `eval_text`, with the outer
  authored marker removed and the host bindings recorded in evidence.

Give a solver only `challenge.json`. Private files and the evidence summary
are authoring records, not model-visible challenges. Episode directories use
opaque numeric names in the bounded evidence run; the public JSON has a strict
field allowlist.

The evidence command creates six complete episodes: both priorities for seeds
20261020/20261021/20261022 and easy/medium/hard respectively. It retains all
outputs from both parameter rules, checks all four possible query roles for
each episode, checks the default against all eight labeled canonical records
(four unique inputs), and checks sixteen generated samples, including four
boundary override combinations. It materializes both rules under `rules/`,
records source hashes and the actual payload command in `summary.json`, and
hashes retained evidence in `files.json`.

## What the evidence does and does not establish

The canonical examples fit both priorities. `canonical-only-ambiguity.json`
retains that negative result for all four query-role rotations. Generated
episodes must uniquely identify their chosen priority against the exact two
declared settings; otherwise generation raises and does not claim a valid
episode. This is a finite rival check, not proof of unique induction against
every possible program.

“Query-role rotation” means holding out each of the four labeled pairs in turn.
Spatial quarter-turns are tested separately on a lawful two-container conflict.
Both rules are reexecuted on every rotated input. Rotating an existing output
is not a safe relabeling operation: spatial rotation may reverse the containers'
row-major order and change which payload wins.

The extension inherits the selected sampler's geometry and distribution limits.
The retained run is bounded to the reported seeds, settings and inputs; it is
not an exhaustive seed or override-domain test. No production parametric API,
variant approval, or training admission is claimed. Canonical repair coverage
is recorded separately by the main review.

Retained check logs in `WORK/checks/parametric/` include the initial missing-pytest
failures, the deliberate missing-prototype prerequisite failure, subsequent
focused test runs, and the final source-bound evidence. The initial macro
adapter also failed two tests because defining a fresh Racket syntax marker
attempted a protected filesystem lookup. The retained bridge diagnosis isolates
that failure and shows ordinary canonical body execution succeeding; the final
adapter does not define that macro. A failed or superseded run is not upgraded
to a passing final result.
