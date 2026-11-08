# Reusable review tools

The selected implementation is `../generator.py`. These tools do not select an
alternate generator, change reference authority, or approve training data.

## Record a command and its evidence

`record_command.py` needs only Python's standard library. Run it from any working
directory; `--cwd` is the child's actual working directory, `--out` must name a
new directory, and relative `--hash-input` paths resolve from the child's cwd.
Arguments after `--` are passed directly to the child without a shell.

From the review packet's `WORK` directory, with a suitable Python interpreter:

```bash
python3 repo/generators/49898d244b5f/workspace/record_command.py \
  --cwd . --out checks/new-task-test-run --timeout 600 \
  --hash-input repo/generators/49898d244b5f/generator.py \
  -- python3 run_with_racket.py python3 -m arcpuzzles check 49898d244b5f \
  --stage task_tests --phase after --timeout 600 --out ../checks/new-task-tests
```

The result directory contains `receipt.json`, `stdout.log`, and `stderr.log`,
including failed commands. The receipt binds before/after input hashes and the
recorder's own source. It records only an allowlisted environment subset; avoid
putting secrets in command arguments. Exit codes propagate child failure, with
124 for timeout, 3 for changed inputs, and 2 for recorder/launch errors. POSIX
timeouts kill the newly created child process group; on other systems cleanup
is limited to the direct child. It never overwrites an earlier evidence folder.

## Check column semantics with real reference labels

`probe_column_rules.py` uses the shared public `reviewer_support` canonical-data
helpers and `RacketBridge`. From `WORK`:

```bash
python3 run_with_racket.py python3 \
  generators/49898d244b5f/workspace/probe_column_rules.py \
  --require-contract --out ../checks/new-column-probe.json
```

The default bounded probe labels three canonical pairs, five saved hand inputs,
and 24 generated inputs with actual Racket. It scores five independent rivals
and every rival declared by the selected generator, checks canonical-shortcut
claims, and exercises a canonical-only ambiguous lesson. It records exact inputs,
outputs, source hashes and command provenance. An existing output is refused.
Use `--help` for an alternate source path or seed count. It works from arbitrary
directories when the public runtime is on `PYTHONPATH` and Racket is available.

For broader production lesson sampling, use the shared `arcpuzzles lesson-census`
command with `--per-band 100 --rotate-query`. The small probe does not replace
that census, and neither proves uniqueness against every possible hypothesis.

## Replay the minimal-shape warning

```bash
python3 run_with_racket.py python3 \
  generators/49898d244b5f/workspace/replay_lawful_minimal.py \
  --out ../checks/new-lawful-minimal.json
```

This tool verifies three stored 7×7 inputs against actual Racket: a single seed,
three horizontal same-color seeds, and three vertical same-color cells. The
first two fill one and three columns and belong to the positive domain; the
vertical case returns blank and is rejected. The report records exact source,
rule, input, output and tool hashes. It provides evidence for the generic
minimal-impostor warning without changing or suppressing the shared gate.
