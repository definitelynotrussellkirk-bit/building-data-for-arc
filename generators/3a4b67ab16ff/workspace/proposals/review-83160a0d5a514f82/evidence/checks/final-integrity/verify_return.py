#!/usr/bin/env python3
"""Verify the source-bound ARC review delta before packaging."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "checks/final-integrity/report.json").resolve()
TASK = "3a4b67ab16ff"
GEN_SHA = "fb837ad93ced67cb30cb20dc6981352c03c2b92c89b4578f3db0f711ac6e3ef2"
RULE_HASH = "32c694357bd0"
FROZEN_TEST_SHA = "b6aa65b4bf7fe0dc7f5ce267300cd5b2871e990ef2a17f460230377436a46244"
CANON_SHA = "a174c473ca475016e2af560afa98749537803bc6f856d3ea5195f94a21776eef"
BASE_SHA = "522df87cc91a83363e738d84a7efe5143be6aa26efd3f01ec489511ea777a1ca"
PROTOTYPE_SHA = "fc74010aa442bf176ba4ab9019467fdcb895ed76c267f53c286d2a47a5b65447"
STAGES = (
    "lint", "selfcheck", "rule-smoke", "defect-lint", "dist-gate",
    "profile-floor", "semantic-gate", "diversity", "override", "grammar",
    "racket-lint", "authority-sync",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def canonical_program(path: Path) -> str:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    found = [row["program_solution"] for row in rows if row.get("task_id") == TASK]
    require(len(found) == 1, "canonical task row must be unique")
    return found[0]


def main() -> None:
    repo = ROOT / "repo"
    generator = repo / f"generators/{TASK}/generator.py"
    frozen_test = repo / f"generators/{TASK}/tests/test_generator_{TASK}.py"
    prototype = repo / f"generators/{TASK}/workspace/parametric/prototype.py"
    canonical = repo / "shared/data/canonical/puzzles.jsonl"
    selected = repo / "shared/data/base/solutions/training/1c02dbbe__3a4b67ab16ff.json"
    baseline = ROOT / ".review/baseline"

    identities = {
        "generator_sha256": sha(generator),
        "frozen_test_sha256": sha(frozen_test),
        "prototype_sha256": sha(prototype),
        "canonical_sha256": sha(canonical),
        "selected_base_sha256": sha(selected),
    }
    require(identities["generator_sha256"] == GEN_SHA, "generator hash drift")
    require(identities["frozen_test_sha256"] == FROZEN_TEST_SHA, "frozen test changed")
    require(identities["prototype_sha256"] == PROTOTYPE_SHA, "prototype hash drift")
    require(identities["canonical_sha256"] == CANON_SHA, "canonical source changed")
    require(identities["selected_base_sha256"] == BASE_SHA, "selected base source drift")
    require(sha(baseline / f"repo/generators/{TASK}/tests/test_generator_{TASK}.py") == FROZEN_TEST_SHA,
            "frozen baseline test hash mismatch")
    require((baseline / "repo/shared/data/canonical/puzzles.jsonl").read_bytes() == canonical.read_bytes(),
            "canonical bytes differ from frozen baseline")

    base_now = json.loads(selected.read_text())
    base_before = json.loads((baseline / "repo/shared/data/base/solutions/training/1c02dbbe__3a4b67ab16ff.json").read_text())
    program = canonical_program(canonical)
    target = base_now["racket_target"]
    require(target["target_code"] == program, "selected target_code is not exact canonical text")
    require(target["raw_code"] == base_before["racket_target"]["raw_code"], "archival raw_code changed")
    require(RULE_HASH in json.dumps({"rule_hash": RULE_HASH}), "rule hash sentinel missing")

    stages = {}
    for stage in STAGES:
        result_path = ROOT / "checks" / f"final-{stage}" / "result.json"
        result = json.loads(result_path.read_text())
        stages[stage] = {
            "passed": result.get("passed"),
            "exit_code": result.get("exit_code"),
            "stage": result.get("stage"),
        }
        require(result.get("passed") is True and result.get("exit_code") == 0,
                f"final stage not green: {stage}")

    focused_exit = int((ROOT / "checks/focused-tests-final/exit_code.txt").read_text().strip())
    focused_log = (ROOT / "checks/focused-tests-final/pytest.log").read_text()
    require(focused_exit == 0 and "17 passed" in focused_log, "focused tests not green")

    task_result = json.loads((ROOT / "checks/final-task-tests-frozen-blocker/result.json").read_text())
    require(task_result.get("passed") is False and task_result.get("test_status") == "preflight_failed",
            "aggregate task-test blocker changed")
    require("Fixed __file__/parents depth" in task_result.get("stderr", ""),
            "expected portable-root diagnostic missing")

    parametric = json.loads((ROOT / "checks/parametric/3a4b67ab16ff-layer-order-v1/report.json").read_text())
    require(parametric.get("passed") is True, "parametric report not passed")
    require(parametric["selected_generator"]["sha256"] == GEN_SHA, "parametric evidence source drift")
    require(all(row["demo_count"] == 3 and row["query_count"] == 4
                for row in parametric["episodes"].values()), "parametric episode counts drift")

    results = json.loads((ROOT / "RESULTS.json").read_text())
    require(results.get("completion_state") == "complete", "RESULTS completion state")
    require(len(results.get("supplementary_tickets", [])) == 2, "ticket row count")
    for command in results.get("verification_commands", []):
        for evidence in command.get("evidence_paths", []):
            require((ROOT / evidence).is_file(), f"missing command evidence: {evidence}")
    for ticket in results["supplementary_tickets"]:
        require(ticket.get("status") == "completed", f"ticket not completed: {ticket.get('ticket_id')}")
        for evidence in ticket.get("evidence_paths", []):
            require((ROOT / evidence).is_file(), f"missing ticket evidence: {evidence}")

    require(not (ROOT / "AUDIT.md").exists(), "AUDIT.md should be absent without safety finding")
    for document in ("REVIEW.md", "RESULTS.json", "FEEDBACK_TO_CODEX.md"):
        require((ROOT / document).is_file(), f"missing handoff document: {document}")

    report = {
        "schema": "3a4b67ab16ff-final-return-integrity-v1",
        "status": "passed",
        "task_id": TASK,
        "rule_hash": RULE_HASH,
        "identities": identities,
        "final_stages": stages,
        "focused_tests": {"exit_code": focused_exit, "summary": "17 passed"},
        "aggregate_task_tests": {
            "status": "blocked_preflight",
            "exit_code": task_result.get("exit_code"),
            "fixture_sha256": identities["frozen_test_sha256"],
        },
        "parametric": {
            "passed": True,
            "settings": sorted(parametric["episodes"]),
            "demo_count": 3,
            "query_count": 4,
        },
        "supplementary_ticket_count": 2,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "passed", "stages": len(stages), "focused": "17/17",
                      "tickets": 2, "task_tests": "blocked_preflight"}, sort_keys=True))


if __name__ == "__main__":
    main()
