# Repository suite result and limitations

The final repository suite **did not pass**: **5 failed, 596 passed, 3 skipped, and 18 subtests passed**, in **219.75 seconds**, with reported process exit status **1**. The final summary and effective working directory are recorded in `checks/repository-tests-final.log`. A machine-readable comparison and selected underlying diagnostic evidence are retained in `checks/repository-suite-analysis.json`, including SHA-256 hashes of both suite logs.

## Exact failing nodes and direct causes

| Failing node ID | Evidence and direct cause | Relation to task `899e2a4cfac9` |
| --- | --- | --- |
| `tests/test_archival_reference.py::test_archival_rule_access_matches_measured_historical_pairs[defba1ab4f90-8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0]` | Historical episode identity mismatch at test line 35: expected `8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0`, observed `b4ba8572d6971d19c012fe1d9e6c33122ab1c68d440a1a2286729fdc279c13db`. Both suite logs show the same values. Whether the historical expectation or that task's current generated episode is wrong was not determined. | Different task: `defba1ab4f90`; historical snapshot assertion. |
| `tests/test_archival_reference.py::test_archival_rules_still_enforce_generator_self_checks[d982cffd80f8]` | At test line 47, the generated row contains no rejection reason with the required `self_check:` substring. The test expects that seed 17, medium difficulty, archival generation must encounter such a rejection. Both suite logs fail at this same assertion. This does not establish that self-check execution was bypassed; a draw can pass without a rejection. | Different task: `d982cffd80f8`; fixed-seed archival rejection expectation. |
| `tests/test_check_jobs.py::test_actual_detached_failure_wait_and_resume_reuses_checkpoint` | At test line 31, `jobs.wait` reports `parent_interrupted_unclean` instead of `stage_failed`. Retained post-test worker state has `pid_birth: null` and subsequently reaches `stage_failed`, exit code 1, resumable true. In `src/arcpuzzles/check_jobs.py`, `_birth` returns `None` when process-stat lookup fails, and `status` maps unavailable birth data for an active state to `parent_interrupted_unclean`. The evidence supports an early supervisor-status classification problem; it does not prove the supervisor really died. | Synthetic fixture task `aaaa00000001`; shared detached-job/process-status infrastructure. |
| `tests/test_packet_racket_setup.py::test_system_runtime_must_pass_probe_on_unsupported_platform` | At test line 77, exception-message regex mismatch: expected `Racket probe failed: unusable runtime`, actual `Racket probe failed: returncode=1; stdout=''; stderr='unusable runtime'`. `src/arcpuzzles/review_full_packet_files/setup_racket.py` emits the latter diagnostic. The rejected runtime behavior occurs as expected; the text contract differs. | Shared packet runtime setup; mocked Darwin/arm64 environment, no puzzle generation. |
| `tests/test_task_test_prerequisites.py::test_preflight_matches_isolated_test_interpreter` | Final top-level assertion sees the nested task test fail. Retained child `result.json` and JUnit XML identify literal executable-path mismatch: parent records `WORK/repo/../.venv-review/bin/python`, child reports normalized `WORK/.venv-review/bin/python`. The isolated preflight passes, has no missing dependencies, disables user site, and clears `PYTHONPATH`; the nested `test_isolated` fails only at its exact-string `sys.executable` assertion. | Synthetic fixture task `aaaa00000001`; interpreter-path normalization in infrastructure test. |

All five final failures were also present in the initial repository run. They have now also been reproduced on the **unpatched original-packet extraction**, as documented below. No final failure node or fixture above references `899e2a4cfac9`, and their directly observed causes concern other tasks or shared infrastructure. The pristine reproduction establishes that these five failures predate the assigned generator repair under this environment and invocation.

## Confirmed pristine-packet baseline

The selected five final failing nodes were rerun in `/workspace/scratch/5c9986a12ab6/fresh_replay/WORK`, before any source patch, after fresh Racket setup and independent creation of a fresh `.venv-review`. Both setup commands exited 0. The pytest invocation used the same relative interpreter form as the final suite:

```text
.venv-review/bin/python run_with_racket.py ../.venv-review/bin/python -m pytest -q <the exact five node IDs listed above>
```

The result was **5 failed, 0 passed, 0 skipped**, in **8.44 seconds**, exit status **1**. **All five node IDs reproduced**, with the same visible assertions and error messages, including the same historical episode hash. The isolated-child diagnostic again confirms successful prerequisite imports and the literal parent/child executable-path spelling mismatch. There are **no unresolved nodes among these five**.

`checks/final-handoff/pristine-baseline.json` records exact argv, invocation and effective working directories, exit statuses, setup logs, selected failures, retained nested-child details, and before/after SHA-256 hashes of 14 relevant source files. Those source hashes are unchanged. Environment package versions, copied distribution files and hashes, and isolated-import validation are recorded separately in `checks/final-handoff/fresh-test-env.json`; complete pytest output is in `checks/final-handoff/pristine-five-node-baseline.log`.

This selected baseline does not claim that the entire original packet suite was run or that these issues reproduce under all host environments. The fresh extraction and environment are left ready for a subsequent patch replay.

## Comparison with the initial repository run

`checks/repository-tests.log` records **13 failed, 588 passed, 3 skipped, 18 subtests passed**, in **214.34 seconds**. The final run has eight fewer failures and eight additional passes, with unchanged skip and subtest counts. There are **no new failing node IDs**.

The eight nodes no longer failing are:

- `tests/test_review_tooling_refresh.py::test_task_tests_include_new_workspace_and_use_staged_catalog`
- `tests/test_review_tooling_refresh.py::test_task_tests_collect_source_once_and_keep_legacy_imports[False]`
- `tests/test_review_tooling_refresh.py::test_task_tests_collect_source_once_and_keep_legacy_imports[True]`
- `tests/test_review_tooling_refresh.py::test_task_tests_keep_legacy_collection_for_nonstandard_source_name`
- `tests/test_review_tooling_refresh.py::test_missing_task_tests_are_not_a_pass`
- `tests/test_review_tooling_refresh.py::test_task_test_import_warning_is_actionable_without_breaking_legacy_snapshot`
- `tests/test_review_tooling_refresh.py::test_task_tests_expose_portable_helper_and_count_skips`
- `tests/test_review_tooling_refresh.py::test_preflight_blocks_missing_import_before_pytest`

The initial log also reports isolated `pytest` missing from the original selected interpreter. The final retained isolated child instead imports pytest, NumPy, and Pillow successfully from `.venv-review`. The observed improvement is consistent with the interpreter/dependency setup change; it must not be credited to the generator repair. The remaining interpreter test has changed direct cause from missing prerequisites to executable-path spelling mismatch.

## Skips and scope limits

- The three skips are optional native tensor export tests: two cases at `tests/test_native_export.py:52` and one at line 100, each because `torch` is unavailable. Their tensor behavior remains unverified in this run.
- `repo/pyproject.toml` sets repository pytest discovery to `testpaths = ["tests"]`. Thus this full repository run does not itself establish that the generator-local `generators/899e2a4cfac9/tests/test_border_components.py` regressions ran; the task-local run is separate evidence.
- The first repository log is an earlier work-session run. The additional pristine baseline now confirms all five final failures on original-packet sources; it does not provide a complete pristine-suite baseline for every other node.
- Both suite logs show the effective repository working directory, but do not include the complete original launcher command. This analysis does not invent that missing provenance.
- No repository sources were edited. Only the requested five failing nodes were additionally tested in the fresh extraction; its environment and Racket runtime were set up without applying a source patch. No solve/private or masked data was read.
