#!/usr/bin/env python3
"""Read-only final contract review for the ec9cf2c80d58 reconciliation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

WORK = Path(__file__).resolve().parents[1]
ROOT = WORK.parent
REPO = WORK / "repo"
TASK = REPO / "generators" / "ec9cf2c80d58"
CHECKS = WORK / "checks"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


checks: dict[str, object] = {}
expected_paths = {
    "WORK/repo/generators/ec9cf2c80d58/notes.md",
    "WORK/repo/generators/ec9cf2c80d58/tests/test_parametric_public_names.py",
    "WORK/repo/generators/ec9cf2c80d58/tests/test_parametric_tie_policy.py",
    "WORK/repo/generators/ec9cf2c80d58/workspace/parametric/README.md",
    "WORK/repo/generators/ec9cf2c80d58/workspace/parametric/build_evidence.py",
    "WORK/repo/generators/ec9cf2c80d58/workspace/parametric/prototype.py",
}
changed = set(run("git", "diff", "--name-only").stdout.splitlines())
assert changed == expected_paths, (changed, expected_paths)
checks["changed_paths_exact"] = sorted(changed)

diff_check = run("git", "diff", "--check")
assert diff_check.returncode == 0 and not diff_check.stdout and not diff_check.stderr
checks["git_diff_check"] = "pass"

generator_path = TASK / "generator.py"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
assert sha(generator_path) == "39cb6a9ff704cbc37689246fc0a7f2cd40a6b95de37ea6fb94fa20e8947413e9"
generator = load(generator_path, "final_review_generator")
assert generator.VERSION == "4.1.0"
assert generator.RULE_HASH == "899eb4e6a25d"
checks["canonical_source"] = {
    "generator_sha256": sha(generator_path),
    "version": generator.VERSION,
    "rule_hash": generator.RULE_HASH,
    "status": "unchanged",
}

result = json.loads((CHECKS / "task-tests-final" / "result.json").read_text())
assert result["passed"] is True and result["exit_code"] == 0
assert "74 passed" in (CHECKS / "task-tests-final-command.log").read_text()
assert "21 passed" in (CHECKS / "focused-final-command.log").read_text()
checks["tests"] = {"focused": 21, "selected_task": 74}

summary = json.loads((CHECKS / "parametric-reconciled" / "summary.json").read_text())
assert summary["status"] == "pass"
assert summary["source"]["canonical_generator_sha256"] == checks["canonical_source"]["generator_sha256"]
assert summary["source"]["canonical_rule_hash"] == "899eb4e6a25d"
assert summary["source"]["column_program_is_exact_canonical_text"] is True
assert set(summary["execution"]) == {"column", "row"}
for policy, row in summary["execution"].items():
    assert row["pair_count"] == 7
    assert row["train_count"] == 3
    assert row["query_count"] == 4
    assert row["racket_outputs_match_stored"] is True
    assert row["python_outputs_match_racket"] is True
    assert row["all_demonstrations_refute_opposite_setting"] is True
    assert row["all_queries_distinguish_opposite_setting"] is True
    assert len(row["racket_outputs"]) == 7
    assert len(row["query_distinctions"]) == 4 and all(row["query_distinctions"])
checks["live_racket"] = {"stored_labels": 14, "distinguishing_queries": 8}

sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402

public_path = CHECKS / "parametric-reconciled" / "public_challenges.json"
public = json.loads(public_path.read_text())
assert list(public) == sorted(public)
assert len(public) == 2
for name, challenge in public.items():
    expected = f"challenge-{public_challenge_id(challenge)}.json"
    assert name == expected
    exact = public_challenge_bytes(challenge)
    target = CHECKS / "parametric-reconciled" / "public" / name
    assert target.read_bytes() == exact
    assert sha(target) == name.removeprefix("challenge-").removesuffix(".json")
checks["public_files"] = sorted(public)

adversarial = json.loads((CHECKS / "reconciliation-adversarial" / "result.json").read_text())
assert adversarial["status"] == "pass"
assert adversarial["duplicate_public_payload_rejected"] is True
assert adversarial["live_racket"]["stored_labels_matched"] == 14
assert adversarial["live_racket"]["queries_distinguishing_opposite_policy"] == 8
for row in adversarial["historical_prefix"].values():
    assert row["historical_prefix_unchanged"] is True
    assert row["appended_distinct_queries"] == 3
    assert row["all_episode_inputs_distinct"] is True
checks["adversarial_probe"] = "pass"

results = json.loads((WORK / "RESULTS.json").read_text())
assert results["completion_state"] == "complete"
assert results["remaining_failures"] == []
assert len(results["supplementary_tickets"]) == 2
assert {row["ticket_id"] for row in results["supplementary_tickets"]} == {
    "ticket-16a62c09f4d34023", "ticket-416ba66cf5d94b46"
}
assert all(row["status"] == "completed" for row in results["supplementary_tickets"])
for row in results["supplementary_tickets"]:
    for relative in row["evidence_paths"]:
        assert (WORK / relative).is_file(), relative

replay = json.loads((CHECKS / "tickets" / "ticket-16a62c09f4d34023" / "replay-result.json").read_text())
assert replay["status"] == "reproduced"
assert replay["replay"]["rotation_hook_warnings"] == 9
assert replay["replay"]["rotations"] == 15
assert replay["scope"].endswith("audit remains needs_triage.")

nvarc_row = next(row for row in results["supplementary_tickets"] if row["type"] == "nvarc_visual")
assessment = json.loads((CHECKS / "tickets" / "ticket-416ba66cf5d94b46" / "assessment.json").read_text())
assert nvarc_row["nvarc_review"]["verdict"] == "ambiguous"
assert nvarc_row["nvarc_review"]["predicted_ok"] is False
assert nvarc_row["nvarc_review"]["bad_pairs"] == assessment["bad_pairs"]
assert assessment["blind_pairs_exact"] == [0, 1, 2, 3]
assert assessment["pair4_different_cells"] == 23
checks["supplementary_tickets"] = {
    "audit_replay": "reproduced_needs_triage",
    "nvarc_visual": "ambiguous_locked_prediction_failed",
}

assert not (WORK / "AUDIT.md").exists()
review = (WORK / "REVIEW.md").read_text()
feedback = (WORK / "FEEDBACK_TO_CODEX.md").read_text()
assert "Reference-rule changes: none." in review
assert "Disposition: routine" in review
assert "Biggest avoidable friction:" in feedback
checks["documents"] = "pass"

print(json.dumps({
    "schema": "ec9cf2c80d58-final-self-review-v1",
    "status": "pass",
    "reviewer": "self-review (no independent subagent available)",
    "checks": checks,
    "findings": {"critical": [], "important": [], "minor": []},
    "assessment": "Ready to package as a task-local delta; no production or canonical authority changed.",
}, indent=2, sort_keys=True))
