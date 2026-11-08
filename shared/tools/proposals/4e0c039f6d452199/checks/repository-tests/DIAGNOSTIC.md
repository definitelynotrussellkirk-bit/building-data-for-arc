# Repository test failure diagnostic

All four broader repository failures reproduce on the untouched original packet. None requires the edited `48bda9528e71` generator. Three failures are stale test expectations; the fourth exposes a real assumption in shared process-liveness handling that fails in the present environment. The broader repository suite is therefore still failing, independently of the selected generator repair.

## Verification boundary

The original full-suite receipt records exit code 1, no timeout, and 219.601 seconds elapsed. Its pytest log reports **4 failed, 597 passed, 3 skipped, and 18 subtests passed in 218.70 seconds**. The three skips are the optional Torch tests in `tests/test_native_export.py`.

Exactly the four failed node IDs were rerun once on a fresh extraction of the original ZIP, before the selected-task delta was applied there. The focused baseline produced **4 failed in 7.33 seconds**, with the same assertion failures and observed values. Its wrapper receipt records exit code 1, no timeout, and 8.342 seconds elapsed.

| Run | Actual wrapper working directory | Effective pytest working directory | Selected generator SHA-256 |
|---|---|---|---|
| Original broader run | `/workspace/scratch/df8d9659f825/review/WORK` | `/workspace/scratch/df8d9659f825/review/WORK/repo` | `fa8f82d356825247d12033364a9c6de885922c2d3829e2de75399d211516cae6` |
| Untouched focused baseline | `/workspace/scratch/df8d9659f825/fresh-replay/WORK` | `/workspace/scratch/df8d9659f825/fresh-replay/WORK/repo` | `102426f4ed3df872c33fa261f413057e45ceedbfa5e662b82a3017b56887e9cc` |

Both wrapper and payload used `/workspace/scratch/df8d9659f825/review/WORK/.venv-review/bin/python`. The payload was `-m pytest -q` followed by the four exact IDs in `pytest_node_ids.json`; the timeout was 180 seconds. `baseline-focused-receipt.json` preserves the exact argument vector and working directories. The log explicitly confirms the fresh repository as effective cwd.

No shared source, repository test, or generator was changed during this diagnostic. A final read-only probe confirms the main selected generator still has SHA-256 `fa8f82d356825247d12033364a9c6de885922c2d3829e2de75399d211516cae6`.

## Findings

### 1. Shared detached-job status misclassifies an unobservable process identity

**Failing node:** `tests/test_check_jobs.py::test_actual_detached_failure_wait_and_resume_reuses_checkpoint`.

The test installs a disposable shell battery for synthetic task `aaaa00000001`. Its first stage writes a successful lint checkpoint; its second stage deliberately exits 1. It expects `jobs.wait()` to return `stage_failed`, `stage_exit_code == 1`, and `resumable == True` before testing resume. Instead, both runs return `parent_interrupted_unclean` at the first assertion.

The relevant implementation is `/workspace/scratch/df8d9659f825/review/WORK/repo/src/arcpuzzles/check_jobs.py`:

- Lines 30–32 obtain process birth time by reading `/proc/{pid}/stat`; a missing path or parse failure becomes `None`.
- Lines 109–110 publish the worker's PID and this birth value in its running state.
- Lines 35–43 synthesize `parent_interrupted_unclean` whenever the current birth value is missing or differs from the recorded one.
- Lines 90–96 make `wait()` return immediately on that synthesized terminal status.

The retained artifacts show that the worker itself did not disappear. In both the original run and the fresh baseline, its final `state.json` is `stage_failed`, with `stage_exit_code: 1`, `resumable: true`, and `pid_birth: null`. Each supervisor log contains `checkpoint`, and each completed `check/result.json` records the intended fixture failure, with no timeout. The original worker PID was 781; the fresh worker PID was 14. These small files were copied into `diagnostic-evidence/original/` and `diagnostic-evidence/baseline/` so the evidence does not depend on pytest temporary-directory retention.

A separate read-only process probe identifies the underlying environment assumption. In the same Python execution environment:

| Observation | Parent probe | Child probe |
|---|---:|---:|
| `os.getpid()` | 2 | 5 |
| PID reported by `/proc/self/stat` | 30124 | 30127 |
| `/proc/{os.getpid()}/stat` | Missing: `FileNotFoundError` | Present, but reports PID 5 |
| `_birth(os.getpid())` | `None` | `"140"` |
| Birth value from `/proc/self/stat` | `"1728868"` | `"1728872"` |

The PID namespace exposed through `os.getpid()` does not match the mounted numeric `/proc` paths. A numeric path can be absent or resolve to a different process. Thus the current birth check can infer a dead worker from an unavailable or unrelated observation. The test's prematurely returned state and the later valid terminal state follow directly from that control flow.

**Dependency assessment:** none on `48bda9528e71`. The test uses only the synthetic fixture library and shared supervisor code. It reproduces with the original selected generator. This is the highest-priority follow-up among these four findings because it affects status and resume behavior, rather than only a test's expected value. A follow-up should distinguish unavailable identity evidence from proven supervisor termination and retain conservative resume behavior. This diagnostic makes no claim that the same failure occurs on a host with matching PID and `/proc` namespaces.

Test construction is at `/workspace/scratch/df8d9659f825/review/WORK/repo/tests/test_check_jobs.py`, lines 24–42, and `/workspace/scratch/df8d9659f825/review/WORK/repo/tests/test_check_resume.py`, lines 8–30. Process measurements and copied-file hashes are retained in `diagnostic_probe.json`.

### 2. The defba archival test compares a current sampler against a historical complete-pair fingerprint

**Failing node:** the `defba1ab4f90` parameter of `tests/test_archival_reference.py::test_archival_rule_access_matches_measured_historical_pairs`.

Both runs produce the same mismatch:

- Expected historical identity: `8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0`.
- Actual current identity: `b4ba8572d6971d19c012fe1d9e6c33122ab1c68d440a1a2286729fdc279c13db`.

At `/workspace/scratch/df8d9659f825/review/WORK/repo/tests/test_archival_reference.py`, lines 11–17 say the expectations were measured during the full v0.3 census against the retained original runner. Lines 32–35 generate one train and one test pair at seed 17, medium difficulty, using `reference="archival"`, then hash the complete resulting pairs. The test does not pin a historical generator.

Archival mode selects a reference bundle; it still invokes the current `module.generate`. That distinction is explicit in `/workspace/scratch/df8d9659f825/review/WORK/repo/src/arcpuzzles/worker.py`, lines 309–321. It cannot guarantee historical input bytes after a sampler replacement.

The packet already ships `defba1ab4f90` version 2.0.0, generator SHA-256 `4189136b4e863e70bf07ee2466d865493554544a72273e4f3918da61da7f7c26`. Its retained notes explain that an unrelated sparse 13×13 local-motif sampler was replaced with the canonical stream task, and selected base-authority records were synchronized. See `/workspace/scratch/df8d9659f825/review/WORK/repo/generators/defba1ab4f90/notes.md`, lines 9 and 21, with fuller rationale later in that file. These are inherited packet changes, not edits made during the selected repair.

**Cause and dependency assessment:** the frozen complete-pair expectation is stale for the generator and selected authority shipped in this packet. This is unrelated to `48bda9528e71`; the test directly requests a different task, and the untouched baseline produces the identical actual fingerprint. A future test correction must decide whether to pin a genuinely historical generator plus authority, or verify archival-reference behavior using the current sampler. Updating a hash alone would not clarify that contract.

### 3. The d982 self-check test depends on a validator defect that was already repaired

**Failing node:** `tests/test_archival_reference.py::test_archival_rules_still_enforce_generator_self_checks[d982cffd80f8]`.

The test generates at seed 17, medium difficulty, then requires an incidental `self_check:` rejection and excludes accepted sample index 0. Both runs fail the first condition. This expectation assumed that the sampler would continue producing at least one input rejected by its validator.

The packet's `d982cffd80f8` version 3.0.0 validator permits one to six fillable centers. Difficulty changes sampling preferences, not validity. The retained notes document the former inconsistency: medium generation allowed two or three centers while validation required exactly two. See `/workspace/scratch/df8d9659f825/review/WORK/repo/generators/d982cffd80f8/notes.md`, lines 15–19. The repaired validator is at `/workspace/scratch/df8d9659f825/review/WORK/repo/generators/d982cffd80f8/generator.py`, lines 229–249.

A focused direct check of the first two requested draws records:

| Seed | Sample index | Difficulty | Overrides | Dimensions | Fillable centers | `self_check` |
|---:|---:|---|---|---|---:|---|
| 17 | 0 | medium | `{}` | 5×15 | 3 | `[]` |
| 17 | 1 | medium | `{}` | 8×10 | 2 | `[]` |

The source hash for these measurements is `f8eacbfeab97db8e356ce5baac3097de8c62a04af64168f1f3f5445fa4974297`; input hashes are in `diagnostic_probe.json`. These observations check validator behavior only and make no new claim about labels.

The worker still calls the current generator's self-check before rule application, including in archival mode, and raises a rejection on any findings. See `/workspace/scratch/df8d9659f825/review/WORK/repo/src/arcpuzzles/worker.py`, lines 325–336. No self-check bypass is shown by this failure.

**Cause and dependency assessment:** the test requires the continued existence of a repaired generator/validator inconsistency. It should verify enforcement with a controlled failing checker or input, rather than relying on a particular production sampler to fail at a fixed seed. No selected-generator dependency exists; this directly requests another task and reproduces on the original packet.

### 4. The unsupported-platform Racket test expects an obsolete error string

**Failing node:** `tests/test_packet_racket_setup.py::test_system_runtime_must_pass_probe_on_unsupported_platform`.

The test mocks Darwin/arm64, a discovered system Racket path, and a failed probe with return code 1, empty stdout, and stderr `unusable runtime`. It expects the regex `Racket probe failed: unusable runtime`. The implementation correctly raises `RuntimeError`, but now emits richer diagnostics:

```text
Racket probe failed: returncode=1; stdout=''; stderr='unusable runtime'
```

The actual rejection is the intended behavior; the old contiguous error substring is absent. The assertion is at `/workspace/scratch/df8d9659f825/review/WORK/repo/tests/test_packet_racket_setup.py`, lines 70–78. The current formatting is at `/workspace/scratch/df8d9659f825/review/WORK/repo/src/arcpuzzles/review_full_packet_files/setup_racket.py`, lines 42–53; the unsupported-platform path calls that probe at lines 60–68.

**Cause and dependency assessment:** a stale regex following a diagnostic-format change. This test mocks the process result and does not execute an ARC generator or a real Racket binary. It therefore provides no evidence of a broken installed Racket runtime. The untouched baseline fails with the identical message.

## Evidence and replay files

All diagnostic deliverables are under `/workspace/scratch/df8d9659f825/review/WORK/checks/repository-tests/`:

- `pytest.log` and `receipt.json`: parent-owned original broader run.
- `pytest_node_ids.json`: the exact four node IDs, including the complete parameterized fingerprints.
- `baseline-focused.log` and `baseline-focused-receipt.json`: the four-test untouched-source reproduction, exact argv/cwd, exit status, timeout, and both selected-source hashes.
- `diagnostic_probe.py` and `diagnostic_probe.json`: two direct validator observations and one parent/child process-identity observation. The command was `.venv-review/bin/python -B checks/repository-tests/diagnostic_probe.py` from the main `WORK`; it exited 0. It did not run pytest, Racket, or any generator battery.
- `diagnostic-evidence/original/` and `diagnostic-evidence/baseline/`: copied supervisor state, request, log, and completed fixture result. Their source paths and SHA-256 hashes are in `diagnostic_probe.json`.

The focused baseline reproduced existing failures; it was not another full-suite run. No shared fix was attempted, no claim is made that the broader repository suite passes, and the selected generator's source hash was preserved.
