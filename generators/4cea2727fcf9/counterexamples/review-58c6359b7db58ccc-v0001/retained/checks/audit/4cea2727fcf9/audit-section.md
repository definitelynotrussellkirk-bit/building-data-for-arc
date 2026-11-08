## Findings-only audit: 4cea2727fcf9

**Reproduced unresolved teaching defect: five generated demonstrations can leave an ignore-portals rival alive when the query requires portals.** Audited source: `repo/generators/4cea2727fcf9/generator.py`, SHA-256 `91f94df8b2a448ccf8556bf788465ffa9faa1cc765baacbc692c6f2d6a9499a9`. This independently confirms the existing source-bound unresolved finding; it is not a new distinct audit claim or a source repair.

The minimal replay uses seed `22`, difficulty `medium`, demonstration sample indices `0..4`, and query index `5`. Every input passes the target's own `self_check`. The canonical Racket program and a rival differing only by replacing the `portal-exit` definition with `(define (portal-exit p) p)` give identical outputs on all five demonstrations. Demonstrations 2 and 4 each contain two portals, but the rival still fits; portal presence alone does not identify their behavior. On query 5, which also contains two portals, the executed outputs differ at seven cells. The canonical authority also reproduces all four retained canonical input/output pairs in this fresh run. All output comparisons use the included live Racket bridge, rather than a Python-only rule mirror.

Evidence is `checks/audit/4cea2727fcf9/replay.json`; the compact, exact-source-guarded reproducer is `checks/audit/4cea2727fcf9/replay.py`. The JSON retains the six inputs, canonical/rival outputs, input/program hashes, exact programs, validation results, and Racket runtime identity. Reproduce from the outer extraction directory:

```bash
PYTHONDONTWRITEBYTECODE=1 WORK/.review/test-venv/bin/python review.py run /workspace/scratch/221090e9e150/arc_review/WORK/.review/test-venv/bin/python ../checks/audit/4cea2727fcf9/replay.py
```

**Additional concrete axis-honesty failure.** At the same seed and demonstration index 0, the baseline has five distinct colors. Each of six calls overriding `palette_kind="warm"`, `palette_size=3`, `palette_size=6`, `n_distinct_colors=3`, `n_distinct_colors=6`, or `texture="varied"` returns the identical grid. In particular, explicit color-count overrides of 3 and 6 both silently produce the same five-color input. Source inspection agrees: these helpful palette/count controls are declared in `AXES` but never drawn or consumed; helpful `texture` values likewise do not alter generation. Exact finite probe results are included in `replay.json`. This finding concerns the declared controls, independently of canonical BFS output correctness.

**Required strict audit preset: failed, with both requested stages completed and no timeout.** `task_tests` exited 5 because no task-local or selected frozen tests exist; `semantic_gate` exited 2 because no `strict_canonical_like`, `SEMANTIC_WITNESSES`, or `lesson_identifiable` contract is declared. Overall exit was 1. This is a completed failed audit, not passing verification or a missing-runtime result. See `checks/audit/4cea2727fcf9/strict/result.json` and `checks/audit/4cea2727fcf9/strict/checks/4cea2727fcf9_audit_semantic_gate.log`.

```bash
PYTHONDONTWRITEBYTECODE=1 WORK/.review/test-venv/bin/python review.py run /workspace/scratch/221090e9e150/arc_review/WORK/.review/test-venv/bin/python -m arcpuzzles check 4cea2727fcf9 --stage audit --phase audit --timeout 1800 --out ../checks/audit/4cea2727fcf9/strict
```

`checks/audit/4cea2727fcf9/invocation.json` records exact argv, cwd, environment setting, exit statuses, unchanged source hash, preserved audit-assignment seed, finite summaries, and key evidence hashes. This audit changed no target generator, tests, notes, contracts, shared interfaces, or parametric files and used no blind-solve material. Its scope is this one constructed six-input lesson, four canonical pairs, six explicit control probes, and the strict preset; it measures no population failure frequency. A likely repair is to require an actual portal-rival counterexample in each lesson and either implement or remove dead declared controls. The peer source and existing unresolved audit remain unchanged.
