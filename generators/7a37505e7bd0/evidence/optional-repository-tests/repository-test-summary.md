# Repository test failure classification

The recorded suite has **995 passed, 19 failed, 3 skipped, and 18 additional passed subtests**, in 404.85 seconds. There are 1,017 primary test cases and no errors. The XML contains 1,017 `<testcase>` elements, although its suite `tests` attribute is 1,035; the additional subtests explain that difference.

This is a findings-only review of the saved suite output, relevant implementation/tests, and one small metadata diagnostic. No shared or task source was changed, and the broad suite was not rerun. **No pristine baseline full-suite comparison was made, so these failures are not all claimed to be proven pre-existing.**

## Classification

| Category | Failures | Evidence |
|---|---:|---|
| Process liveness and safe resume | 12 | Recorded unknown-state or liveness assertions; current syscall/proc PID disagreement and the implementation's explicit guard. |
| Socket permission | 1 | Original traceback raises `PermissionError: [Errno 1] Operation not permitted` while creating a socket. |
| Interpreter path identity | 2 | Retained isolated-test stdout and a metadata-only resume-settings comparison show equivalent paths with different spelling. |
| Interface expectations | 2 | Exact regex/argv assertions disagree with current error formatting and the `--time-budget 310` argument. |
| Historical expectations | 2 | Other-task archival identity and expected-rejection assertions fail; historical cause is unresolved. |

The process diagnostic observed `os.getpid() = 7` and `/proc/self/stat` PID `16118`; `_process_table_supported()` returned false and `_process_identity()` returned null. The retained between-stages receipt has `session_empty=false` and `remaining_processes=null`. These facts support the liveness classification, but do not constitute individual reruns of those twelve tests. The four signal variants fail before their test signal is sent.

For interpreter identity, the saved setting ends in `WORK/repo/../.venv/bin/python`, while the metadata child reports `WORK/.venv/bin/python`. Both resolve to the same file. This is the only mismatch among the eight base settings read with the recorded resume environment. The isolated-test receipt independently shows that exact string assertion failing after dependency preflight and user-site isolation had succeeded.

## All 19 failing tests

| # | Exact test identity | Observed failure | Category |
|---:|---|---|---|
| 1 | `tests/test_archival_reference.py::test_archival_rule_access_matches_measured_historical_pairs[defba1ab4f90-8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0]` | Historical pair SHA-256 expected 8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0; actual b4ba8572d6971d19c012fe1d9e6c33122ab1c68d440a1a2286729fdc279c13db. | Historical expectation |
| 2 | `tests/test_archival_reference.py::test_archival_rules_still_enforce_generator_self_checks[d982cffd80f8]` | No recorded rejection reason contains self_check:; any(...) returned False. | Historical expectation |
| 3 | `tests/test_check_audit_phase.py::test_managed_public_audit_check_and_resume_keep_target_phase` | Observed liveness_unknown; expected stage_failed with resumable=True. | Liveness |
| 4 | `tests/test_check_jobs.py::test_unfinished_dead_supervisor_is_not_a_stage_failure_or_safe_resume` | Observed liveness_unknown; expected parent_interrupted_unclean for synthetic PID 99999999. | Liveness |
| 5 | `tests/test_check_jobs.py::test_actual_detached_failure_wait_and_resume_reuses_checkpoint` | Observed liveness_unknown; expected stage_failed with stage_exit_code=1. | Liveness |
| 6 | `tests/test_check_resume.py::test_native_battery_reuses_receipts_after_interruption` | ValueError: Checkpoint has unclean or unknown child liveness; inspect with check-status --out before starting a fresh output. | Liveness |
| 7 | `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[lint-15]` | assert all(live(pid) for pid in pids) failed before the test sends its signal. | Liveness |
| 8 | `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[lint-2]` | assert all(live(pid) for pid in pids) failed before the test sends its signal. | Liveness |
| 9 | `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[selfcheck-15]` | assert all(live(pid) for pid in pids) failed before the test sends its signal. | Liveness |
| 10 | `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[selfcheck-2]` | assert all(live(pid) for pid in pids) failed before the test sends its signal. | Liveness |
| 11 | `tests/test_check_signals.py::test_status_distinguishes_live_child_after_unclean_controller_loss` | Observed liveness_unknown; expected controller_lost_child_alive. | Liveness |
| 12 | `tests/test_check_signals.py::test_status_rejects_pid_reuse_and_legacy_liveness_unknown` | Observed liveness_unknown; expected parent_interrupted_unclean for a wrong-birth controller record. | Liveness |
| 13 | `tests/test_check_signals.py::test_signal_before_child_exits_preserves_committed_receipts` | check_status(out)['resumable'] was False; expected True. | Liveness |
| 14 | `tests/test_check_signals.py::test_resume_recipe_retains_policy_environment_and_schedule_copy` | Resume subprocess returned 1: Settings differ or old checkpoint has no settings; start a new --out. | Interpreter path |
| 15 | `tests/test_check_signals.py::test_resume_recipe_restores_pinned_racket_for_path_consuming_gates` | Resume subprocess returned 1: Checkpoint has unclean or unknown child liveness; inspect with check-status --out before starting a fresh output. | Liveness |
| 16 | `tests/test_packet_racket_setup.py::test_system_runtime_must_pass_probe_on_unsupported_platform` | Regex expected 'Racket probe failed: unusable runtime'; actual message was "Racket probe failed: returncode=1; stdout=''; stderr='unusable runtime'". | Interface expectation |
| 17 | `tests/test_review_runtime.py::test_check_after_phase_uses_after_policy_and_receipt` | Actual mocked battery argv appends --time-budget 310; the expected argv ends with --keep-going. | Interface expectation |
| 18 | `tests/test_server.py::test_http_filters_errors_and_challenge_match_python` | PermissionError: [Errno 1] Operation not permitted during socket.socket(AF_INET, SOCK_STREAM) construction. | Socket permission |
| 19 | `tests/test_task_test_prerequisites.py::test_preflight_matches_isolated_test_interpreter` | Outer assertion result['passed'] failed with empty stderr; retained child stdout shows sys.executable path spelling differed: WORK/repo/../.venv versus WORK/.venv. | Interpreter path |

## Three skips

All three report `could not import 'torch': No module named 'torch'`:

- `tests/test_native_export.py::test_private_tensors_preserve_labels_without_teacher_forcing[native-False]`
- `tests/test_native_export.py::test_private_tensors_preserve_labels_without_teacher_forcing[bottleneck-True]`
- `tests/test_native_export.py::test_too_small_tensor_canvas_retains_failed_export`

The two teacher-forcing variants skip at `tests/test_native_export.py:52`; the too-small-canvas case skips at line 100.

## Scope and retained evidence

The two interface mismatches use mocked operations, and the two archival mismatches concern `defba1ab4f90` and `d982cffd80f8`. Their apparent independence from the assigned generator edits follows from those scopes and fixtures; their historical pre-existence was not proven. The missing expected archival rejection does not by itself demonstrate validator bypass. The pinned-Racket resume test already passed its real Racket stage and then stopped at a liveness guard.

Primary evidence is `checks/repository-tests.xml` and `checks/repository-tests.log`. `checks/repository-test-summary.json` retains exact XML messages, classifications, source/evidence hashes, and all test identities. The metadata script, output, stdout/stderr, and exact argv/cwd/exit receipt are retained under `checks/repository-test-environment-diagnostic.*`; the wrapper and its metadata-only child both exited 0. Selected original temporary fixture receipts are preserved as hash-bound excerpts in that diagnostic output. No extra suite, socket, signal, resume, or installation was attempted.
