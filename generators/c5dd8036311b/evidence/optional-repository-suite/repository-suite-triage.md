# Repository pytest triage

**The repository suite failed: 17 failed, 1,002 passed, 3 skipped, and 18 subtests passed in 774.22 seconds; exit code 1.** No global pass is claimed.

## Command and scope

Run from `WORK/`:

```bash
python3 run_with_racket.py /workspace/scratch/27882fecf88e/packet/WORK/.venv/bin/python -m pytest -q > checks/regression/repository-tests.log 2>&1
```

The wrapper's effective cwd was `WORK/repo/`. The parent confirmed this command and terminal return code from execution session 69032. The suite was launched while the selected generator was being finalized, so it is not an atomic final-source verification. `repo/pyproject.toml` sets `testpaths = ["tests"]`; the selected task's own tests are checked separately.

## Failure categories

| Category | Failures | Assessment |
| --- | ---: | --- |
| process_identity_and_resume | 12 | Environment assumption mismatch is directly supported: os.getpid and /proc/self/stat disagree. Runtime deliberately declines to infer liveness or safe resume under this condition. |
| archival_pair_golden | 1 | The supplied test's historical golden disagrees with its supplied generator/archival selection. Relevant test, generator, runner, canonical ledger, authority maps, and both retained authority files match packet hashes. No selected-task regression is identified. |
| archival_rejection_expectation | 1 | The test assumes this exact draw must reject an input. Failure of that assertion alone does not prove self-checks were bypassed. Relevant shipped sources and authority files are unchanged. |
| setup_diagnostic_expectation | 1 | Exact source/test wording mismatch within unchanged packet bytes. The test did receive a RuntimeError for the unusable mocked runtime. |
| battery_command_expectation | 1 | Exact source/test command expectation mismatch within unchanged packet bytes, using a synthetic aaaa00000001 fixture rather than the selected generator. |
| socket_creation_policy | 1 | Independently reproduced environment restriction; HTTP request handling was not exercised by this failing case. |

The process-table cause is directly supported by a separate read-only probe: `os.getpid()` returned **2**, while `/proc/self/stat` reported **57308**. The runtime explicitly treats this mismatch as unsupported process identity and returns `liveness_unknown` rather than assuming a process is dead or safe to resume. Four signal tests fail their initial `live(pid)` assertion before they send the signal, so those failures do not establish a signal-cleanup defect. A separate socket-construction probe also reproduced `PermissionError: [Errno 1] Operation not permitted`.

The two textual expectation mismatches are specific: the Racket probe error now includes returncode/stdout/stderr fields, and the battery command includes `--time-budget 310`. Both corresponding tests and implementation files match the supplied packet. The archival digest failure concerns `defba1ab4f90`; the missing expected rejection concerns `d982cffd80f8`. Their shipped generator, runner, authority selection, and relevant data bytes were also compared. Determining whether those historical expectations or prior generator behavior should change remains an owner task.

## Frozen tests and selected-task assessment

SHA-256 comparison with `PACKET-MANIFEST.json` verified **92/92 root repository test files**, **28/28 shared test files**, and **17/17 failure-relevant implementation/data files** unchanged. There were no mismatches or missing files in those groups. The intentionally migrated task-local file is outside these frozen groups.

No failed node or explicitly exercised generator points to `c5dd8036311b`; this triage identified no actionable selected-task regression. That statement does not erase the global failures or replace the task's final portable test stage. No earlier full-suite run or original-snapshot pytest rerun was compared. The evidence establishes unchanged bytes and the current failures, not a historical pass/fail result.

The three skips are optional PyTorch-dependent native-export cases because `torch` is not installed.

## Evidence and reproducibility

The complete log remains `checks/regression/repository-tests.log`. `repository-suite-triage.json` lists all 17 exact node IDs, category reasoning, commands, counts, context cautions, and evidence hashes. `repository-source-comparison.json` retains every compared path/hash. `repository-environment-probe.json` retains the separate PID/socket observations.

Reproduce this read-only triage from `WORK/` with:

```bash
/workspace/scratch/27882fecf88e/packet/WORK/.venv/bin/python checks/analysis/triage_repository_suite.py
```

No generator, shared implementation, root test, or frozen fixture was edited during this triage. The output remains a failed global suite, with environment limitations and unresolved archival expectations explicitly retained.
