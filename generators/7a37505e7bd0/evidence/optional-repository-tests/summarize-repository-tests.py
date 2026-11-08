#!/usr/bin/env python3
"""Rebuild a findings-only summary from the saved repository suite evidence."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spec(category: str, message: str, interpretation: str, *source_paths: str) -> dict:
    return {"category": category, "concise_failure": message,
            "interpretation": interpretation,
            "reviewed_source_paths": ["repo/" + path for path in source_paths]}


LIVENESS = "environment_process_liveness"
PATH = "interpreter_path_identity"
INTERFACE = "interface_expectation_mismatch"
HISTORICAL = "historical_expectation_mismatch"
SOCKET = "environment_socket_denied"
specifications = {
    "test_archival_rule_access_matches_measured_historical_pairs[defba1ab4f90-8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0]": spec(
        HISTORICAL,
        "Historical pair SHA-256 expected 8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0; actual b4ba8572d6971d19c012fe1d9e6c33122ab1c68d440a1a2286729fdc279c13db.",
        "Recorded seed 17, medium, archival generation for task defba1ab4f90 differs from a fixed historical identity. Fixture/source drift is a hypothesis; no pristine historical replay or source-history attribution was performed.",
        "tests/test_archival_reference.py"),
    "test_archival_rules_still_enforce_generator_self_checks[d982cffd80f8]": spec(
        HISTORICAL,
        "No recorded rejection reason contains self_check:; any(...) returned False.",
        "The seed-17 archival draw for task d982cffd80f8 did not supply the rejection expected by the test. This assertion alone does not demonstrate that the validator was bypassed.",
        "tests/test_archival_reference.py"),
    "test_managed_public_audit_check_and_resume_keep_target_phase": spec(
        LIVENESS, "Observed liveness_unknown; expected stage_failed with resumable=True.",
        "Managed-job status fails at the liveness expectation. The implementation explicitly returns liveness_unknown when its process-table consistency guard fails; the follow-up diagnostic directly observes that guard failing in this sandbox.",
        "tests/test_check_audit_phase.py", "src/arcpuzzles/check_jobs.py", "src/arcpuzzles/runtime.py"),
    "test_unfinished_dead_supervisor_is_not_a_stage_failure_or_safe_resume": spec(
        LIVENESS, "Observed liveness_unknown; expected parent_interrupted_unclean for synthetic PID 99999999.",
        "The process-table consistency guard precedes the dead-supervisor interpretation. Current syscall/proc PID disagreement explains why absence cannot be treated as confirmed death.",
        "tests/test_check_jobs.py", "src/arcpuzzles/check_jobs.py", "src/arcpuzzles/runtime.py"),
    "test_actual_detached_failure_wait_and_resume_reuses_checkpoint": spec(
        LIVENESS, "Observed liveness_unknown; expected stage_failed with stage_exit_code=1.",
        "The detached-job test fails before the expected terminal status/resume assertions. This matches the process-table guard behavior observed in the follow-up, without a per-test rerun.",
        "tests/test_check_jobs.py", "src/arcpuzzles/check_jobs.py", "src/arcpuzzles/runtime.py"),
    "test_native_battery_reuses_receipts_after_interruption": spec(
        LIVENESS, "ValueError: Checkpoint has unclean or unknown child liveness; inspect with check-status --out before starting a fresh output.",
        "Resume is refused by the checkpoint liveness guard after the fixture's interruption. Current process-table inspection is unsupported; no resumed stage failure was reached.",
        "tests/test_check_resume.py", "src/arcpuzzles/runtime.py"),
    "test_status_distinguishes_live_child_after_unclean_controller_loss": spec(
        LIVENESS, "Observed liveness_unknown; expected controller_lost_child_alive.",
        "The test's departed-controller/live-child fixture cannot obtain verifiable controller/session identities when the consistency guard fails.",
        "tests/test_check_signals.py", "src/arcpuzzles/runtime.py"),
    "test_status_rejects_pid_reuse_and_legacy_liveness_unknown": spec(
        LIVENESS, "Observed liveness_unknown; expected parent_interrupted_unclean for a wrong-birth controller record.",
        "The first assertion assumes process identities can be established. Current process inspection is unavailable; subsequent legacy-record assertions were not reached.",
        "tests/test_check_signals.py", "src/arcpuzzles/runtime.py"),
    "test_signal_before_child_exits_preserves_committed_receipts": spec(
        LIVENESS, "check_status(out)['resumable'] was False; expected True.",
        "The retained interrupted receipt already has green committed lint and no running stages, but child_cleanup is session_empty=False with remaining_processes=None. The guard therefore refuses safe resume; this is not evidence of a committed-receipt loss.",
        "tests/test_check_signals.py", "src/arcpuzzles/runtime.py"),
    "test_resume_recipe_retains_policy_environment_and_schedule_copy": spec(
        PATH, "Resume subprocess returned 1: Settings differ or old checkpoint has no settings; start a new --out.",
        "A metadata-only child launched with the saved interpreter spelling and saved environment reproduces one difference among the eight base settings: saved Python has WORK/repo/../.venv, while child sys.executable has WORK/.venv. Both resolve to the same file. runtime.check compares the settings dictionaries literally. This strongly supports path spelling as the cause, but no full resume replay was run.",
        "tests/test_check_signals.py", "src/arcpuzzles/runtime.py"),
    "test_resume_recipe_restores_pinned_racket_for_path_consuming_gates": spec(
        LIVENESS, "Resume subprocess returned 1: Checkpoint has unclean or unknown child liveness; inspect with check-status --out before starting a fresh output.",
        "The recorded test already passed its real pinned Racket rule_smoke stage. Resume is refused at the liveness guard before the PATH-consuming gate, so this failure is not evidence that Racket was unavailable.",
        "tests/test_check_signals.py", "src/arcpuzzles/runtime.py"),
    "test_system_runtime_must_pass_probe_on_unsupported_platform": spec(
        INTERFACE, "Regex expected 'Racket probe failed: unusable runtime'; actual message was \"Racket probe failed: returncode=1; stdout=''; stderr='unusable runtime'\".",
        "The fixture mocks platform and subprocess results. The implementation supplies a richer failure message than the exact regex accepts; this is an error-format expectation mismatch, not an observed real runtime failure on an unsupported platform.",
        "tests/test_packet_racket_setup.py", "src/arcpuzzles/review_full_packet_files/setup_racket.py"),
    "test_check_after_phase_uses_after_policy_and_receipt": spec(
        INTERFACE, "Actual mocked battery argv appends --time-budget 310; the expected argv ends with --keep-going.",
        "runtime.check computes and appends a native time budget before invoking the mocked runner. This assertion is a command-interface expectation mismatch; no real battery stage failed in this test.",
        "tests/test_review_runtime.py", "src/arcpuzzles/runtime.py"),
    "test_http_filters_errors_and_challenge_match_python": spec(
        SOCKET, "PermissionError: [Errno 1] Operation not permitted during socket.socket(AF_INET, SOCK_STREAM) construction.",
        "Direct socket permission denial is recorded before HTTP binding/request assertions. This is environmental restriction evidence from the original traceback; no additional socket attempt was necessary.",
        "tests/test_server.py", "src/arcpuzzles/server.py"),
    "test_preflight_matches_isolated_test_interpreter": spec(
        PATH, "Outer assertion result['passed'] failed with empty stderr; retained child stdout shows sys.executable path spelling differed: WORK/repo/../.venv versus WORK/.venv.",
        "The existing task-test receipt records successful dependency preflight, user-site isolation, and cleared PYTHONPATH. The isolated child fails the fixture's literal interpreter-string comparison. This is a directly observed path identity mismatch, not a missing pytest/numpy/PIL prerequisite.",
        "tests/test_task_test_prerequisites.py", "src/arcpuzzles/runtime.py"),
}
for suffix in ("lint-15", "lint-2", "selfcheck-15", "selfcheck-2"):
    specifications[f"test_foreground_signal_stops_stage_tree_checkpoints_and_resumes[{suffix}]"] = spec(
        LIVENESS, "assert all(live(pid) for pid in pids) failed before the test sends its signal.",
        "The fixture's live(pid) helper reads /proc/<pid>/stat. The current follow-up proves syscall/proc PID disagreement, so this failure is consistent with an invalid liveness observation. The recorded assertion does not establish that signal handling or checkpoint resume failed.",
        "tests/test_check_signals.py", "src/arcpuzzles/runtime.py")


def main() -> None:
    tree = ET.parse(ROOT / "repository-tests.xml")
    suites = list(tree.getroot().iter("testsuite"))
    cases = list(tree.getroot().iter("testcase"))
    log = (ROOT / "repository-tests.log").read_text()
    diagnostic = json.loads((ROOT / "repository-test-environment-diagnostic.json").read_text())
    failures, skips = [], []
    for case in cases:
        name = case.attrib["name"]
        nodeid = case.attrib["classname"].replace(".", "/") + ".py::" + name
        failure = case.find("failure")
        skipped = case.find("skipped")
        if failure is not None:
            item = dict(specifications[name])
            trace = failure.text or ""
            locations = re.findall(r"(tests/[^\s:]+\.py):(\d+):", trace)
            item.update(index=len(failures) + 1, nodeid=nodeid,
                        xml_classname=case.attrib["classname"], xml_name=name,
                        recorded_message=failure.attrib.get("message", ""),
                        traceback_sha256=hashlib.sha256(trace.encode()).hexdigest(),
                        assertion_location=("repo/" + locations[-1][0] + ":" + locations[-1][1]) if locations else None,
                        primary_evidence_paths=["checks/repository-tests.xml", "checks/repository-tests.log"])
            if item["category"] in (LIVENESS, PATH):
                item["followup_evidence_paths"] = ["checks/repository-test-environment-diagnostic.json"]
            failures.append(item)
        elif skipped is not None:
            skips.append({"nodeid": nodeid, "recorded_reason": skipped.attrib.get("message", ""),
                          "recorded_location": (skipped.text or "").strip(),
                          "category": "optional_dependency_torch_unavailable"})
    assert len(failures) == len(specifications) == 19
    assert len(skips) == 3
    assert len(cases) == 1017
    log_match = re.search(r"(\d+) failed, (\d+) passed, (\d+) skipped, (\d+) subtests passed in ([\d.]+)s", log)
    assert log_match is not None
    failed, passed, skipped, subtests = map(int, log_match.groups()[:4])
    assert (failed, passed, skipped, subtests) == (19, 995, 3, 18)
    assert all(item["nodeid"] in log for item in failures)
    category_counts = Counter(item["category"] for item in failures)
    category_explanations = {
        LIVENESS: "Twelve failures occur at process-state expectations, a /proc-based pre-signal assertion, or safe-resume liveness guards. The original failures and one current metadata probe support this classification; the twelve tests were not rerun individually.",
        SOCKET: "One original traceback directly records EPERM from the socket constructor before HTTP assertions.",
        PATH: "Two failures involve interpreter spelling. One is directly visible in retained child-test output; a metadata-only child independently reproduces the resume settings mismatch.",
        INTERFACE: "Two exact interface expectations disagree with the current richer error string or native time-budget argv. Tests mock these operations; the stale-expectation interpretation does not establish when the mismatch was introduced.",
        HISTORICAL: "Two archival expectations for other task IDs fail. Their cause and historical provenance were not resolved by a pristine baseline replay.",
    }
    evidence_names = ["repository-tests.xml", "repository-tests.log",
                      "repository-test-environment-diagnostic.py",
                      "repository-test-environment-diagnostic.json",
                      "repository-test-environment-diagnostic.command.json",
                      "repository-test-environment-diagnostic.stdout.log",
                      "repository-test-environment-diagnostic.stderr.log"]
    source_paths = sorted({path for item in failures for path in item["reviewed_source_paths"]} |
                          {"repo/tests/test_native_export.py"})
    result = {
        "schema": "arcpuzzles-repository-test-summary-v1",
        "scope": "Findings-only classification of the already recorded repository test run. No shared/task source edits and no second broad test run.",
        "counts": {
            "primary_test_cases": len(cases), "passed": passed, "failed": failed,
            "skipped": skipped, "errors": sum(int(s.attrib["errors"]) for s in suites),
            "passed_subtests_reported_separately": subtests,
            "junit_tests_attribute": sum(int(s.attrib["tests"]) for s in suites),
            "junit_testcase_elements": len(cases),
            "junit_passing_testcase_elements": sum(c.find("failure") is None and c.find("error") is None and c.find("skipped") is None for c in cases),
            "log_elapsed_seconds": float(log_match.group(5)),
            "xml_elapsed_seconds": sum(float(s.attrib["time"]) for s in suites),
            "accounting_note": "The XML suite tests attribute is 1035, while it contains 1017 testcase elements. The log's additional 18 passed subtests account for the difference; do not describe 1035 as primary tests or 1013 as passing testcase elements.",
        },
        "original_junit_suite_attributes": [s.attrib for s in suites],
        "categories": [{"id": key, "count": category_counts[key], "assessment": value}
                       for key, value in category_explanations.items()],
        "environment_evidence": {
            "process_view": diagnostic["process_view"],
            "interpreter_base_setting_differences": diagnostic["metadata_child"]["base_setting_differences"],
            "python_paths_resolve_equal": diagnostic["metadata_child"]["saved_and_child_python_resolve_equal"],
            "between_stages_child_cleanup": diagnostic["existing_suite_receipt_excerpts"]["between_stages_interruption"]["selected_fields"]["child_cleanup"],
            "isolated_dependency_preflight_passed": diagnostic["existing_suite_receipt_excerpts"]["isolated_interpreter"]["selected_fields"]["test_prerequisite_preflight"]["passed"],
            "diagnostic_command_path": "checks/repository-test-environment-diagnostic.command.json",
            "diagnostic_exit_code": 0,
        },
        "failures": failures,
        "skips": skips,
        "evidence_sha256": {"checks/" + name: sha(ROOT / name) for name in evidence_names},
        "reviewed_source_sha256": {path: sha(WORK / path) for path in source_paths},
        "limitations": [
            "No pristine-baseline full-suite rerun was performed, so this summary does not claim all failures are proven pre-existing.",
            "The environment diagnostic was run after the suite. It establishes the current process/path behavior, not each original subprocess state or a counterfactual pass for all twelve liveness tests.",
            "Apparent independence from the assigned generator edits is inferred from these assertions, fixture task aaaa00000001, other archival task IDs, and infrastructure scope. It is not a full historical attribution.",
            "No additional test run, socket request, signal operation, checkpoint resume, installation, or repository source modification was used for this classification.",
            "The original broad command/exit is not reconstructed from XML/log; the retained follow-up command receipt records its own exact argv, cwd and exit code.",
            "Torch-dependent behavior remains untested in the three skipped cases.",
        ],
    }
    json_path = ROOT / "repository-test-summary.json"
    json_path.write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# Repository test failure classification", "",
        "The recorded suite has **995 passed, 19 failed, 3 skipped, and 18 additional passed subtests**, in 404.85 seconds. There are 1,017 primary test cases and no errors. The XML contains 1,017 `<testcase>` elements, although its suite `tests` attribute is 1,035; the additional subtests explain that difference.", "",
        "This is a findings-only review of the saved suite output, relevant implementation/tests, and one small metadata diagnostic. No shared or task source was changed, and the broad suite was not rerun. **No pristine baseline full-suite comparison was made, so these failures are not all claimed to be proven pre-existing.**", "",
        "## Classification", "", "| Category | Failures | Evidence |", "|---|---:|---|",
        "| Process liveness and safe resume | 12 | Recorded unknown-state or liveness assertions; current syscall/proc PID disagreement and the implementation's explicit guard. |",
        "| Socket permission | 1 | Original traceback raises `PermissionError: [Errno 1] Operation not permitted` while creating a socket. |",
        "| Interpreter path identity | 2 | Retained isolated-test stdout and a metadata-only resume-settings comparison show equivalent paths with different spelling. |",
        "| Interface expectations | 2 | Exact regex/argv assertions disagree with current error formatting and the `--time-budget 310` argument. |",
        "| Historical expectations | 2 | Other-task archival identity and expected-rejection assertions fail; historical cause is unresolved. |", "",
        "The process diagnostic observed `os.getpid() = " + str(diagnostic["process_view"]["os_getpid"]) + "` and `/proc/self/stat` PID `" + str(diagnostic["process_view"]["proc_self_stat_pid"]) + "`; `_process_table_supported()` returned false and `_process_identity()` returned null. The retained between-stages receipt has `session_empty=false` and `remaining_processes=null`. These facts support the liveness classification, but do not constitute individual reruns of those twelve tests. The four signal variants fail before their test signal is sent.", "",
        "For interpreter identity, the saved setting ends in `WORK/repo/../.venv/bin/python`, while the metadata child reports `WORK/.venv/bin/python`. Both resolve to the same file. This is the only mismatch among the eight base settings read with the recorded resume environment. The isolated-test receipt independently shows that exact string assertion failing after dependency preflight and user-site isolation had succeeded.", "",
        "## All 19 failing tests", "", "| # | Exact test identity | Observed failure | Category |", "|---:|---|---|---|",
    ]
    labels = {LIVENESS: "Liveness", SOCKET: "Socket permission", PATH: "Interpreter path",
              INTERFACE: "Interface expectation", HISTORICAL: "Historical expectation"}
    for item in failures:
        message = item["concise_failure"].replace("|", "\\|")
        lines.append(f"| {item['index']} | `{item['nodeid']}` | {message} | {labels[item['category']]} |")
    lines.extend(["", "## Three skips", "", "All three report `could not import 'torch': No module named 'torch'`:", ""])
    lines.extend("- `" + item["nodeid"] + "`" for item in skips)
    lines.extend([
        "", "The two teacher-forcing variants skip at `tests/test_native_export.py:52`; the too-small-canvas case skips at line 100.", "",
        "## Scope and retained evidence", "",
        "The two interface mismatches use mocked operations, and the two archival mismatches concern `defba1ab4f90` and `d982cffd80f8`. Their apparent independence from the assigned generator edits follows from those scopes and fixtures; their historical pre-existence was not proven. The missing expected archival rejection does not by itself demonstrate validator bypass. The pinned-Racket resume test already passed its real Racket stage and then stopped at a liveness guard.", "",
        "Primary evidence is `checks/repository-tests.xml` and `checks/repository-tests.log`. `checks/repository-test-summary.json` retains exact XML messages, classifications, source/evidence hashes, and all test identities. The metadata script, output, stdout/stderr, and exact argv/cwd/exit receipt are retained under `checks/repository-test-environment-diagnostic.*`; the wrapper and its metadata-only child both exited 0. Selected original temporary fixture receipts are preserved as hash-bound excerpts in that diagnostic output. No extra suite, socket, signal, resume, or installation was attempted.", "",
    ])
    (ROOT / "repository-test-summary.md").write_text("\n".join(lines))
    print(json.dumps({"counts": result["counts"], "category_counts": category_counts,
                      "summary_sha256": sha(json_path),
                      "markdown_sha256": sha(ROOT / "repository-test-summary.md")}, indent=2))


if __name__ == "__main__":
    main()
