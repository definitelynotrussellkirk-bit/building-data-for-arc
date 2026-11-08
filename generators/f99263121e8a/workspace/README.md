# Task-local review tools

These are source/evidence inspection utilities for maintainers and later review
agents. **Keep them closed during a fresh Python solve.** They expose reference
behavior. No private answer files are accessed. No third-party Python packages
are required by the probes; `pytest` is needed for the regression suite. Use the
packet's verified Racket installation (`python3 setup_racket.py`).

## Search the teaching curriculum for surviving shortcuts

From the extracted packet root:

```sh
python3 run_with_racket.py python3 generators/f99263121e8a/workspace/rival_search.py \
  --seeds 300 --out ../checks/new-rival-search.json
```

This mirror-scored scanner tests every contiguous five-demo phase in the
periodic default curriculum, in all three difficulty bands, against every entry
in `LESSON_COMPETITORS`. It records exact first witnesses, source hash, schedule, per-rival refutation
counts, and any rival that fits all demonstrations while disagreeing on the next
query. Add `--compound` to enumerate 503 cross-axis alternatives spanning four
component extractors, raw versus masked crops, seven orderings, three alignments
and three separator widths (minus the intended rule):

```sh
python3 run_with_racket.py python3 generators/f99263121e8a/workspace/rival_search.py \
  --seeds 30 --compound --out ../checks/new-compound-search.json
```

Compound mode exits nonzero if any candidate even fits one complete five-demo
window, a stricter condition than query-only survival. Both modes refuse to
overwrite evidence. They are deliberately finite and **not label authority**;
run the Racket census below for differential parity.

## Reproduce a source-bound census

```sh
python3 run_with_racket.py python3 generators/f99263121e8a/workspace/review_probe.py \
  census --seeds 300 --racket-per-band 80 --lessons 60 \
  --out ../checks/new-census.json
```

The wrapper changes directory to `repo`, so the output path starts `../checks`.
The helper refuses to overwrite existing reports. It records exact generator
and rule hashes, seeds, difficulty bands, input/output uniqueness by band,
component counts, strict-canonical frequency, actual Racket differential checks,
one exact Racket-verified counterexample per declared rival, an explicit
override matrix, and five-demo identifiability. All exceptions become failures.
`passed=true` means those listed checks passed, **not** that all inference
shortcuts were eliminated. Distribution and lesson counts are mirror-based;
actual Racket calls are counted separately.

`--generator PATH` tests an earlier task generator with current diagnostic
semantics while skipping unsupported final-only contracts. For the immutable
assignment baseline, use
`--generator ../.review/baseline/repo/generators/f99263121e8a/generator.py`.
A baseline report's `passed=true` means successful execution/parity, not adequate
semantic coverage; inspect rival-refutation counts and canonical support.

## Audit-only counterexamples

```sh
python3 run_with_racket.py python3 generators/f99263121e8a/workspace/review_probe.py \
  audit --seeds 60 --racket-per-band 15 --out ../checks/new-audits.json
```

This uses only immutable assigned targets `4e7f50f23507` and `6e175c009c2a`.
It does not edit either target. `passed=true` means the reproductions and sampled
output comparisons succeeded; it does **not** mean the audits found no issue.
The report retains both exact Racket-verified counterexamples and whether the
target's own `self_check` admits each one.

## Relocation and regression suite

```sh
python3 run_with_racket.py python3 generators/f99263121e8a/workspace/relocation_probe.py \
  --out ../checks/new-relocation.json
cd repo
python3 -m pytest -q generators/f99263121e8a/tests/test_generator_f99263121e8a.py
```

Relocation copies the selected portable runtime, moves that copy, removes its
old location, clears inherited `PYTHONPATH`, and starts an isolated (`-I`) child.
It checks generated examples against actual Racket and rejects any imported
module from the original repository. The external verified Racket executable is
an explicit dependency, not a borrowed source checkout.

The repository's default test discovery covers `repo/tests`; the task-local
suite must be run explicitly. The synthetic fixture failure in
`tests/test_review_solve.py::test_duties_solve_preparation_runs_from_packet_root`
is independent of this generator: the fixture library omits the source-bound API
that its packet launcher imports. The return includes
`checks/round2/proposed_shared_fixture_patch.diff`, a narrowly scoped test-only
correction that copies `src/arcpuzzles` in the solve-test packet helper. It is
intentionally excluded from the assigned source patch. The rejected global
fixture patch and both full-suite logs are retained beside it; read those before
deciding whether to apply the proposal.

The review probe adapts the inherited normalizer's `scripts` package name to
canonical `shared/tools` in its own process only; it does not edit shared files.

## Handoff

Read the return's `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, `AUDIT.md`,
then the exact commands in `RESULTS.json`. Apply `patches/source.patch` through
the project's review-intake workflow. Do not reuse source snapshots as passed
receipts for a later revision. Keep all source-hash changes and rejected runs.
The next maintainer should independently score the masked solve, verify intake,
decide whether downstream episode consumers preserve consecutive five-demo
windows, and separately review the proposed shared-fixture diff.
