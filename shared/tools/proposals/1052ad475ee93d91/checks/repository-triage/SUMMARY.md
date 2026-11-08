# Repository-suite triage

**Completed run:** 19 failed, 995 passed, 3 skipped, 18 subtests passed in 438.99s (0:07:18)

All 19 failure tracebacks were inspected. They are grouped below by observed cause; none remains unclassified at the immediate-failure level. This is bounded triage, not a successful repository-wide qualification. No repository source was modified.

## Measured causes

| Cause | Failed tests | Evidence |
|---|---:|---|
| Shipped archival expectations no longer match shipped generators | 2 | Full tracebacks, independent archival reruns, shipped generator notes |
| `/proc` PIDs disagree with syscall PIDs | 12 | PID diagnostic; liveness tracebacks; retained cleanup receipts; representative foreground rerun |
| Interpreter path spelling changes across child execution | 2 | Retained preflight/child traceback and exact saved-environment settings comparison |
| Test expects an older diagnostic/command shape | 2 | Exact expected/actual tracebacks and unchanged implementation bytes |
| Socket creation returns EPERM | 1 | Full server traceback before bind/listen |

### Historical archival expectations

`defba1ab4f90` expects historical hash `8b35cf5d…`; the shipped v2.0.0 sampler returns `b4ba8572…`, indexes `[0,1]`, and no rejections. Its shipped notes document replacement of the older v1.3.0 sampler. `d982cffd80f8` v3.0.0 accepts seed 17/index 0 with `self_check=[]`; the test still requires a rejection. Its shipped notes document repair of that validator. Both failures repeated in the focused run.

### Process identity and cleanup verification

The diagnostic measured syscall PID `6` and `/proc/self/stat` PID `55965`; `_process_table_supported()` returned false. Managed audit/jobs tests therefore receive `liveness_unknown`. All four foreground cases fail their fixture's direct `/proc/<pid>/stat` liveness assertion before sending the signal; one repeated in 0.29s. The live-child/PID-reuse cases likewise receive `liveness_unknown`. The native resume, committed-receipts, and pinned-Racket resume fixtures retain `session_empty=false` with `remaining_processes=null`; the runtime refuses to claim safe resume when process-table cleanup cannot be verified. This explains 12 failures without a timing-load assumption.

### Interpreter path spelling

The controller records `/WORK/repo/../.venv/bin/python`, while the child reports `/WORK/.venv/bin/python`. The prerequisite preflight actually passed: user site was disabled, inherited PYTHONPATH was absent, and pytest/NumPy/Pillow had no dependency errors. Its generated test then failed a raw `sys.executable` equality assertion. For the separate policy/schedule resume test, the read-only diagnostic recreated only the saved environment/interpreter prefix and recomputed settings: **the sole differing key was `python`**, with those equivalent spellings. The schedule hash and policy flags matched. No battery was rerun by this diagnostic.

### Exact protocol assertions and socket restriction

The packet-Racket test expects `Racket probe failed: unusable runtime`, but the unchanged implementation reports `Racket probe failed: returncode=1; stdout=''; stderr='unusable runtime'`; its mocked unusable runtime is rejected as intended. The review-runtime test expects a six-item battery command, while the unchanged implementation additionally supplies `--time-budget 310`. The HTTP test fails creating an AF_INET/SOCK_STREAM socket with `PermissionError: [Errno 1] Operation not permitted`, before binding or serving requests.

## Complete failure mapping

### Historical archival expectations (2)

- `tests/test_archival_reference.py::test_archival_rule_access_matches_measured_historical_pairs[defba1ab4f90-8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0]`

- `tests/test_archival_reference.py::test_archival_rules_still_enforce_generator_self_checks[d982cffd80f8]`



### Process identity and cleanup verification (12)

- `tests/test_check_audit_phase.py::test_managed_public_audit_check_and_resume_keep_target_phase`

- `tests/test_check_jobs.py::test_unfinished_dead_supervisor_is_not_a_stage_failure_or_safe_resume`

- `tests/test_check_jobs.py::test_actual_detached_failure_wait_and_resume_reuses_checkpoint`

- `tests/test_check_resume.py::test_native_battery_reuses_receipts_after_interruption`

- `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[lint-15]`

- `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[lint-2]`

- `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[selfcheck-15]`

- `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[selfcheck-2]`

- `tests/test_check_signals.py::test_status_distinguishes_live_child_after_unclean_controller_loss`

- `tests/test_check_signals.py::test_status_rejects_pid_reuse_and_legacy_liveness_unknown`

- `tests/test_check_signals.py::test_signal_before_child_exits_preserves_committed_receipts`

- `tests/test_check_signals.py::test_resume_recipe_restores_pinned_racket_for_path_consuming_gates`



### Equivalent interpreter paths compared as raw strings (2)

- `tests/test_check_signals.py::test_resume_recipe_retains_policy_environment_and_schedule_copy`

- `tests/test_task_test_prerequisites.py::test_preflight_matches_isolated_test_interpreter`



### Stale exact protocol assertions (2)

- `tests/test_packet_racket_setup.py::test_system_runtime_must_pass_probe_on_unsupported_platform`

- `tests/test_review_runtime.py::test_check_after_phase_uses_after_policy_and_receipt`



### Socket creation denied (1)

- `tests/test_server.py::test_http_filters_errors_and_challenge_match_python`



## Source and evidence binding

`source-comparison.json` verifies 21 relevant test, implementation, generator-note and wrapper files are byte-identical to the uploaded ZIP. It does not claim a fresh run of every test in a separate pristine extraction.

- `../repository-tests.log` and `../repository-tests.xml`: completed run; hashes in `summary.json`.
- `failures.json`: all 19 full failure records and cause assignments.
- `fixture-evidence.json`: selected retained checkpoint/preflight fields, original paths and original-file hashes.
- `focused-command.json`, `focused.log`: exact three-test rerun, exit 1.
- `signal-command.json`, `signal.log`: exact one-case foreground rerun, exit 1.
- `inspect_causes.py`, `inspect-causes-command.json`, `inspect-causes.log`: archival/PID/source diagnostic, exit 0.
- `settings-probe-command.json`, `settings-probe.log`, `settings-probe.json`: exact read-only settings diagnostic, exit 0.
- `summarize.py`, `summary-command.json`, `summary.json`: this reproducible triage collector and command receipt.

## Limitations

The broader repository suite remains failing. These measured causes are outside the assigned generator repair; no shared fixes or approval changes were made. The three skipped tests lack optional torch. The separately reported task-specific battery/tests and proposed parametric evidence are not upgraded or invalidated merely by this grouping. No load/timing explanation, universal runtime compatibility, or production approval is claimed.
