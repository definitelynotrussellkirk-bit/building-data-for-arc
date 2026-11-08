# Repository-suite failure attribution

## Result

All **16 failures** from the repaired workspace's repository suite reproduced on
**pristine input-packet source** in a separate extraction and Python environment.
The pristine run failed at the same assertions, with no skips or collection
errors. These are confirmed inherited failures under this execution environment;
the selected `b1972482cb43` repair did not introduce these observations.

| Run | Result | Elapsed |
|---|---|---:|
| Working repository, default `pytest -q` suite | 16 failed, 970 passed, 3 skipped, 18 subtests passed | 425.58 s |
| Pristine packet, only the exact 16 failing node IDs | 16 failed, 0 skipped, 0 collection errors | 10.59 s |

The three skips in the working run concern the optional `torch` dependency.
The generator's separate focused regression suite is outside this attribution.

## Causes

| Cases | Classification | Observed cause |
|---:|---|---|
| 12 | Environment-sensitive process identity and resume checks | A pristine-wrapper probe returned syscall PID **7** but `/proc/self/stat` PID **32283**. The unmodified runtime detects the mismatch, returns no process identity, and conservatively reports `liveness_unknown` or refuses resume. Four signal cases fail their own direct `/proc` liveness precondition before sending a signal. |
| 2 | Existing archival expectations disagree with issued behavior | `defba1ab4f90` produces a different historical episode digest; `d982cffd80f8` produces no rejection reason containing `self_check:` for the seeded draw the test expects to reject. Both differences reproduce on issued bytes. This investigation does not decide whether their expectations or the unrelated generators should change. |
| 1 | Exact Racket error-message expectation | The test expects `Racket probe failed: unusable runtime`; issued code raises `RuntimeError` with `returncode=1; stdout=''; stderr='unusable runtime'` included in the message. The exception is raised, but the regex fails. |
| 1 | Exact battery-argument expectation | The test omits `--time-budget 310` from its expected command. Issued runtime appends that argument for its default 330-second controller budget. |

The historical episode mismatch is exact and repeatable:

- Expected: `8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0`
- Actual: `b4ba8572d6971d19c012fe1d9e6c33122ab1c68d440a1a2286729fdc279c13db`

The process-table explanation follows the current code in
`src/arcpuzzles/runtime.py` (`_process_table_supported`, `_process_identity`,
`check_status`) and `src/arcpuzzles/check_jobs.py` (`status`). The environment
probe directly confirms the guard's failing premise; no guard was bypassed.

## Exact failure inventory

All node IDs, including the full archival hash parameter, appear in `summary.json`
and the retained command argument list.

| Test file | Failing test cases |
|---|---|
| `tests/test_archival_reference.py` | `test_archival_rule_access_matches_measured_historical_pairs[defba1ab4f90-…]`; `test_archival_rules_still_enforce_generator_self_checks[d982cffd80f8]` |
| `tests/test_check_audit_phase.py` | `test_managed_public_audit_check_and_resume_keep_target_phase` |
| `tests/test_check_jobs.py` | `test_unfinished_dead_supervisor_is_not_a_stage_failure_or_safe_resume`; `test_actual_detached_failure_wait_and_resume_reuses_checkpoint` |
| `tests/test_check_resume.py` | `test_native_battery_reuses_receipts_after_interruption` |
| `tests/test_check_signals.py` | `test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[lint-15]`, `[lint-2]`, `[selfcheck-15]`, `[selfcheck-2]`; `test_status_distinguishes_live_child_after_unclean_controller_loss`; `test_status_rejects_pid_reuse_and_legacy_liveness_unknown`; `test_signal_before_child_exits_preserves_committed_receipts`; `test_resume_recipe_restores_pinned_racket_for_path_consuming_gates` |
| `tests/test_packet_racket_setup.py` | `test_system_runtime_must_pass_probe_on_unsupported_platform` |
| `tests/test_review_runtime.py` | `test_check_after_phase_uses_after_policy_and_receipt` |

## Isolation and evidence

The pristine extraction is bound to upload SHA-256
`3844f60d9fef8c191d00d09bee47452fc95da285b45ac74599955b08807f24bf`.
The selected tests ran through that extraction's public `review.py run` wrapper,
using a separately created virtual environment and its own bundled Racket.
Inherited `PYTHONPATH`, `PYTHONHOME`, `ARCPUZZLES_HOME`, and `RACKET_PATH` were
removed; `PYTHONNOUSERSITE=1` remained enabled. The environment probe records
package paths and confirms imports resolve to the pristine repository.

A three-way SHA-256 comparison verified **25 relevant files** match exactly
between the upload, pristine extraction, and repaired workspace. The comparison
covers all failing test files, their shared fixtures, relevant orchestration
code, catalog/canonical data, and the two archival generators and mapped rules.

Evidence retained under `checks/repository-suite-review/`:

- `summary.json` and this report: current classification and exact failure list.
- `pristine-selected.run.json`, `pristine-selected.log`,
  `pristine-selected.junit.xml`: exact argv, working directory, source binding,
  exit status, and all 16 reproductions.
- `source-comparison.json`: the 25-file byte-equality record.
- `pristine-environment.log`: source/dependency import paths and Racket location.
- `process-table-probe.stdout.json` and `process-table-probe.run.json`: measured
  PID mismatch and the exact diagnostic command.
- `pristine-source.json` and environment setup receipts: extraction and runtime
  provenance.

No repository source was changed. Only the failing nodes were rerun on pristine
source; the full pristine suite was not rerun. This result does not establish
that the broader repository suite passes on another host, nor does it resolve
the two archival behavior expectations.
