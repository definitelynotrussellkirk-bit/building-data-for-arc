# Reusable review tools for 996fc37f49d9

These tools inspect generators and their Racket authorities. **Do not use them during a visible-only solve phase.** They are review utilities, not training admission tools. They use the supplied native library and copy its own runtime; no network is needed after packet Racket setup.

## Reproduce the final review checks

From the extracted packet root, after applying the returned task patch:

```bash
python3 setup_racket.py
python3 -m pytest -q repo/generators/996fc37f49d9/tests
python3 run_with_racket.py python3 -m arcpuzzles check 996fc37f49d9 --battery --timeout 4000 --phase after --out ../checks/replay-after
python3 run_with_racket.py python3 -m arcpuzzles check 996fc37f49d9 --stage lint --phase after --out ../checks/replay-lint
python3 run_with_racket.py python3 generators/996fc37f49d9/workspace/probe_distribution.py --phase final --per-band 600 --lesson-seeds 30 --racket-per-band 64 --out ../checks/replay-census
python3 run_with_racket.py python3 generators/996fc37f49d9/workspace/audit_findings.py --per-band 256 --out ../checks/replay-audits
python3 run_with_racket.py python3 generators/996fc37f49d9/workspace/verify_portable.py --out ../checks/replay-portable
```

The wrapper changes the working directory to `repo`, sets `PYTHONPATH=src` and selects verified Racket. Output paths therefore use `../checks`. Choose new output directories; the probes refuse to overwrite prior evidence. `RESULTS.json` records the exact commands used during this review (some initial probes set `RACKET_PATH` directly from packet root).

## Original-versus-final census without reverting the working generator

The original file is returned in `checks/probes/baseline_generator.py` with SHA-256 `57e4744c366cd942f344ef316a0a006120068d74213df3d639914b0a4c1324ce`. Pass it as a staged-only replacement:

```bash
python3 run_with_racket.py python3 generators/996fc37f49d9/workspace/probe_distribution.py --phase before --per-band 600 --lesson-seeds 30 --racket-per-band 64 --baseline-generator ../checks/probes/baseline_generator.py --out ../checks/replay-before
```

For exact replay of the original packet-root invocation recorded in its receipt, first create `.review/baseline_generator.py` from that retained baseline, set `RACKET_PATH` to the binary returned by `setup_racket.py`, then run the receipt's arguments from packet root. The original before battery itself was run before source edits; a replay of that battery requires the original packet source, not the final generator under a misleading “before” label.

## What each tool measures

`probe_distribution.py`: independent 4-neighbour occupied-area oracle; explicit wrong rules; colour/rank support; canonical floor; exact and structural diversity; lesson ambiguity; a declared actual-Racket subset; exact handcrafted and generated box-inversion witnesses. It returns nonzero for final-cohort failures, but original known ambiguities are retained as baseline measurements rather than causing a baseline-command failure.

`audit_findings.py`: only the two assigned targets. It detects fixed role-layout support, crop/marker semantics, canonical clipping omission, validator false acceptance and ignored overrides. Target sources are never edited. The crop oracle copies nonzero **bbox contents**, including markers inside that box, exactly as the authority does. The initial wrong oracle is retained as `rejected_audit_oracle_v1.py` solely for provenance.

`verify_portable.py`: creates a disposable runtime outside the source tree, stages the new tools/tests that the old runtime map does not know about, runs all 80 task tests under isolated Python with a source-read audit guard, checks imported file origins, and compares 36 generated outputs with Racket. It records the actual temporary directory then removes it. This is not an operating-system sandbox, and the receipt says so.

`rejected_v1_generator.py` and `rejected_v2_generator.py` are failed intermediate snapshots. They are not imported by production generation. Their historical failures are recorded under checks/probes and checks/after. Review claims always bind to the final generator hash, not merely the reused version string.

## Important limitations

Do not add per-band counts as if transforms were independent draws. Do not call overlapping windows unique lessons. Do not call all 1,800 Python-oracle outputs Racket checked: the census explicitly runs 199 Racket comparisons. No inference about trained-model accuracy follows from these structural counts. The full repository pytest has an unresolved startup-sensitive timeout test in this environment; see `checks/probes/runtime_startup_probe.py` and FEEDBACK_TO_CODEX.md.
