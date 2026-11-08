# Source-bound lesson probe

`lesson_probe.py` measures the source supplied through `--generator-file`. It
imports the actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` dictionaries,
checks every claimed canonical shortcut against all five recorded pairs, and
separately evaluates all sixteen Boolean occupancy truth tables. The independent
truth-table convention is `00, 01, 10, 11`, with XOR represented by table 6.

The default run contains 100 independent lessons per easy/medium/hard band.
Each lesson has three demonstrations and one query. A lesson uses one seed and
four consecutive sample indices. Independent seeds increase from `--seed`; the
start index cycles through every declared `SCHEDULE_PROFILES` position. A second
measurement contains 100 overlapping windows per band from a single additional
seed. These windows receive separate counts and are never presented as additional
independent lessons.

The report records exact source, tool, competitor-source, canonical-record and
rule hashes. An explicit `--schedule-cycle 3` gives baseline and final runs the
same diagnostic seed/index plan; it does not assert that the baseline has a
native schedule. Global distinct counts use set unions across bands and modes,
so reused inputs and overlapping windows are never counted twice. Every sampled seed and sample-index tuple is recorded. Each section
reports total appearances, distinct inputs, distinct outputs, distinct pairs,
and distinct lessons. A complete first witness is retained for each failure
class, including the first rival that survives the demonstrations and disagrees
on the query. Demonstration survival without query disagreement is recorded
separately. These are finite-rival diagnostics, not an assertion that every
possible alternative rule has been eliminated.

## Commands from the repository root

Final source:

```sh
python generators/d70726fd510f/workspace/lesson_probe.py \
  --lessons-per-band 100 --overlap-windows 100 --seed 0 --sample-index 4 --schedule-cycle 3 \
  --out ../checks/lesson-probe/final.json
```

Older baseline bytes lacking declarations can be measured against the current
explicitly bound declaration source:

```sh
python generators/d70726fd510f/workspace/lesson_probe.py \
  --generator-file /absolute/path/to/baseline-generator.py \
  --competitor-file generators/d70726fd510f/generator.py \
  --sample-index 4 --lessons-per-band 100 --overlap-windows 100 --seed 0 --sample-index 4 --schedule-cycle 3 \
  --out ../checks/lesson-probe/baseline.json
```

The independently reproduced baseline seed-0 ambiguity uses demonstrations
4, 5, 6 and query 7. Its demonstrations omit occupancy `01`; table 4 and XOR
both fit those demonstrations but disagree on the query. This tuple is a useful
reproducer and is not itself a fresh Racket validation claim.

Tests:

```sh
python -m pytest generators/d70726fd510f/tests/test_lesson_probe.py -q
```

## Portable runtime and optional Racket parity

The bootstrap locates either `shared/runtime/puzzle_generators` in a checkout or
`puzzle_generators` inside a portable runtime produced by the supported runtime
preparation API. For a separately staged runtime, provide
`--generator-file /runtime/puzzle_generators/per_puzzle/d70726fd510f/generator.py`
and `--runtime-root /runtime`. `--canonical-file` can bind the canonical ledger
explicitly. No private runner function is used by the probe.

Python diagnostics are explicitly labeled as Python XOR predictions. Add
`--racket-parity` when a real Racket installation is available in the process
environment. This invokes the public `Catalog.apply` API, verifies its executed
normalized rule hash against the report's canonical authority, and records distinct
Racket outputs. The exact ledger rule hash and public execution text hash are
retained separately: the public runtime hashes the wrapped callable text, so
those exact-byte hashes can differ while their normalized rule authority matches.
Applications respect the public API input limit by batching the matrix. Its bounded matrix covers all 64 ordered allowed foreground
pairs (including color 2 and equal foreground colors), the four extreme dimension
combinations crossed with four occupancy states, default/difficulty examples,
every declared helpful/degenerate texture, and all five canonical examples.
For a portable runtime outside a checkout, `--library-root /checkout` supplies
the public catalog used for this optional execution route.

Exit zero means the requested measurement completed. Inspect reported failures,
canonical shortcut fits, and optional parity results when interpreting quality;
measurement completion does not approve a generator or create training labels.

## Optional measured gate

`--require-pass` returns exit status 2 if a claimed canonical shortcut fails any
canonical pair, the independent Python reference fails a canonical output, a
sample fails generation/input validation/self-check, a declared rival raises,
a surviving rival disagrees with the query, or requested Racket parity fails.
The default diagnostic command preserves exit status 0 after measurements and
reports these problems in `diagnostic_gate`; completion is not approval.

A rival which survives demonstrations and agrees on this particular query is
reported separately. To require that every declared rival is refuted by each
lesson's demonstrations, add `--require-rival-refutation`, which also enables the
gate. These are finite measured checks against the declared hypotheses; they do
not prove uniqueness against every conceivable rule. Requested Racket parity
also binds each public application receipt's generator hash to the exact module
bytes imported by the probe, detecting a source change during staging.

A strict final command adds `--require-pass --require-rival-refutation` to the
final census, while the baseline command remains diagnostic so its failures can
be inspected. Keep identical `--seed`, `--sample-index`, `--schedule-cycle`,
`--lessons-per-band`, and `--overlap-windows` values in both commands.
