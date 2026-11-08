#!/usr/bin/env python3
"""Recheck the compact ARCpuzzles review handoff without regenerating evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "src"))

from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402

TASK_ID = "74a14031dc79"
GENERATOR_SHA = "11a12a0ad29bcf2ddc4bd744b1fc34ab0e1cf6fb30bf3ae9f966eaa8ca8078a3"
EXPECTED_CHANGED = {
    f"repo/generators/{TASK_ID}/notes.md",
    f"repo/generators/{TASK_ID}/tests/test_parametric_occupancy_rule.py",
    f"repo/generators/{TASK_ID}/workspace/parametric/README.md",
    f"repo/generators/{TASK_ID}/workspace/parametric/prototype.py",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_prototype():
    path = REPO / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("delivery_parametric_prototype", path)
    require(spec is not None and spec.loader is not None, "cannot import prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def changed_source_paths() -> list[str]:
    assignment = load_json(WORK / "ASSIGNMENT.json")
    changed: set[str] = set()
    for rel, baseline_digest in assignment["baseline_sha256"].items():
        path = WORK / rel
        if path.is_file() and sha(path) != baseline_digest:
            changed.add(rel)
    home = WORK / f"repo/generators/{TASK_ID}"
    for path in home.rglob("*"):
        if not path.is_file() or any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        rel = path.relative_to(WORK).as_posix()
        if rel not in assignment["baseline_sha256"]:
            changed.add(rel)
    return sorted(changed)


def verify_manifest(root: Path) -> int:
    manifest = load_json(root / "manifest.json")
    rows = manifest["files"]
    for row in rows:
        path = root / row["path"]
        require(path.is_file(), f"manifest member missing: {row['path']}")
        require(sha(path) == row["sha256"], f"manifest digest mismatch: {row['path']}")
    return len(rows)


def verify() -> dict[str, Any]:
    prototype = load_prototype()
    generator_path = REPO / f"generators/{TASK_ID}/generator.py"
    require(sha(generator_path) == GENERATOR_SHA, "production generator changed")
    require(changed_source_paths() == sorted(EXPECTED_CHANGED), "unexpected changed source scope")

    evidence = WORK / "checks/parametric/occupancy-rule-v2"
    report = load_json(evidence / "report.json")
    require(report["prototype_version"] == "proposed-occupancy-rule-v2", "wrong prototype version")
    require(report["counts"] == {
        "ambiguous_parameter_rivals": 0,
        "canonical_pairs_checked": 6,
        "episode_settings_exercised": 3,
        "episodes": 3,
        "parameter_rival_episode_checks": 9,
        "query_pairs": 12,
        "settings_exercised": 3,
        "train_pairs": 9,
    }, "unexpected retained evidence counts")
    require({row["parameters"]["occupancy_rule"] for row in report["episodes"]} == {"or", "xor", "and"},
            "retained episodes do not cover all settings")
    require([row["public_id"] for row in report["episodes"]] == sorted(row["public_id"] for row in report["episodes"]),
            "episode rows are not sorted by public ID")

    public_ids: set[str] = set()
    for row in report["episodes"]:
        public_path = evidence / row["public_path"]
        private_path = evidence / row["private_path"]
        public = load_json(public_path)
        private = load_json(private_path)
        expected_public = prototype.public_challenge(private)
        require(public == expected_public, f"public/private projection mismatch: {row['public_id']}")
        visible = public_challenge_bytes(public)
        public_id = public_challenge_id(public)
        require(public_path.read_bytes() == visible, f"noncanonical public bytes: {public_path.name}")
        require(public_path.name == f"challenge-{public_id}.json", f"filename is not visible-byte hash: {public_path.name}")
        require(row["public_id"] == public_id, f"row public ID mismatch: {public_path.name}")
        require(public_id not in public_ids, f"duplicate public ID: {public_id}")
        public_ids.add(public_id)
        require(len(public["train"]) == row["n_train"] == 3, "wrong demonstration count")
        require(len(public["test"]) == row["n_test"] == 4, "wrong query count")
        require(all("output" not in pair for pair in public["test"]), "public query answer leaked")
        require(all("output" in pair for pair in private["test"]), "private query answer missing")
        require(not private["ambiguities"], "retained finite-rule ambiguity")

    source_rows = {row["path"]: row for row in report["sources"]}
    prototype_rel = f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    test_rel = f"generators/{TASK_ID}/tests/test_parametric_occupancy_rule.py"
    require(source_rows[prototype_rel]["sha256"] == sha(REPO / prototype_rel), "prototype source binding mismatch")
    require(source_rows[test_rel]["sha256"] == sha(REPO / test_rel), "test source binding mismatch")
    require((evidence / source_rows[prototype_rel]["snapshot"]).read_bytes() == (REPO / prototype_rel).read_bytes(),
            "prototype snapshot differs")
    require((evidence / source_rows[test_rel]["snapshot"]).read_bytes() == (REPO / test_rel).read_bytes(),
            "test snapshot differs")
    require(source_rows[f"generators/{TASK_ID}/generator.py"]["sha256"] == GENERATOR_SHA,
            "report generator binding mismatch")

    adversarial = load_json(WORK / "checks/parametric/occupancy-rule-v2-adversarial/result.json")
    require(adversarial["status"] == "pass", "main adversarial probe did not pass")
    require(adversarial["distinct_inputs"] == 24 and adversarial["n_train"] == adversarial["n_test"] == 12,
            "main adversarial boundary was not 12+12 distinct")
    require(adversarial["all_inputs_have_complete_truth_table"], "incomplete truth-table input")
    require(adversarial["private_metadata_and_query_answer_invariant"], "public ID changed under private mutation")
    require(adversarial["duplicate_visible_id_rejected"], "duplicate visible ID was not rejected")
    require(adversarial["prototype_sha256"] == sha(REPO / prototype_rel), "adversarial source binding mismatch")

    ticket1 = load_json(WORK / "checks/tickets/ticket-a3f2df44fc733942/verification.json")
    require(ticket1["status"] == "finding" and ticket1["default_rival_matches"] == ticket1["default_draws"] == 120,
            "adversarial ticket receipt mismatch")
    require(ticket1["racket_matches_intended"] and ticket1["rival_differs_on_witness"],
            "adversarial ticket witness was not separated")
    ticket2 = load_json(WORK / "checks/tickets/ticket-9ac3c5812b351b75/verification.json")
    require(ticket2["status"] == "completed" and ticket2["complete_four_query_episodes"] == 3,
            "allocation ticket receipt mismatch")
    require(ticket2["distinct_labelled_queries"] == 12 and ticket2["sampling_rejections"] == 0,
            "allocation ticket query/rejection counts mismatch")
    require(ticket2["source_and_rule_bindings_match"], "allocation ticket source binding mismatch")

    return {
        "schema": "arcpuzzles-review-delivery-verification-v1",
        "status": "pass",
        "task_id": TASK_ID,
        "production_generator_sha256": GENERATOR_SHA,
        "changed_source_paths": changed_source_paths(),
        "retained_evidence": {
            "manifest_members": verify_manifest(evidence),
            "episodes": 3,
            "demonstrations": 9,
            "queries": 12,
            "public_ids": sorted(public_ids),
            "finite_rival_ambiguities": 0,
            "canonical_replays": 6,
        },
        "adversarial_boundary": {"n_train": 12, "n_test": 12, "distinct_inputs": 24},
        "supplementary_tickets": {
            "ticket-a3f2df44fc733942": "finding",
            "ticket-9ac3c5812b351b75": "completed",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = verify()
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
