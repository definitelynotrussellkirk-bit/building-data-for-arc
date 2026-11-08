"""One bounded replay of the pinned, retained admission-policy proposal.

Only the proposal script's report destination is adapted. Scoring logic,
generator source and retained labels are unchanged; no Racket is started.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback


TICKET_ID = "ticket-2e57f9b650066ba5"
AUTHORING_START = "2026-10-23T09:45:35+00:00"
EVIDENCE = Path(__file__).resolve().parent
WORK = EVIDENCE.parents[2]
REPO = WORK / "repo"
COMMAND = ("timeout 120s python3 review.py run python3 "
           "../checks/tickets/ticket-2e57f9b650066ba5/reproduce.py")


def digest(body):
    return hashlib.sha256(body).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    started = time.monotonic()
    report = {
        "ticket_id": TICKET_ID, "type": "tool_reproduction",
        "consumer": "existing_tool_request_disposition",
        "command": COMMAND, "command_cwd": "outer extraction directory",
        "targeted_probes": 1, "probe_timeout_seconds": 120,
        "authoring_started_utc": AUTHORING_START,
        "probe_started_utc": datetime.now(timezone.utc).isoformat(),
        "source_bindings": [], "racket_executions_this_probe": 0,
        "limitations": [
            "Retained Racket-labeled fixture reused; its labels were not freshly executed.",
            "One retained lesson with three demos and one query; no broad generator census.",
            "This probes worker.lesson_check policy, not an end-to-end dataset or training admission.",
            "No shared source, request status, approval or training admission was changed.",
        ],
    }
    def bind(relative, expected=None):
        body = (WORK / relative).read_bytes()
        value = {"path": relative, "sha256": digest(body), "bytes": len(body)}
        if expected is not None:
            value.update(expected_sha256=expected, matches_pin=digest(body) == expected)
        report["source_bindings"].append(value)
        if expected is not None and digest(body) != expected:
            raise ValueError(f"pinned source mismatch: {relative}")
        return body

    def timed_out(signum, frame):
        raise TimeoutError("targeted probe reached 115-second internal limit")

    previous_handler = signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(115)
    stdout = io.StringIO()
    exit_code = 0
    try:
        ticket = next(row for row in json.loads((WORK / "AUDIT_ASSIGNMENT.json").read_text())["tickets"]
                      if row["ticket_id"] == TICKET_ID)
        report["pinned_ticket"] = ticket
        suggestions = json.loads(bind(ticket["request_source"]["path"],
                                     ticket["request_source"]["sha256"]))
        request = next(row for row in suggestions["items"] if row["request_id"] == ticket["request_id"])
        request_hash = digest(json.dumps(request, sort_keys=True, separators=(",", ":")).encode())
        report["request"] = request
        report["request_sha256"] = request_hash
        report["request_hash_matches_pin"] = request_hash == ticket["request_sha256"]
        if request_hash != ticket["request_sha256"]:
            raise ValueError("pinned request record changed")
        assets = json.loads(bind(ticket["assets_manifest"]["path"], ticket["assets_manifest"]["sha256"]))
        for asset in assets["files"]:
            bind("repo/" + asset["path"], asset["sha256"])
        bind(f"repo/generators/{ticket['task_id']}/generator.py", ticket["generator_sha256"])
        for relative in ("repo/src/arcpuzzles/worker.py", "repo/shared/runtime/reviewer_support.py",
                         "checks/tickets/" + TICKET_ID + "/reproduce.py"):
            bind(relative)
        retained_report_path = REPO / "shared/tools/proposals/6416660230840310/checks/admission-policy-probe.json"
        retained_report = json.loads(retained_report_path.read_text())
        fixture_path = f"repo/generators/{ticket['task_id']}/counterexamples/singleton-marker-lesson.json"
        fixture = json.loads(bind(fixture_path, retained_report["counterexample_sha256"]))
        report["materialized_counts"] = {"train": len(fixture["train"]), "test": len(fixture["test"])}
        rules = []
        with (REPO / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    if row.get("task_id") == ticket["rule_task_id"]:
                        rules.append(row["program_solution"])
        if len(rules) != 1:
            raise ValueError("canonical rule authority not unique")
        rule_sha = digest(rules[0].encode())
        report["canonical_rule"] = {"task_id": ticket["rule_task_id"], "sha256": rule_sha,
                                     "short_hash_matches_pin": rule_sha[:12] == ticket["rule_hash"]}
        if rule_sha[:12] != ticket["rule_hash"]:
            raise ValueError("pinned canonical rule changed")

        proposal = REPO / "shared/tools/proposals/6416660230840310/checks/admission-policy-probe.py"
        source = proposal.read_text(encoding="utf-8")
        old_destination = 'Path("../checks/admission-policy-probe.json")'
        if source.count(old_destination) != 1:
            raise ValueError("retained probe output destination is not the expected unique literal")
        adapted = source.replace(old_destination, "Path(__ticket_output_path)")
        report["output_only_adaptation"] = {"original_expression": old_destination,
                                            "replacement_expression": "Path(__ticket_output_path)",
                                            "adapted_source_sha256": digest(adapted.encode())}
        sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
        os.chdir(REPO)
        with redirect_stdout(stdout):
            exec(compile(adapted, str(proposal), "exec"),
                 {"__name__": "__main__", "__file__": str(proposal),
                  "__ticket_output_path": str(EVIDENCE / "reproduced-policy-probe.json")})
        actual = json.loads((EVIDENCE / "reproduced-policy-probe.json").read_text())
        report["reproduced_report_sha256"] = digest((EVIDENCE / "reproduced-policy-probe.json").read_bytes())
        report["same_result_as_retained_report"] = actual == retained_report
        report["result"] = {
            "uncontracted_automatic": actual["uncontracted_automatic"]["status"],
            "explicit_demo_count": actual["contracted_explicit_demo_count"]["status"],
            "automatic_demo_count_raises": actual["contracted_automatic"]["raised"],
            "query_disagreement_reasons": actual["contracted_explicit_demo_count"]["queries"],
        }
        report["status"] = "completed"
        report["proposed_disposition"] = (
            "Retain the existing accepted request as pending shared implementation. The pinned "
            "worker policy behavior reproduces: missing evidence is not_declared, explicit counts "
            "retain diagnostic_unsupported, and automatic counts raise. A distinct admission gate "
            "should require complete source-bound rival evidence on every actual query, while "
            "allowing demo survivors that predict the same query answer. The probe does not "
            "establish that any dataset was admitted or that a boundary fix is implemented.")
    except BaseException as error:
        exit_code = 1
        report.update(status="blocked", error=f"{type(error).__name__}: {error}",
                      traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
        report["exit_code"] = exit_code
        report["probe_elapsed_seconds"] = round(time.monotonic() - started, 6)
        now = datetime.now(timezone.utc)
        report["finished_utc"] = now.isoformat()
        report["elapsed_minutes"] = round((now - datetime.fromisoformat(AUTHORING_START)).total_seconds() / 60, 4)
        (EVIDENCE / "stdout.txt").write_text(stdout.getvalue(), encoding="utf-8")
        write_json(EVIDENCE / "evidence.json", report)
    print(json.dumps({key: report[key] for key in ("ticket_id", "status", "exit_code",
                                                  "probe_elapsed_seconds", "elapsed_minutes")}, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
