# Reusable review probes

The selected implementation is `../generator.py`. These scripts support evidence collection; they are not alternate generator entry points. Apply the return's source patch to the original packet before using them. Use a new output directory on every run so previous failures are not overwritten.

## Selected-task replay

Run at the extracted packet root:

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 -m arcpuzzles check fbf36c193fa6 --battery --timeout 4000 --phase after --out ../checks/replay-after
python3 run_with_racket.py python3 generators/fbf36c193fa6/workspace/stage_review.py --out var/ray-replay
ROOT="$PWD"
export RACKET_PATH="$ROOT/.review/racket-runtime/racket/bin/racket"
export PATH="$(dirname "$RACKET_PATH"):$PATH"
cd repo/var/ray-replay
python3 -m pytest -q tests/test_generator_fbf36c193fa6.py tests/test_ray_distribution.py
python3 review_probe.py --phase final --lessons-per-band 100 --out "$ROOT/checks/replay-probe"
cd "$ROOT"
python3 run_with_racket.py python3 -m pytest -q
```

`stage_review.py` extends the normal frozen runtime map by copying every selected-task `tests/test_*.py` and the coverage probe. `REVIEW_RUNTIME_MANIFEST.json` records their hashes. New tests otherwise can be absent from a staged runtime even when the repository suite passes. Direct pytest/probe commands must run inside the staged runtime, not from the task source directory; `run_with_racket.py` itself always changes to the repository root.

The census imports the generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` mappings, verifies all public canonical pairs, and evaluates every generated output with a live persistent Racket process. It does not read the separate solve episode's private answers. Default lessons use seed `int(sha256("fbf36c193fa6:coverage-v1:BAND:LESSON").hexdigest()[:12], 16)` for lesson 0..99, and sample indices `11*lesson + offset` for offsets 0..3. Three demos and one query share one seed. There is no rejection filtering. All cyclic starts are counted, as are unique inputs, failures, rival survivals and exact counterexamples. A nonzero exit is meaningful: before-phase evidence deliberately records the directional shortcut surviving.

## Findings-only audit replay

At the packet root, with a fresh runtime destination:

```bash
python3 run_with_racket.py python3 -c 'from pathlib import Path; from arcpuzzles import Catalog; from arcpuzzles.runtime import prepare_runtime; prepare_runtime(Catalog(), Path("var/ray-audit-replay"), task_ids=["96d2d525a266", "13e4ae480f66"])'
cp repo/generators/fbf36c193fa6/workspace/audit_probe.py repo/var/ray-audit-replay/audit_probe.py
ROOT="$PWD"
export RACKET_PATH="$ROOT/.review/racket-runtime/racket/bin/racket"
export PATH="$(dirname "$RACKET_PATH"):$PATH"
cd repo/var/ray-audit-replay
python3 audit_probe.py --out "$ROOT/checks/replay-audits"
```

The audit program succeeds when its concrete defect reproductions and Racket calls succeed; exit zero does not mean audited targets are clean. Inspect each JSON finding. The two target generators remain unmodified. Manual counterexamples explicitly distinguish validator acceptance and documented rule domain from actual ordinary sampler support.

## Handoff and packaging

Read the return-root REVIEW.md, DECISIONS.md, QUESTION_ANSWER.md, AUDIT.md and RESULTS.json. Before/intermediate/final evidence labels are intentional. Historical failed sources are retained under checks/historical-sources. New runs must use final source hashes rather than reusing old receipts.

Generated runtimes under `repo/var` are local disposable work products, not allowed source edits. Move those directories outside `repo` before invoking `package_return.py` (keep your check logs and manifests). Do not place runtime copies into the return. Keep the original assignment, audit assignment, baseline and canonical ledger unchanged.

If generator bytes change, preserve the current solve as prior evidence and prepare a new solve episode. Do not relabel the existing episode as fresh for another hash. Masked solve correctness remains withheld. Maintainer verification/approval is a separate step.
