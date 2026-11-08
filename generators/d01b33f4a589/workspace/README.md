# Reproducible complete-lesson probe

`lesson_probe.py` uses the sampled generator's actual `LESSON_COMPETITORS` and
`CANONICAL_SHORTCUTS`; it does not maintain a second, stale list of rival names.
Every declared canonical shortcut must fit every available canonical pair.
For each whole lesson it separates rivals refuted by demonstrations, rivals
that harmlessly survive and agree on the query, and surviving rivals that
change the query answer. Only the last category is an ambiguity failure.

From the extracted review packet root (choose a NEW output path each run):

```sh
python3 repo/generators/d01b33f4a589/workspace/lesson_probe.py \
  --library repo --seeds 256 --starts 8 --out checks/lesson-replay.json

RACKET_PATH="$PWD/.review/racket-runtime/racket/bin/racket" \
python3 repo/generators/d01b33f4a589/workspace/lesson_probe.py \
  --library repo --oracle racket --seeds 16 --starts 8 \
  --runner-lessons 128 --out checks/lesson-racket-replay.json
```

Run `python3 setup_racket.py` first for the included offline runtime, or set
RACKET_PATH to another installed Racket. `--library` accepts the absolute library
root, so the tool also works outside the packet. The Racket mode copies the
existing portable runtime to a temporary directory, explicitly binds the sampled
module (including baseline modules), executes the canonical rule, and cleans up.
It does not edit shared infrastructure or install new packages.

Replay the frozen source against the final competitor contract:

```sh
python3 repo/generators/d01b33f4a589/workspace/lesson_probe.py \
  --library repo \
  --generator-source .review/baseline/repo/generators/d01b33f4a589/generator.py \
  --contract-source repo/generators/d01b33f4a589/generator.py \
  --seeds 256 --starts 8 --out checks/lesson-baseline-replay.json
```

The frozen baseline belongs to the original packet, not this delta return.
Use `--seed-start`, `--seeds`, `--starts`, and `--bands` for disjoint probes.
The default eight starts covers every residue of the four-slot schedule twice.
`--runner-lessons` requires Racket and exercises actual `runner.run_one` assembly,
including duplicate rejection, separately from raw overlapping windows.
Outputs include source/rule hashes, exact population definitions, unique-grid
counts, literal-public and axis frequencies, every failure's replay coordinates,
and full seed-661 input/reference/rival grids. Reports explicitly mark Python
mirrors as non-independent. Existing output files are never overwritten.

New task-local regressions (run separately from the repository suite):

```sh
RACKET_PATH="$PWD/.review/racket-runtime/racket/bin/racket" \
python3 -m pytest -q \
  repo/generators/d01b33f4a589/tests/test_lesson_coverage.py \
  repo/generators/d01b33f4a589/tests/test_lesson_probe.py
```

The live-Racket CLI regression skips only when RACKET_PATH is absent. It guards
against importing a stale `puzzle_generators` package before constructing the
portable runtime. The unchanged original task fixture needs the portable layout;
see the return's `checks/verify_portable_runtime.py` for a relocation/hash/import
check and its exact unittest invocation. Returned reports are evidence, not an
approval override or a promise of neural-model accuracy.
