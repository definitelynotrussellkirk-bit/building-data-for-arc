# Reproducers and compact next-agent handoff

Selected implementation: `../generator.py`, version 3.0.1. This workspace contains **diagnostic tools**, not alternative automatically selected generators. No private solve labels are read by these tools.

## What changed and why

The old singleton distribution taught pixel counting rather than component counting and rejected canonical multi-cell/noise inputs. The repaired generator varies body areas, monochromatic diagonal connectivity, different-color contact and distractors. The reference remains four-neighbor component counting. Canonical-scale support is deliberately mixed into every difficulty, not exempted from checks. Negative fixtures are explicit-only and not declared ordinary AXES values.

Final reviewed generator SHA256:
`2dadb7679e19dc75fe6c86017bafc4502f292ddd2ae6931c50f0618346b4fbcd`.

In the returned packet, `checks/after-verified/` is the final battery. `checks/after-final/` is an intermediate version despite its historical name. Do not cite it as final-source evidence. `checks/verified-census.json` and `.rows.jsonl` contain the final default census; the baseline census has its own old hash. The visible solve is not blind and query correctness is unknown.

## Commands in the original review packet

Run from the extracted packet root after applying the task patch. The wrapper verifies the pinned Racket installation, sets `RACKET_PATH`, sets source imports, and runs the command from `repo`. Evidence output paths below are relative to that actual Python working directory. Choose fresh output names for tools that reject an existing directory.

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 -m pytest -q generators/dc91f4798e24/tests/test_component_curriculum.py
python3 run_with_racket.py python3 -m arcpuzzles check dc91f4798e24 --battery --timeout 4000 --phase after --out ../checks/next-agent-battery
python3 run_with_racket.py python3 generators/dc91f4798e24/workspace/review_probe.py census --phase next-agent --per-band 250 --out ../checks/next-agent-census.json
python3 run_with_racket.py python3 generators/dc91f4798e24/workspace/review_probe.py audits --per-band 25 --out ../checks/next-agent-audits.json
```

`review_probe.py` uses the shipped prepared-runtime API in source layout and the local runtime directly in portable layout. It computes rivals independently and executes intended labels through Racket. Reports include source/rule hashes, actual runtime directory, manifest hash, seeds/indices, duplicate-aware denominators and exact counterexamples. Census rows retain each input and Racket output. The audits are deliberately scoped to this assignment's two immutable targets; they do not edit them.

The baseline can be re-evaluated in the original packet using `census --generator-source ../.review/baseline/repo/generators/dc91f4798e24/generator.py`; retain its separate phase label. The frozen baseline is not a runtime dependency of the new generator.

## Portability and runtime diagnostics

```bash
python3 run_with_racket.py python3 generators/dc91f4798e24/workspace/portable_smoke.py --out ../checks/next-agent-landlock
python3 run_with_racket.py python3 generators/dc91f4798e24/workspace/portable_smoke.py --isolation python-audit --out ../checks/next-agent-python-audit
python3 run_with_racket.py python3 generators/dc91f4798e24/workspace/runtime_timeout_probe.py --out ../checks/next-agent-timeout.json
```

The first command requires Linux Landlock and fails visibly when unavailable. The second is an **explicitly weaker** mode: copied sources/Racket, source-free Python import paths, and a Python audit hook denying original-source reads. It is not an OS sandbox and does not sandbox Racket's filesystem. The exact temporary runtime directory is retained in `result.json`; the temporary runtime itself is deleted, not shipped. Neither tool borrows a predecessor checkout.

The timeout tool only measures the unchanged shared runner with normal versus `-S` Python startup and 0.2/1.0-second budgets. Its exit 0 means the diagnostic ran; inspect recorded stdout/timing rather than calling a failing suite fixed. The shared suite had 169 passes and one startup-sensitive timeout failure on both attempts in this review.

Dependencies are the repository's declared Python stack (NumPy, Pillow, pytest) and a functioning Racket executable. Outside the packet wrapper, use the repository's normal environment and set `RACKET_PATH` explicitly. The tools do not install packages, access external services, or modify global startup behavior.

## Next useful work; do not reopen settled decisions

Independently inspect/apply the delta and rerun the final task tests/battery before considering admission. Resolve the shared timeout fixture in a separate authorized change rather than weakening these task checks. Maintainer scoring of the masked solve remains outstanding.

Audit A1 (`26f313fdf812`) needs objects where bbox top-left order differs from row-major first-cell order; the exact accepted counterexample is in the return. Audit A2 (`9b028298192f`) needs a decision about expanding its explicit morphology grammar before adding vertical-domino examples. More random seeds inside either unchanged grammar are not the useful next step. Keep both targets unchanged unless newly assigned.

For the next review ZIP, retain the accepted generator hash, final battery/census receipts, unresolved timeout/isolation caveats, and these targeted audit findings. Draw a new assignment through the normal workflow; do not reroll this immutable assignment or mark this reviewer evidence as automatic approval.
