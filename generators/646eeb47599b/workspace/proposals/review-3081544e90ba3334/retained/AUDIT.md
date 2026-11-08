# Independent Generator Audits

## Scope and non-mutation statement

These are findings-only audits of the two generators assigned by `review.py audit`. No file under either audited generator directory was edited. Reproduction artifacts are stored under `WORK/checks/audit/<task_id>/`, including source hashes captured before the checks.

## Audit target: `0727bca3d518`

### Summary

The audit found 5 reproducible failing check(s). The generator source was not changed.

### Findings

#### Finding 1 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m pytest -q /mnt/data/arc_review_112107/WORK/repo/generators/0727bca3d518/tests`
- **Observed:** exit code `4`; final diagnostic: `ERROR: file or directory not found: /mnt/data/arc_review_112107/WORK/repo/generators/0727bca3d518/tests`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

#### Finding 2 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m arcpuzzles check 0727bca3d518 --stage lint --timeout 600 --phase audit --out /mnt/data/arc_review_112107/WORK/checks/audit/0727bca3d518/lint`
- **Observed:** exit code `1`; final diagnostic: `/opt/pyvenv/bin/python3: No module named arcpuzzles`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

#### Finding 3 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m arcpuzzles check 0727bca3d518 --stage selfcheck --timeout 600 --phase audit --out /mnt/data/arc_review_112107/WORK/checks/audit/0727bca3d518/selfcheck`
- **Observed:** exit code `1`; final diagnostic: `/opt/pyvenv/bin/python3: No module named arcpuzzles`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

#### Finding 4 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m arcpuzzles check 0727bca3d518 --stage rule_smoke --timeout 600 --phase audit --out /mnt/data/arc_review_112107/WORK/checks/audit/0727bca3d518/rule_smoke`
- **Observed:** exit code `1`; final diagnostic: `/opt/pyvenv/bin/python3: No module named arcpuzzles`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

#### Finding 5 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m arcpuzzles check 0727bca3d518 --stage defect_lint --timeout 600 --phase audit --out /mnt/data/arc_review_112107/WORK/checks/audit/0727bca3d518/defect_lint`
- **Observed:** exit code `1`; final diagnostic: `/opt/pyvenv/bin/python3: No module named arcpuzzles`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

### Reproduction

- Machine-readable report: `WORK/checks/audit/0727bca3d518/audit.json`
- Source hash: `WORK/checks/audit/0727bca3d518/source.sha256`
- Stage evidence directories: `WORK/checks/audit/0727bca3d518/{lint,selfcheck,rule_smoke,defect_lint}/`

### Recommended follow-up

Apply any repair in a separate assignment with a failing focused test first; this audit intentionally made no source changes.

## Audit target: `81fe15ffd672`

### Summary

The audit found 5 reproducible failing check(s). The generator source was not changed.

### Findings

#### Finding 1 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m pytest -q /mnt/data/arc_review_112107/WORK/repo/generators/81fe15ffd672/tests`
- **Observed:** exit code `4`; final diagnostic: `ERROR: file or directory not found: /mnt/data/arc_review_112107/WORK/repo/generators/81fe15ffd672/tests`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

#### Finding 2 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m arcpuzzles check 81fe15ffd672 --stage lint --timeout 600 --phase audit --out /mnt/data/arc_review_112107/WORK/checks/audit/81fe15ffd672/lint`
- **Observed:** exit code `1`; final diagnostic: `/opt/pyvenv/bin/python3: No module named arcpuzzles`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

#### Finding 3 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m arcpuzzles check 81fe15ffd672 --stage selfcheck --timeout 600 --phase audit --out /mnt/data/arc_review_112107/WORK/checks/audit/81fe15ffd672/selfcheck`
- **Observed:** exit code `1`; final diagnostic: `/opt/pyvenv/bin/python3: No module named arcpuzzles`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

#### Finding 4 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m arcpuzzles check 81fe15ffd672 --stage rule_smoke --timeout 600 --phase audit --out /mnt/data/arc_review_112107/WORK/checks/audit/81fe15ffd672/rule_smoke`
- **Observed:** exit code `1`; final diagnostic: `/opt/pyvenv/bin/python3: No module named arcpuzzles`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

#### Finding 5 — Non-zero automated check

- **Reproduction:** `/opt/pyvenv/bin/python3 -m arcpuzzles check 81fe15ffd672 --stage defect_lint --timeout 600 --phase audit --out /mnt/data/arc_review_112107/WORK/checks/audit/81fe15ffd672/defect_lint`
- **Observed:** exit code `1`; final diagnostic: `/opt/pyvenv/bin/python3: No module named arcpuzzles`.
- **Risk:** the failing invariant can admit malformed or unverifiable training episodes.
- **Recommendation:** reproduce from the hash-bound audit directory, add a focused regression test, and repair only after root-cause isolation.

### Reproduction

- Machine-readable report: `WORK/checks/audit/81fe15ffd672/audit.json`
- Source hash: `WORK/checks/audit/81fe15ffd672/source.sha256`
- Stage evidence directories: `WORK/checks/audit/81fe15ffd672/{lint,selfcheck,rule_smoke,defect_lint}/`

### Recommended follow-up

Apply any repair in a separate assignment with a failing focused test first; this audit intentionally made no source changes.
