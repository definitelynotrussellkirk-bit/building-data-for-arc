## 5cff0d794bdf

**Reproduced generator API contract defects; no accepted-input semantic failure found in the bounded Racket check. Target source and approvals were left unchanged.**

Audited generator v2.0.1, SHA-256 `b6ba414e0be2f73cd50ba150644a5039c190c831aba2339dcb03026182249493`. Canonical source SHA-256 is `58366c2a42a0295c05c075dc0f78d1947b3be3f7ea211756496cd21d7b5405da`; the public runner executed rule hash `58366c2a42a0` with `rule_hash_matches_catalog=true`. The generator has no `RULE_HASH` declaration. This audit does not edit or reconcile authority records.

### Reproduced findings

**Advertised integer ranges are rejected.** At seed `12345`, sample index `7`, difficulty `medium`, all seven tested calls using advertised valid values raise `ValueError`: `{grid_h:8, grid_w:9}`, `grid_h=4`, `grid_h=24`, `grid_w=3`, `grid_w=18`, `cols=1`, and `cols=12`. The declarations promise height `4..24`, width `3..18`, and active-column count `1..12`; generation instead enforces the narrower default ranges `9..14`, `7..10`, and `3..5`. The first call fails with `draw_int('grid_h'): override 8 outside [9, 14]`. This is especially concrete because canonical train pair 0 is 8×9 and passes the selected `self_check`. The `cols=12` declaration also exceeds the nine distinct nonzero ARC colors available under the generator's distinct-color-per-column invariant; this audit did not treat that call as a feasible joint-domain construction.

**Ignored controls remain unfixed.** The current `review_index.json` already retains a `needs_triage` ignored-control finding on these exact source bytes. This audit freshly reproduced and extended it: ten calls produce the exact baseline grid, all pass `self_check`, and all contain three nonzero colors despite count requests of one or nine. Calls are `palette_kind="warm"`, `palette_kind="not-a-declared-kind"`, `palette_size=1/9`, `n_distinct_colors=1/9`, `density="dense"`, `position_bias="rows"`, `texture="warm"`, and unknown `unknown_axis=3`. Baseline grid SHA-256 is `37a510ae16f678230a4dc8dc109a4d15a1248d907efa03e94678573a8889bd66` using compact JSON grid serialization. Valid controls collapse to duplicates; invalid values and unknown keys are silently accepted. This is a generator API/coverage defect, not a wrong Racket label.

Suggested future repair: expose only controls that are consumed and observable, reject unknown or invalid values, and either implement each advertised range constructively or narrow its declaration honestly. Distinguish default difficulty preferences from legal override bounds. No changes were made during this audit.

### Semantic and teaching scope

The public reference run checked all **5 canonical labeled pairs**, **12 normal generated inputs** (seeds `0, 1, 17, 12345`; sample index `7`; each of `easy`, `medium`, and `hard`), and **2 guard-condition diagnostics**, for **19 inputs total**. Racket matched the independent guarded column-fill mirror on **19/19**. The first 17 inputs passed the selected domain checker; there were **0/17 accepted-domain rule disagreements**.

A rival that fills from the first to last nonzero cell in every active column, without checking marker count or matching colors, fits **5/5 canonical pairs and 12/12 generated inputs**. The constructor always supplies exactly two same-color markers, so ordinary scenes do not exercise these guards. Two mutations of canonical train pair 0 establish the difference: change cell `(6,1)` from 2 to 9, or add a third color-2 marker at `(2,1)`. Racket leaves that column unfilled while the rival fills it. Both mutations are explicitly **outside the current generator domain**: `self_check` rejects mismatching colors or three markers. These are a bounded teaching-coverage observation and potential future domain-extension fixtures; they are **not accepted-input semantic counterexamples**.

### Evidence and actual commands

Evidence: `checks/audit/5cff0d794bdf/probe.json`, `input.json`, `racket.json`, `verification.json`, `commands.json`, and `reproduce.py`. The small reproducer loads the exact selected generator with the public `reviewer_support.load_selected_generator` API and asserts the assigned source hash. `racket.json` records each input/output hash and each independent generator-domain verdict; `verification.json` records receipt hashes and the comparison counts.

All three commands below ran from `/workspace/scratch/64d6d4b955d5/review_work/WORK/repo` and exited **0**. The wrapper's effective directory was the same repository:

```bash
python3 /workspace/scratch/64d6d4b955d5/review_work/WORK/run_with_racket.py /workspace/scratch/64d6d4b955d5/review_work/WORK/.venv-review/bin/python ../checks/audit/5cff0d794bdf/reproduce.py build
python3 /workspace/scratch/64d6d4b955d5/review_work/WORK/run_with_racket.py /workspace/scratch/64d6d4b955d5/review_work/WORK/.venv-review/bin/python -m arcpuzzles apply 5cff0d794bdf --input ../checks/audit/5cff0d794bdf/input.json --reference canonical --check-generator-domain --timeout 120 --out ../checks/audit/5cff0d794bdf/racket.json
python3 /workspace/scratch/64d6d4b955d5/review_work/WORK/run_with_racket.py /workspace/scratch/64d6d4b955d5/review_work/WORK/.venv-review/bin/python ../checks/audit/5cff0d794bdf/reproduce.py verify
```

No full battery, target test suite, exhaustive override sweep, or lesson census was run. No target-local test directory was present. The findings above are freshly reproduced finite evidence, not a new approval or a claim of complete semantic coverage.
