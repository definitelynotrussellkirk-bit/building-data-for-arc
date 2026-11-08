# Read-only repository-suite triage

The wider suite remains **17 failed, 1002 passed, 3 skipped, 18 subtests passed** (497.93 seconds). The focused repaired-task and parametric checks are a separate scope. No repository source was changed and the full suite was not rerun.

## Classification

| Category | Failures | Evidence |
|---|---:|---|
| Environment restriction | 13 | Twelve process-observation/liveness failures plus one denied socket creation. |
| Stale assertion / shared tooling | 2 | Exact error-message and command-argument expectations conflict with current shared implementations. |
| Unrelated task fixture | 2 | Historical identity/rejection assumptions for two other tasks fail; causes remain unresolved. |
| Unknown category | 0 | The fixture category identifies scope, not a resolved root cause. |

## Process environment evidence

A bounded read-only probe observed `os.getpid()=5` while `/proc/self/stat` identifies PID `48947`; `runtime._process_table_supported()` returned `False`. This directly matches the conservative `liveness_unknown` branches and refusal to certify descendant cleanup. Four signal tests fail at their initial PID-observation assertion before delivering the signal, so their traces do not demonstrate a signal-cleanup regression.

The socket failure is direct: Python raises `PermissionError: [Errno 1] Operation not permitted` while creating the server socket, before HTTP behavior is exercised.

## Every failed test

### 1. `tests/test_archival_reference.py::test_archival_rule_access_matches_measured_historical_pairs[defba1ab4f90-8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0]`

**Classification:** unrelated_task_fixture. **Confidence:** high for scope; root cause unresolved.

Historical-pair identity expected 8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0; observed b4ba8572d6971d19c012fe1d9e6c33122ab1c68d440a1a2286729fdc279c13db for defba1ab4f90 at seed17, medium, one train/one test, archival reference.

Task-specific generator, archival authority, catalog and asserting test are byte-identical to original ZIP. Cause of fixture discrepancy was not resolved; no original-snapshot suite run was performed.

Evidence: `console.log` failure summary line 541; full traceback also retained in `junit.xml`.

### 2. `tests/test_archival_reference.py::test_archival_rules_still_enforce_generator_self_checks[d982cffd80f8]`

**Classification:** unrelated_task_fixture. **Confidence:** high for scope; root cause unresolved.

d982cffd80f8 archival generation completed but no rejection reason contained self_check:, contradicting this test fixture assumption. This does not establish that validation was bypassed.

Task-specific generator, archival authority, catalog and asserting test are byte-identical to original ZIP. Cause of fixture discrepancy was not resolved; no original-snapshot suite run was performed.

Evidence: `console.log` failure summary line 542; full traceback also retained in `junit.xml`.

### 3. `tests/test_check_audit_phase.py::test_managed_public_audit_check_and_resume_keep_target_phase`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Expected a definite stage/controller status but obtained liveness_unknown. check_jobs.status and runtime process identity code explicitly take this conservative branch when _process_table_supported() is false.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 543; full traceback also retained in `junit.xml`.

### 4. `tests/test_check_jobs.py::test_unfinished_dead_supervisor_is_not_a_stage_failure_or_safe_resume`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Expected a definite stage/controller status but obtained liveness_unknown. check_jobs.status and runtime process identity code explicitly take this conservative branch when _process_table_supported() is false.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 544; full traceback also retained in `junit.xml`.

### 5. `tests/test_check_jobs.py::test_actual_detached_failure_wait_and_resume_reuses_checkpoint`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Expected a definite stage/controller status but obtained liveness_unknown. check_jobs.status and runtime process identity code explicitly take this conservative branch when _process_table_supported() is false.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 545; full traceback also retained in `junit.xml`.

### 6. `tests/test_check_resume.py::test_native_battery_reuses_receipts_after_interruption`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Interrupted checkpoint resume is refused with Checkpoint has unclean or unknown child liveness; runtime cannot verify child-session emptiness in the inconsistent procfs view.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 546; full traceback also retained in `junit.xml`.

### 7. `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[lint-15]`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Fixture writes its two PIDs, but live(pid) is false at the initial all-live assertion, before the requested signal is delivered. live() reads /proc/PID/stat; this environment has inconsistent syscall PID/procfs namespaces.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 547; full traceback also retained in `junit.xml`.

### 8. `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[lint-2]`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Fixture writes its two PIDs, but live(pid) is false at the initial all-live assertion, before the requested signal is delivered. live() reads /proc/PID/stat; this environment has inconsistent syscall PID/procfs namespaces.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 548; full traceback also retained in `junit.xml`.

### 9. `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[selfcheck-15]`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Fixture writes its two PIDs, but live(pid) is false at the initial all-live assertion, before the requested signal is delivered. live() reads /proc/PID/stat; this environment has inconsistent syscall PID/procfs namespaces.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 549; full traceback also retained in `junit.xml`.

### 10. `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[selfcheck-2]`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Fixture writes its two PIDs, but live(pid) is false at the initial all-live assertion, before the requested signal is delivered. live() reads /proc/PID/stat; this environment has inconsistent syscall PID/procfs namespaces.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 550; full traceback also retained in `junit.xml`.

### 11. `tests/test_check_signals.py::test_status_distinguishes_live_child_after_unclean_controller_loss`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Expected a definite stage/controller status but obtained liveness_unknown. check_jobs.status and runtime process identity code explicitly take this conservative branch when _process_table_supported() is false.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 551; full traceback also retained in `junit.xml`.

### 12. `tests/test_check_signals.py::test_status_rejects_pid_reuse_and_legacy_liveness_unknown`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Expected a definite stage/controller status but obtained liveness_unknown. check_jobs.status and runtime process identity code explicitly take this conservative branch when _process_table_supported() is false.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 552; full traceback also retained in `junit.xml`.

### 13. `tests/test_check_signals.py::test_signal_before_child_exits_preserves_committed_receipts`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Committed lint receipt and zero running-stage assertions pass; resumable is false. Unknown session membership makes child_cleanup.session_empty false, so runtime deliberately refuses resumability.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 553; full traceback also retained in `junit.xml`.

### 14. `tests/test_check_signals.py::test_resume_recipe_restores_pinned_racket_for_path_consuming_gates`

**Classification:** environment_restriction. **Confidence:** supported inference from trace, source branch and bounded process-table probe.

Interrupted checkpoint resume is refused with Checkpoint has unclean or unknown child liveness; runtime cannot verify child-session emptiness in the inconsistent procfs view.

Bounded live probe confirms mismatched os.getpid()/proc-self PID and runtime._process_table_supported()==False. Shared/test sources are unchanged. No claim is made about equivalent behavior on an ordinary Linux process table.

Evidence: `console.log` failure summary line 554; full traceback also retained in `junit.xml`.

### 15. `tests/test_packet_racket_setup.py::test_system_runtime_must_pass_probe_on_unsupported_platform`

**Classification:** stale_assertion_shared_tooling. **Confidence:** direct assertion mismatch.

Mocked failed runtime probe correctly raises RuntimeError, but regex expects Racket probe failed: unusable runtime; actual richer diagnostic is Racket probe failed: returncode=1; stdout=''; stderr='unusable runtime'.

Asserted error format conflicts with unchanged shared setup implementation; this is a synthetic mocked probe, not failure of the installed Racket runtime.

Evidence: `console.log` failure summary line 555; full traceback also retained in `junit.xml`.

### 16. `tests/test_review_runtime.py::test_check_after_phase_uses_after_policy_and_receipt`

**Classification:** stale_assertion_shared_tooling. **Confidence:** direct assertion mismatch.

Exact fake-run command assertion omits implemented --time-budget 310 suffix; all earlier command arguments match.

Test expectation conflicts with unchanged runtime timeout-budget argument construction; no real battery gate fails in this mocked test.

Evidence: `console.log` failure summary line 556; full traceback also retained in `junit.xml`.

### 17. `tests/test_server.py::test_http_filters_errors_and_challenge_match_python`

**Classification:** environment_restriction. **Confidence:** direct trace.

AF_INET/SOCK_STREAM socket construction in ThreadingHTTPServer raises PermissionError [Errno1] Operation not permitted before binding or serving any request.

Direct operating-environment denial; test/server sources are unchanged.

Evidence: `console.log` failure summary line 557; full traceback also retained in `junit.xml`.

## Original-packet source comparison

Direct member reads from `SEND-THIS-ARCpuzzles-review(20261023-022243).zip` confirm **25/25** selected test, shared-code, catalog, task-generator and archival-rule files are byte-identical to the original ZIP. `triage.json` lists exact archive member paths and both SHA-256 values. The ZIP itself has SHA-256 `8c0c8b1c8a538a708b8437c4093524c6d70f193b174c2141cb326b193186864f`.

This comparison supports that these artifacts were inherited unchanged. It is not a baseline execution: no pristine-original suite was run, and the entire transitive runtime/dependency closure was not compared. In particular, the two archival mismatches must remain unresolved findings rather than being dismissed as pre-existing solely because they involve other tasks.

## Scope and remaining status

All 17 failures remain recorded. This triage changes no test result or approval and proposes no shared-code patch. Three optional native-export tests were skipped because `torch` is absent.
