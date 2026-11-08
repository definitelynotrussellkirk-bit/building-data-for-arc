# F1: avoid aliased generator schedules in defect lint

**Status: optional shared-tool proposal; not applied to shared source.**

The stock per-puzzle linter calls `generate(sd, sd, difficulty=band)` for every
sample. For a legal `(seed + sample_index) % 2` curriculum, all requests reach
one phase. Here that phase is the deliberately informative `rich_top` example,
so the linter reports limited axis variation and persistent-marker mismatch
without inspecting the generator's other phase.

`sampling.patch` changes the per-puzzle sample plan to seed 1 with consecutive
indices 0 through N−1. It keeps the existing N samples per difficulty, preserves
generic-generator sampling and all detector functions, and adds exact request
records plus declared-period index coverage to the JSON result. A failed
generation request remains in that record. `manifest.json` binds the original
tool, proposed tool and retained baseline-generator fixture by SHA-256.

## Measured results

Each population has 24 requests: 8 per band for easy, medium and hard.

| Source and measurement | Stock sampler | Proposed sampler |
|---|---|---|
| Baseline v1.2.1 profiles | 24 rich, 0 varied | 12 rich, 12 varied |
| Baseline axis-span warnings | 5 | 0 |
| Final v1.3.0 profiles | 24 rich, 0 varied | 12 rich, 12 varied |
| Final axis-span warnings | 3 | 0 |
| Baseline persistent-marker support | `{2}` | `{2,3,5}` |
| Final persistent-marker support | `{2}` | `{2,3,5,6}` |
| Canonical persistent-marker support | `{3,5}` | `{3,5}` |
| Deliberately narrow control | — | Still emits axis-span |

The final stock warnings concern `key_len`, `palette_size`, `zero_rings`, plus
the separate persistent-marker structural advisory. Both original and proposed
populations were labelled with the selected Racket authority through the public
`Catalog.apply` API: 33 distinct inputs for the baseline comparison and 28 for
the final comparison, all with valid outputs and valid selected-generator domain
checks. The populations overlap, so these counts are not independent samples.
The structural diagnostic is unchanged; its mismatch disappears because its
measured support now includes the varied phase. No semantic threshold or
canonical comparison was weakened.

Baseline producer SHA-256:
`7dada8785969fa93b14a0ae95750f70969ef80cda6f9c8ce35ae3778f5a4d8f7`.

Final producer SHA-256:
`c14518d0be325525090968de13d9598d195cf38a7c5f8732a0d87925cc80ca39`.

The Racket-labelled receipts explicitly distinguish the baseline input producer
from the current v1.3.0 generator copied into the reference-execution snapshot.
Selected rule-text SHA-256:
`4a0c5067e0e995025593ed564bad54f6646b44cf04d196a1ccf19d52b86c2591`.

## Reproduce

From the outer packet directory, with its prepared Python environment:

```bash
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run ../.venv/bin/python ../checks/linter-proposal/test_sampling.py
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run ../.venv/bin/python ../checks/linter-proposal/reproduce.py --out ../checks/linter-proposal/reproduced-baseline.json --racket
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run ../.venv/bin/python ../checks/linter-proposal/reproduce.py --generator generators/2e663d812b7a/generator.py --out ../checks/linter-proposal/reproduced-final.json --racket
```

Use fresh output names. A different prepared Python 3.12+ interpreter may replace
the `.venv` interpreter in both wrapper and payload positions.

`reproduce.py` extracts and executes the actual sampling prefix of each tool's
`lint_one` function and its unchanged axis-honesty function. It uses the public
context observer and does not import private `scripts.*` helpers. The retained
results are targeted sampler/axis/structure evidence. A separate full candidate
defect-lint run is retained under `integration/`; it does not change the selected
stock battery result. The six regression tests cover the original failure, both phases under
the proposal, a real narrow fixture, honest partial/complete residue reporting,
failed-request retention and unchanged detector implementations.

## Full strict integration

The complete proposed linter also passed end to end in an independent runtime
exported by the public `arcpuzzles workspace --id 2e663d812b7a --out DIR` command.
Only the exported runtime's `scripts/generator_defect_lint.py` received the
proposed bytes; the original runtime manifest is retained unchanged, with a
separate tool-overlay identity. The selected repository shared tool and generator
were checked before and after execution and remained unchanged.

The exact full invocation used `--strict --seeds 8 --bands easy,medium,hard`,
without `--fast`, and the real verified Racket runtime. It returned exit **0**,
**0 issues**, **0 warnings**, and `scanned 1; FLAGGED 0`, with all 24 main sampling
requests recorded. This is a full candidate defect-lint pass for the selected
final generator; it is not a selected-tool battery pass or universal schedule
coverage. The final period-10 receipt still reports only residues 0 through 7
per band as incomplete coverage.

`integration/RESULTS.json` records exact commands, interpreter and Racket
identities, source hashes, original runtime manifest hash, executed candidate
overlay hash, exit statuses and the runtime's disposition. Full linter JSON,
stdout and stderr are retained alongside it. The initial pre-linter harness
failure in `integration/attempt-1/` is preserved: the CLI returns an export
summary, not the full manifest, and the harness originally compared those two
different documents. The corrected harness validates the summary's actual
fields against the retained manifest; no candidate linter change was involved.

To repeat the full integration into fresh evidence:

```bash
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run ../.venv/bin/python ../checks/linter-proposal/integration/run_integration.py --out ../checks/linter-proposal/integration-repeat
```

## Evidence inventory

- `baseline-results.json` and `baseline-results-racket.json`: source-bound
  baseline population, original false warnings and authoritative outputs.
- `final-results.json` and `final-results-racket.json`: final-source comparison,
  exact request records and partial schedule coverage.
- `tests.log`: six tests passed, zero failures/errors/skips.
- `patch-replay.json`: the exact patch applied in a fresh temporary Git root and
  reproduced the proposed tool byte for byte.
- `verification.json`: exact commands, exit statuses and retained evidence paths.
- `baseline_generator.py`: small retained source fixture for the reproduced
  failure; it is not selected by the repository.
- `candidate_generator_defect_lint.py` and `sampling.patch`: complete proposed
  source and its exact delta against the original shared tool.

The final generator declares period 10; the default budget samples residues
0 through 7 in each band, so the receipt correctly marks coverage incomplete.
A fixed-seed index sweep does not inspect all seeds or establish semantic
correctness. The proposal addresses the general aliasing caused by coupling
seed and index and preserves genuine narrow-support warnings; it requires a
shared-tool decision before it affects any battery. With eight requests for a
ten-slot schedule, the proposed result remains finite partial evidence and
does not replace the separate lesson-schedule census.
