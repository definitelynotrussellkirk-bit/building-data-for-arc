# Full repository suite: explicit failure scope

**The full repository suite failed: 17 failed, 1002 passed, 3 skipped, and 18 subtests passed in 664.66 seconds (11:04).** This is the terminal result retained in `checks/repository-suite.log`, SHA-256 `35e475098ca4ee6d1bb27ee8523d60a75fcb0cdfd38a3f955904176e1fa62b22`. The log reaches `[100%]`; the later requested SIGINT was not sent because the authorized pytest process had already disappeared.

The command was run from the outer packet directory through `WORK/.venv/bin/python review.py run /workspace/scratch/e99e6bfff21b/packet/WORK/.venv/bin/python -m pytest -q --tb=short`; the payload cwd was `WORK/repo/`. The three skips are all optional `torch` imports in `tests/test_native_export.py` (two at line 52, one at line 100).

The failure buckets are **2 other-task archival cases + 12 process/liveness cases + 2 exact expectation mismatches + 1 denied socket operation = 17**. The selected-task qualification is separately reported in the return as 82 tests / 159 subtests and twelve green battery stages. Those results and this failed repository-wide run measure different scopes; retain both outcomes.

## Other-task archival behavior: 2 failures

| Exact failed test node | Observed failure |
| --- | --- |
| `tests/test_archival_reference.py::test_archival_rule_access_matches_measured_historical_pairs[defba1ab4f90-8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0]` | The measured episode identity was `b4ba8572d6971d19c012fe1d9e6c33122ab1c68d440a1a2286729fdc279c13db`; the test expected `8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0`. |
| `tests/test_archival_reference.py::test_archival_rules_still_enforce_generator_self_checks[d982cffd80f8]` | No returned rejection reason contained the expected `self_check:` marker. |

Both tests use seed 17, medium difficulty, one demonstration and one query under `reference="archival"`. Their target IDs are `defba1ab4f90` and `d982cffd80f8`, not the selected repair task `33275a4aae3e`. These observations identify failed archival expectations; they do not establish the cause or correctness of either other task's current behavior.

## Process, liveness, signal, and resume integration: 12 failures

| Exact failed test node | Observed failure |
| --- | --- |
| `tests/test_check_audit_phase.py::test_managed_public_audit_check_and_resume_keep_target_phase` | `liveness_unknown` instead of expected resumable `stage_failed`. |
| `tests/test_check_jobs.py::test_unfinished_dead_supervisor_is_not_a_stage_failure_or_safe_resume` | `liveness_unknown` instead of `parent_interrupted_unclean`. |
| `tests/test_check_jobs.py::test_actual_detached_failure_wait_and_resume_reuses_checkpoint` | `liveness_unknown` instead of `stage_failed`. |
| `tests/test_check_resume.py::test_native_battery_reuses_receipts_after_interruption` | Resume rejected a checkpoint with unclean or unknown child liveness. |
| `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[lint-15]` | The fixture's initial `all(live(pid) for pid in pids)` assertion failed. |
| `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[lint-2]` | The same initial fixture-process liveness assertion failed. |
| `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[selfcheck-15]` | The same initial fixture-process liveness assertion failed. |
| `tests/test_check_signals.py::test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[selfcheck-2]` | The same initial fixture-process liveness assertion failed. |
| `tests/test_check_signals.py::test_status_distinguishes_live_child_after_unclean_controller_loss` | `liveness_unknown` instead of `controller_lost_child_alive`. |
| `tests/test_check_signals.py::test_status_rejects_pid_reuse_and_legacy_liveness_unknown` | `liveness_unknown` instead of `parent_interrupted_unclean`. |
| `tests/test_check_signals.py::test_signal_before_child_exits_preserves_committed_receipts` | `resumable` was false where the fixture expected true. |
| `tests/test_check_signals.py::test_resume_recipe_restores_pinned_racket_for_path_consuming_gates` | Retry exited 1 because the checkpoint had unclean or unknown child liveness. |

These are shared orchestration tests using temporary fixtures and synthetic task `aaaa00000001`, rather than selected-generator semantic assertions. The runtime deliberately returns unknown when process-table identity cannot be verified. The repeated unknown/liveness results are consistent with process-visibility restrictions in this execution environment, but this classification is **not proof that one environmental cause explains all twelve failures**. No baseline rerun or additional process tests were performed for this report.

## Exact expectation mismatches in shipped harness: 2 failures

| Exact failed test node | Observed failure |
| --- | --- |
| `tests/test_packet_racket_setup.py::test_system_runtime_must_pass_probe_on_unsupported_platform` | The test expected the regex `Racket probe failed: unusable runtime`; the implementation reported `Racket probe failed: returncode=1; stdout=''; stderr='unusable runtime'`. The expected failure occurred with a different, more detailed message. |
| `tests/test_review_runtime.py::test_check_after_phase_uses_after_policy_and_receipt` | The expected battery argument array omitted the actual `--time-budget 310` arguments. The test intercepts command construction with a fake process runner. |

Static inspection shows the assertions disagree with the shipped implementations' text/arguments. These are classified as stale exact expectations; the relevant test and implementation files are unchanged from the original packet. No original-packet execution was performed to re-establish a baseline result.

## Socket operation denied: 1 failure

`tests/test_server.py::test_http_filters_errors_and_challenge_match_python` failed while constructing the HTTP server's socket, before serving its test request. The traceback ends in `_socket.socket.__init__` with `PermissionError: [Errno 1] Operation not permitted`. This is an observed socket permission denial in the execution environment, not a measured HTTP response or generator-output mismatch.

## Source-integrity check against the original packet

`checks/repository-suite-source-hashes.json` records exact expected/current SHA-256 values and the original-archive identity of the packet manifest. **31/31 inspected files matched `PACKET-MANIFEST.json`; the current manifest itself matched the original uploaded ZIP exactly.** The checked set contains:

- All eight test modules with failed cases, plus `tests/conftest.py` and the shared `test_check_rotations.py` fixture helper: ten test files.
- Nine implementation files covering runtime/check jobs, catalog/worker/dataset behavior, HTTP server/CLI, receipt reading, and the Racket setup template.
- The shared battery shell script and generator base runtime; three catalog/mapping files; and both outer runtime/setup wrappers.
- Both archival-test target generators and all three mapped authority-source files for those targets.

The unchanged other-task generator hashes are:

| Task | SHA-256 |
| --- | --- |
| `defba1ab4f90` | `4189136b4e863e70bf07ee2466d865493554544a72273e4f3918da61da7f7c26` |
| `d982cffd80f8` | `f8eacbfeab97db8e356ce5baac3097de8c62a04af64168f1f3f5445fa4974297` |

The whole canonical data file has the separately disclosed selected-task authority synchronization, so it is not described as wholly unchanged. Instead, each of the two archival-test tasks' exact canonical row bytes was compared with the original ZIP; both matched. Their original/current row hashes are included in the source-hash receipt.

These comparisons establish that the inspected failing tests, shared implementations, other-task generators, and their relevant authority sources were **not directly edited by this repair**. They do not prove that each failure predated all review activity, exclude every indirect environmental interaction, or establish causation. The full-suite failures remain explicit unresolved qualification limits outside the selected task's reported verification. No further tests were run to produce this scope report.
