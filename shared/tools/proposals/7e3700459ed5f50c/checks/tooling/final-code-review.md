# Independent selected-task code review

## Verdict and findings

**Accept the reviewed implementation within its stated canonical-repair and proposed-prototype scopes.** No Critical, Important, or Minor functional/reproducibility defects were found. This is an independent code review, not production approval or training admission. Source files were not changed by the reviewer.

## Scope and basis

Reviewed the exact selected task `7fc158ab7b70`, comparing `WORK/.review/baseline/repo/generators/7fc158ab7b70/generator.py` with `WORK/repo/generators/7fc158ab7b70/generator.py`; the new `tests/test_seed_contract.py`; and `workspace/parametric/scaling.py`, its README, and `tests/test_parametric_scaling.py`. Requirements were read from `WORK/checks/tooling/implementation-plan.txt`, `WORK/ARC-DESIGN.md`, and `WORK/PARAMETRIC-RULES.md`. The implementation plan still had pending checkboxes when read; conclusions below follow the actual source and executions, not that checklist.

References below are relative to `WORK/repo/generators/7fc158ab7b70/`:

- `generator.py:113-129`: the entire production change is a two-line strict `type(seed) is int` guard before the existing implementation. It rejects booleans and other non-int values without changing the RNG/version or any path reached by an actual int seed. The source diff contains no other production edit.
- `tests/test_seed_contract.py:10-24`: direct non-int rejection across all four difficulty choices, plus negative, zero, normal, and large integer seeds. These tests check determinism and lawfulness; the independent baseline comparison below additionally checks exact compatibility.
- `workspace/parametric/scaling.py:29-65,117-153,211-269`: bounded six-setting domain; canonical default `cells/both`; independent rule/input RNG streams; one fixed setting per episode; lawful inputs; distinct input sampling with explicit failure; default three demonstrations and four queries.
- `workspace/parametric/scaling.py:100-114,156-199,221-252`: matching Racket programs execute through the included bridge. Python predictions check those outputs, rather than supplying authoritative labels. The unchanged canonical callable is separately executed on every input.
- `workspace/parametric/scaling.py:202-208,225-248`: demonstrations alone select the surviving rule. All six rivals are evaluated and recorded for each query after fixing that survivor set. The finite inventory limitation is explicit.
- `workspace/parametric/scaling.py:272-274,301-334`: public JSON has only demonstration input/output pairs and query inputs; private evidence binds parameters, labels, exact Racket, runtime identity, source/file hashes, and command.
- `workspace/parametric/README.md:60-130`: documents the exact wrapper/payload invocation, setting/count controls, authority, public/private split, bounded evidence, and output-directory requirement.

The selected ledger and archival authority were compared byte-for-byte with the baseline and were unchanged. Shared runtime code was read only to understand bridge execution and portability; in particular, `_task_test_snapshot` copies the selected task workspace beside its tests. No shared implementation change is being reviewed here.

## Independently observed checks

All commands below ran with working directory `/workspace/scratch/4bbe6d6743f0/arc-review`. Wrapper and payload interpreters were explicit absolute paths. No official `arcpuzzles check`, full runtime copy, apply, or integration operation was run by this reviewer.

### Selected task tests

Exact command:

```bash
/workspace/scratch/4bbe6d6743f0/arc-review/WORK/.venv/bin/python /workspace/scratch/4bbe6d6743f0/arc-review/review.py run /workspace/scratch/4bbe6d6743f0/arc-review/WORK/.venv/bin/python -m pytest -q -p no:cacheprovider generators/7fc158ab7b70/tests/test_seed_contract.py generators/7fc158ab7b70/tests/test_generator_7fc158ab7b70.py generators/7fc158ab7b70/tests/test_parametric_scaling.py
```

Observed exit code: **0**. Observed output:

```text
effective cwd: /workspace/scratch/4bbe6d6743f0/arc-review/WORK/repo
Payload paths are relative to repo; use generators/TASK/..., not repo/generators/TASK/...
.............................................................            [100%]
61 passed in 12.22s
```

This runs 36 seed-contract cases, 13 existing canonical tests, and 12 prototype tests, including actual Racket bridge execution for all six settings at seed 17 and a separate seed 41 episode with four demonstrations/five queries.

### Exact integer-seed baseline compatibility and authority bytes

Exact command:

```bash
/workspace/scratch/4bbe6d6743f0/arc-review/WORK/.venv/bin/python /workspace/scratch/4bbe6d6743f0/arc-review/review.py run /workspace/scratch/4bbe6d6743f0/arc-review/WORK/.venv/bin/python - <<'PY'
import hashlib, importlib.util, json
from pathlib import Path
root = Path.cwd()
baseline = root.parent / '.review/baseline/repo'
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec); spec.loader.exec_module(obj)
    return obj
old = module('review_old', baseline / 'generators/7fc158ab7b70/generator.py')
new = module('review_new', root / 'generators/7fc158ab7b70/generator.py')
integer_cases=0
for seed in (-2**90, -17, 0, 991, 2**80+1):
    for difficulty in (None,'easy','medium','hard'):
        for index in range(27):
            assert old.generate(seed,index,difficulty=difficulty)==new.generate(seed,index,difficulty=difficulty),(seed,index,difficulty)
            integer_cases += 1
for grid_n in (3,4,5):
    for n_cells in range(2,7):
        for unique in (False,True):
            for anchor in (False,True):
                kw=dict(grid_n=grid_n,n_cells=n_cells,unique_colors=unique,anchor_origin=anchor)
                assert old.generate(-31,9,**kw)==new.generate(-31,9,**kw)
                integer_cases += 1
for name in ('shared/data/canonical/puzzles.jsonl','shared/data/base/solutions/training/ac0a08a4__7fc158ab7b70.json'):
    assert (root/name).read_bytes()==(baseline/name).read_bytes(),name
print(json.dumps({'integer_seed_parity_cases':integer_cases,'canonical_authority_bytes_unchanged':True}))
PY
```

Observed exit code: **0**. Observed result:

```json
{"integer_seed_parity_cases": 600, "canonical_authority_bytes_unchanged": true}
```

This used common unchanged runtime dependencies to compare the two source modules directly. It is finite execution evidence; the two-line source diff is the additional basis for preservation of all previously successful actual-int calls.

### Retained six-setting evidence

Independently parsed `WORK/checks/parametric/six-settings-seed17/manifest.json` and every setting's `public.json`, `private.json`, and `rule.rkt`; did not rely on `validation.json` assertions. Verified:

- Every manifest prototype source hash matches the currently reviewed source.
- Public/private file hashes and exact Racket text/hash match their receipts.
- Each of the six settings retains exactly three demonstrations and four queries; all seven inputs in an episode are distinct and public/private inputs align.
- Public schemas are exactly `train/test`, demonstration `input/output`, and query `input`.
- Every retained output independently matches direct row/column index replication using the declared cell/color count.
- Every episode has one declared demonstration survivor, exactly four query receipts, six predictions per query, and no surviving disagreeing rival.

All assertions passed with exit code 0. The retained suite reports 49 Racket evaluations; actual Racket execution was separately re-exercised by the 12 prototype tests above. No claim is made that the independent JSON audit itself executes Racket.

## Source identities

Paths below are relative to `WORK/`; SHA-256:

```json
{
  ".review/baseline/repo/generators/7fc158ab7b70/generator.py": "82870834ac6e72252cbf4764dcd3f78bd65d263c9e025dc789717cca8218823b",
  "repo/generators/7fc158ab7b70/generator.py": "9070d806a5720ecc39eae06c4294c338f5a7afb564e0c89ad36af898fbd6369f",
  "repo/generators/7fc158ab7b70/tests/test_seed_contract.py": "bf6d30e7be9dd5db96a08b88b7250795ea64cf8a8b3a48700defd87d00fae82e",
  "repo/generators/7fc158ab7b70/tests/test_parametric_scaling.py": "9f2ceaec4ae828326170d54b40a0d90d2f71f7276fb233002213f6c7421dc344",
  "repo/generators/7fc158ab7b70/workspace/parametric/scaling.py": "e5cd6ac8917a33bba7aeba2fd89fc2779fc031212bf81c93e7263547a0313ff4",
  "repo/generators/7fc158ab7b70/workspace/parametric/README.md": "0cc01c8196a622d9aec1109208a4f1f2c722c0839b537952504921531771dadf",
  "repo/shared/data/canonical/puzzles.jsonl": "9d46eb627dac0d3f096b8b1a63dd95e012039cf72d0d08f3d1bbbc109211965f",
  "repo/shared/data/base/solutions/training/ac0a08a4__7fc158ab7b70.json": "699ab1f2a05849900d784746ba7e1b318275c3d2f6203fad6212a202f48599ca",
  "checks/parametric/six-settings-seed17/manifest.json": "6c4dc801c9d3a1b5c3aad60b127b169b5cf6a78081a192f60b9bc1b8f6a0056e"
}
```

## Declined to judge / limitations

- No universal identifiability claim beyond the six declared parameter settings; no exhaustive random-seed/input-space claim. The prototype appropriately states both limits.
- No new independent twelve-stage battery or official isolated `task_tests` execution in this review. Root is handling the required isolated check separately. The command above exercised the complete selected test set in the packet checkout without copying a runtime.
- No relocated-checkout/integration/package verification in this review; those remain root's work. Reading the snapshot-copy implementation is not a substitute for executing a relocated check.
- No audit verdict for the two separately assigned audit tasks, native seed-journal/recovery tooling, full-library completeness, or unrelated source changes.
- No approval, training-admission, model-mastery, difficulty-calibration, or corpus-coverage decision follows from this review.
