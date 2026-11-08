# Optional shared-tool proposal: process liveness from run ownership

This is a separately reviewable proposal for `src/arcpuzzles/check_jobs.py`. It has **not** been applied to the main review repository or the fresh replay repository, and it is not part of the selected `48bda9528e71` task delta.

The patch replaces an unreliable PID birth comparison with the supervisor's existing run-scoped lock. The isolated implementation passes **33 focused tests**, including the previously failing detached failure/resume test and **18 new regression cases**. The corresponding unchanged implementation failed 13 of the same 33 cases.

## Problem

The current supervisor obtains a process birth value from `/proc/{pid}/stat` and treats an unavailable or changed value as proof of an unclean supervisor exit. In the measured environment, `os.getpid()` and the numeric PID namespace mounted at `/proc` differ. A numeric path can be absent or can name an unrelated process. This caused `wait()` to return `parent_interrupted_unclean` while a real supervisor was still running; the worker subsequently wrote the correct completed failure and checkpoint state.

The original diagnosis, untouched-packet reproductions, and process measurements are preserved at `../repository-tests/DIAGNOSTIC.md`.

## Bounded repair

The worker already acquires `worker.lock` exclusively before publishing its PID and running state. It holds that lock through the final state write. The proposal uses that existing lifecycle invariant:

| Observation | Result |
|---|---|
| A nonblocking shared lock probe is blocked by the worker's exclusive lock | Preserve the reported state; this run still has an owner. |
| The shared probe succeeds, and a protected reread finds a terminal state | Return that terminal state with its existing exit code and resume eligibility. |
| The shared probe succeeds, and the protected reread remains unfinished with a published PID | Return `parent_interrupted_unclean`, with `resumable=False`. |
| No worker lock file exists for a published unfinished run | Return unclean and nonresumable. |
| Initial startup has not published a PID | Preserve the existing startup behavior. |
| A lock or I/O operation fails unexpectedly | Propagate the error; do not fabricate a liveness verdict. |

A **shared** probe is intentional: simultaneous status readers can coexist, so reader activity cannot be confused with exclusive worker ownership. Re-reading the state while holding the acquired lock handles a worker that finishes between the initial state read and the lock probe.

The recorded PID and birth remain diagnostic fields. A held run lock outranks absent, matching, or mismatched birth values. Conversely, a live unrelated process with the same numeric PID cannot substitute for the missing run lock. `_birth()` now returns `None` when `/proc/self/stat` does not agree with `os.getpid()`, preventing an unrelated numeric entry from being recorded as trustworthy birth metadata.

The patch adds no signals, process termination, PID polling fallback, runtime dependency, or new persistent file. Loss of worker ownership still does **not** authorize resume: surviving descendants remain possible.

## Platform scope

The existing module imports `fcntl`, and its runtime uses POSIX process groups. This proposal preserves that Unix platform boundary; it does not add Windows support. The actual integration run was performed on Linux in the environment with the reproduced PID namespace mismatch. Missing `/proc`, compatible `/proc`, and incompatible `/proc` behavior are also controlled regression cases. No actual macOS or BSD host run is claimed.

The Python documentation describes `fcntl` as Unix-only and notes that `flock` may be emulated using `fcntl`. The implementation recognizes the portable nonblocking contention errors `EACCES`, `EAGAIN`, and `EWOULDBLOCK`, while propagating unexpected failures. Reference: [Python fcntl documentation](https://docs.python.org/3/library/fcntl.html).

The run lock file must retain a stable inode throughout a run, and the filesystem must provide working advisory locking. Those requirements already apply to the existing exclusive worker lock. The proposal does not claim to repair externally deleted/replaced lock files, hostile state edits, or filesystems that do not honor locks.

## Test evidence

The test workspace was `/workspace/scratch/df8d9659f825/process-liveness-work`. It contains copied source and fixture files plus its own virtual environment and local test dependencies; it does not import source or packages from either review repository. The source copy contains about 0.6 MB of Python, documentation, tests, and the shell fixture dependency. No generator corpus or solve data was copied.

| Run | Implementation | Focused result | Exit | Timeout |
|---|---|---|---:|---|
| `before` | Unchanged shared module | 13 failed, 20 passed; 0 errors | 1 | No |
| `after` | Proposed shared module | 33 passed in 2.64 seconds | 0 | No |

The before run took 4.426 seconds including its wrapper; the after run took 2.882 seconds. Both used the same regression file hash and the same three test files:

```text
tests/test_check_jobs.py
tests/test_check_resume.py
tests/test_check_jobs_liveness.py
```

The 18 new cases cover actual ownership held by a separate live process, real process exit without a final state, missing and incompatible `/proc`, matching/mismatched/missing birth metadata, a live unrelated PID in stale state, an absent lock file, completion during the status probe, concurrent shared readers, portable lock contention, unexpected lock errors, startup, and diagnostic birth capture.

The recycled-PID risk is modeled by pointing stale unfinished state at an actually live unrelated process and varying its reported identity. No artificial operating-system PID reuse cycle was forced. Real subprocess execution, checkpoint retention, and successful resume are exercised by the unchanged detached-job integration test.

The first workspace run exposed one omitted copied fixture dependency: `shared/tools/run_generator_battery.sh`. That initial run is retained as `setup-baseline.log`, `.xml`, and `-receipt.json` (14 failures, 19 passes, including the fixture-copy failure). The original shell file was then copied, without implementation changes, before the reported `before` run. The shell integration test uses synthetic inexpensive gate commands; no corpus battery was run.

No full repository suite was repeated. The other three inherited broader-suite failures described in the repository diagnostic were outside this proposal and were not changed.

## Source binding and review

| File | SHA-256 |
|---|---|
| Unchanged `check_jobs.py` | `a561721b48b0c4ebe04566de0e80213decc2a4a0acde84d3ba9e4fc7462fea6b` |
| Proposed `check_jobs.py` | `d0e7853988bbee0d427b112a09130eda8e385f4824c7951600b91290efba261f` |
| New regression file | `0e0727e9d1e00bb7fe2210a34694132c1a52cd37ac8a54eeede55aa199c0ca55` |
| Preserved main `48bda9528e71/generator.py` | `fa8f82d356825247d12033364a9c6de885922c2d3829e2de75399d211516cae6` |

An independent agent reviewed the proposed lifecycle, actual implementation diff, and regression tests, and found no blocking race or correctness issue in this scope. That review was read-only and did not independently execute tests. The recorded passing run was executed by the implementing diagnostic agent.

## Files and optional application

- `process-liveness.patch`: the complete proposal, touching only the shared module and adding the regression test file.
- `test_check_jobs_liveness.py`: a standalone copy of the regression file for inspection.
- `check_jobs.before.py` and `check_jobs.after.py`: exact implementation snapshots.
- `before.log`, `after.log`, their JUnit XML, and their receipts: actual commands, cwd, environment overrides, source hashes, elapsed time, and exit status.
- `source-manifest.json`: copied source files, hashes, and local test dependency versions.
- `run_focused.py`: the exact bounded evidence runner used in this session.
- `verification_commands.json`: consolidated test receipts and patch applicability/hash verification.

From the root of a separately authorized checkout containing the unchanged shared module, review and apply with:

```bash
git apply --check /path/to/process-liveness.patch
git apply /path/to/process-liveness.patch
PYTHONPATH=src PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python -B -m pytest -q tests/test_check_jobs.py tests/test_check_resume.py \
  tests/test_check_jobs_liveness.py
```

The supplied patch was also checked and applied to a separate scratch copy of its original source, then the resulting implementation and regression hashes were compared with the tested files. This applicability check did not modify the active review or fresh replay repository.
