# Reusable review tools

The selected implementation is `../generator.py`. Nothing here is automatically selected as a generator.

## Exact-control census

`probe_exact_controls.py` enumerates all 4,800 advertised height/width/target-count combinations. It checks realized geometry, an independent structural count, `self_check`, explicit capacity-rejection metadata, and six repeated deterministic draws. It writes a compact source-bound JSON report and refuses to overwrite an existing output.

From the packet's `repo` directory, with the reviewer virtual environment prepared:

```bash
../.venv-review/bin/python generators/1e99030a2d90/workspace/probe_exact_controls.py --band medium --seed 17 --sample-index 9 --out ../checks/exact-controls-new.json
```

Use `--generator PATH` to test an alternate or baseline source without replacing the selected implementation. `--band`, `--seed`, and `--sample-index` make the selected sweep explicit. The source locator uses `reviewer_support.find_root` and handles both library and copied runtime layouts.

The probe is a sampler/interface test. Its Python structural oracle is not an authoritative labeler, and its capacity expectation describes this sampler's disjoint-slot design, not the full legal input domain.

## Focused regression suite

From WORK, run the supported isolated task-test stage:

```bash
.venv-review/bin/python run_with_racket.py ../.venv-review/bin/python -m arcpuzzles check 1e99030a2d90 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-new
```

The wrapper starts in WORK but runs its payload from WORK/repo; the payload's relative interpreter path therefore starts with `../`. The 58 cases include exact boundaries, rejected controls, canonical acceptance, counterexample semantics, and the previously failing query-only color case.

For authoritative labels, use the public `arcpuzzles apply` command. The two counterexample JSON files next to this workspace preserve exact reference outputs, rival outputs, source hashes, and their provenance. The full review return additionally preserves battery reports, lesson censuses, both solves, and both separate audit findings.
