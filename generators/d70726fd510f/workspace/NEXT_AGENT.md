# Handoff: review-6c4f2053a7aa3c1b

## State

Task `d70726fd510f` is ready for independent maintainer intake. The assignment/audit draw are unchanged; do not redraw. Final generator version `2.1.0`, SHA256 `83d38a64916999f05b2dfcffd7f75fc9c261df02491582b61173a01aab46b0c7`; probe SHA256 `152e7b7eb98f0a919c303b251ef0c6628aad035ef4b2b09f126814b679413baf`. No training-admitted flag was set.

The delta includes exact-control and validation repairs, independent proposal/symmetric XOR projection, core/transfer/broad schedule, executable rival declarations, 215 task tests and a reusable probe. Selected Racket target text changed in formatting only; canonical ledger and semantics remain unchanged. Audit tasks `89c85768abe1` and `d1c037cda16e` have findings and unchanged source.

## Evidence first

Read return `REVIEW.md`, `RESULTS.json`, `QUESTION_ANSWER.md`. Final battery: `checks/final-verified/`; final/comparable baseline lessons: `checks/lesson-probe/final.json` and `baseline.json`; portable tests/public parity: `checks/portable-final-v2/`. `checks/final-battery/` is intermediate success on older bytes.

The standard `EVIDENCE-BUNDLE` has path/size/hash manifest and supported extraction instructions. Large JSON evidence is also losslessly compacted, with identical duplicate payloads represented by references. After extraction, use `python3 checks/packaging/restore_evidence.py --out <fresh-directory>` for original report formatting and duplicate paths. It verifies original SHA256 values and preserves every failed run.

Do not reuse counts from historical unreviewed `review-7db198064734f44c:v0001`; selected source in this incoming packet was still baseline.

## Replay after applying the delta

Use fresh output paths. From packet root:

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 -m arcpuzzles check d70726fd510f --battery --timeout 4000 --phase after --out ../checks/replay-battery
python3 run_with_racket.py python3 -m pytest -q
```

From `repo/`:

```bash
python3 -m pytest -q generators/d70726fd510f/tests
python3 generators/d70726fd510f/workspace/lesson_probe.py --lessons-per-band 100 --overlap-windows 100 --seed 0 --sample-index 4 --schedule-cycle 3 --require-pass --require-rival-refutation --out ../checks/replay-lessons.json
```

Add `--racket-parity` with `RACKET_PATH` set to the archived runtime, as documented in `LESSON_PROBE.md`, or use the portable route below. Default exit 0 only means a report was written and can accompany gate FAIL; use failure-exit flags for gating.

From packet root, with a fresh destination:

```bash
python3 checks/portable/verify.py --runtime ../portable-replay --out checks/portable-replay
python3 checks/portable/public_parity.py --runtime ../portable-replay --out checks/portable-replay
```

Preparation copies locally installed test dependencies into a separate test environment and explicitly includes new task tests/workspace files. The original successful runtime was `/workspace/scratch/11eef787ff33/portable-final-v2`; actual paths are in its receipt.

## Interpretation

Final: 12/12 battery stages, 215 task tests in each layout, 234 repository tests passed and 3 optional Torch skips, zero ambiguities in 300 independent and 300 separately counted overlapping lessons, 99/99 Racket parity, and 9 portable lessons/36 matching pairs. The overlap section has only 309 distinct inputs. Repeated parity in another layout does not double independent coverage.

Ordinary consecutive demonstrations are covered by the three-profile schedule. Overrides, arbitrary assembly and unknown rivals need separate evidence. Density/texture remain proposal controls. No Qwen experiment was run.

Both solve episodes finished with one genuine revision and 3/3 visible examples passing. Blind `6d06c5b96c19` declares no earlier exposure; repaired task declares earlier exposure. Neither consulted references while solving. Masked verdicts are unknown. If generator bytes change, retain the old solve and prepare a fresh source-bound solve per packet rules.
