# Workspace

The selected implementation is `../generator.py`. Workspace tools are never
automatically selected as generators.

## Replay complete lesson windows

`probe_lesson_windows.py` is a reusable source-bound authoring probe for tasks
that declare `LESSON_COMPETITORS` and optionally `CANONICAL_SHORTCUTS`. It imports
the task's actual declarations, verifies all claimed canonical shortcuts, then
generates consecutive inputs and obtains authoritative outputs through public
`arcpuzzles.catalog.Catalog.apply` in batches of at most 64. It retains inputs,
labels, source/canonical hashes, application receipts, refuting example indices,
each production query and every single-pair query rotation. A partial run,
invalid input, missing rivals, label error or ambiguity cannot be a pass.

From the original packet root, after `python3 setup_racket.py`:

```sh
python3 run_with_racket.py python3 \
  generators/5430502683a1/workspace/probe_lesson_windows.py \
  --task 5430502683a1 --seed-start 0 --seeds 3 --starts 8 \
  --out ../checks/cyclic-windows-replayed.json
```

Use a new output path. The wrapper executes from `repo/`, so the script path
starts with `generators/` and the check output starts with `../checks/`.
The demonstration count defaults to the module's `EXAMPLES_NEEDED`; `--demos`
can explicitly test a different policy. `--starts` is the number of consecutive
window starts to enumerate, beginning at zero. Select the complete actual
curriculum period; this task needs 8. The tool can inspect another task via
`--task`, provided its generator follows the supported public interfaces.

For the delivered v4.0.1, seven demos and one query are used. The retained run
tested seeds 0..2 and starts0..7 in all three bands: 72 windows, 576 query rotations,
135 source labels and 82 unique input hashes. No tested rival was ambiguous.
Windows overlap, and canonical-weighted geometry can repeat across bands;
these counts must not be described as independent puzzle samples.

This direct-sequence probe complements the production sampler census:

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 5430502683a1 \
  --per-band 100 --rotate-query --timeout 1800 \
  --out ../checks/lesson-census-replayed.json
```

The census retains actual accepted indices, so rejected draws cannot silently
be counted as scheduled teaching witnesses. The window probe enumerates cyclic
starts that a production census does not exhaust for each seed. Neither tool
certifies unlisted hypotheses, arbitrary lesson assembly, all seeds, or training
admission. Both expose answers and must stay closed during a visible-only solve.

## Focused and isolated tests

The 449 cases in `../tests/` use `reviewer_support.find_root`, `canonical_path`
and `canonical_pairs` for compatibility with both library and runtime layouts.

```sh
python3 run_with_racket.py python3 -m pytest -q \
  generators/5430502683a1/tests
python3 run_with_racket.py python3 -m arcpuzzles check 5430502683a1 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-replayed
```

The public task-test command snapshots the selected tests/workspace and records
the actual isolated runtime. Its interpreter must have pytest available with
user-site packages disabled; use an ordinary project virtual environment with
the packet's declared dependencies when needed. A no-tests or import failure
is not a pass. The general twelve-stage battery does not run these task tests.
