#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

from arc_repl.isolated_verifier import Limits, verify_candidate
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root

TICKET_ID = "ticket-65c6ca1849518171"
TASK_ID = "ebe910be6876"
REQUEST_ID = "review-e2074fc131195d42:v0001:F2"
ROOT = find_root(__file__)
OUT = Path(__file__).with_name("result.json")
ASSET_DIR = ROOT / "shared/tools/proposals/c1b1da5f2c8fd554"
MANIFEST = ASSET_DIR / "manifest.json"
FAILURE = ASSET_DIR / "checks/parametric/ebe910be6876-racket-initial-failure.json"
FINAL = ASSET_DIR / "checks/parametric/ebe910be6876-magnification.json"
GENERATOR = ROOT / "generators/ebe910be6876/generator.py"
PROTOTYPE = ROOT / "generators/ebe910be6876/workspace/parametric/prototype.py"
VERIFY_SOURCE = ROOT / "generators/ebe910be6876/workspace/parametric/verify.py"

PINNED = {
    "manifest": "1db78b19c9b87b5cdb521b641c5bdd29f303c8cd0284a675937cb312c89862dd",
    "generator": "783376dcfb80920ccdbb3f8d2e1a3431655eb57581c540fbc3c9b2d5fda11056",
    "failure": "1d2840ad1036f03cd2d38db772cf8d13fa64ea92d4621c9ac526cf06d8b9717a",
    "final": "5132152c02cdf07d5911f27eee6b01830a64708cd764995b5989f3870518de4d",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_prototype():
    spec = importlib.util.spec_from_file_location("_ticket_ebe910be6876_proto", PROTOTYPE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    observed_hashes = {
        "manifest": sha(MANIFEST),
        "generator": sha(GENERATOR),
        "failure": sha(FAILURE),
        "final": sha(FINAL),
    }
    assert observed_hashes == PINNED
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failure = json.loads(FAILURE.read_text(encoding="utf-8"))
    final = json.loads(FINAL.read_text(encoding="utf-8"))
    assert manifest["request_id"] == REQUEST_ID
    assert failure["observed"]["error_fragment"] == "h: undefined"
    assert final["all_racket_exact"] is True

    proto = load_prototype()
    episode = proto.generate_episode(
        101,
        magnification=1,
        demo_count=1,
        query_count=1,
    )
    task = {
        "train": [episode["train"][0]],
        "test": [{"input": episode["test"][0]["input"]}],
    }
    racket_path = os.environ.get("RACKET_PATH")
    assert racket_path, "review wrapper did not activate RACKET_PATH"
    receipt = verify_candidate(
        task,
        episode["program"],
        racket_path=racket_path,
        limits=Limits(
            wall_seconds=30.0,
            step_seconds=5.0,
            cpu_seconds=20,
            memory_mb=1536,
            max_source_bytes=32768,
            max_output_bytes=1024 * 1024,
            max_grid_side=64,
            max_pairs=4,
        ),
    )
    assert receipt["status"] == "pass", receipt
    assert receipt["backend"] == "racket"
    assert receipt["input_purity"] is True
    assert receipt["test_outputs"] == [episode["test"][0]["output"]]

    verifier_text = VERIFY_SOURCE.read_text(encoding="utf-8")
    bridge_has_requested_method = hasattr(RacketBridge, "apply_rule_program")
    task_verifier_still_imports_private_parser = (
        "from puzzle_generators.generic.concepts.extraction import _program_body"
        in verifier_text
    )
    assert bridge_has_requested_method is False
    assert task_verifier_still_imports_private_parser is True

    result = {
        "schema": "arcpuzzles-tool-request-reproduction-v1",
        "ticket_id": TICKET_ID,
        "request_id": REQUEST_ID,
        "task_id": TASK_ID,
        "pinned_hashes": observed_hashes,
        "retained_failure": {
            "error_fragment": failure["observed"]["error_fragment"],
            "root_cause": failure["root_cause"],
            "final_asset_all_racket_exact": final["all_racket_exact"],
        },
        "current_probe": {
            "complete_rule_program_sha256": hashlib.sha256(
                episode["program"].encode("utf-8")
            ).hexdigest(),
            "public_verify_candidate_status": receipt["status"],
            "backend": receipt["backend"],
            "input_purity": receipt["input_purity"],
            "query_output_exact": receipt["test_outputs"]
            == [episode["test"][0]["output"]],
            "racket_bridge_has_apply_rule_program": bridge_has_requested_method,
            "retained_task_verifier_still_uses_private_program_body": (
                task_verifier_still_imports_private_parser
            ),
        },
        "proposed_disposition": {
            "action": "narrow_and_defer",
            "reason": (
                "The public isolated_verifier.verify_candidate API now accepts and "
                "successfully executes a complete materialized (rule! ...) program, "
                "so qualification-style exact replay no longer requires prototype "
                "authors to parse the wrapper. The exact requested persistent "
                "RacketBridge.apply_rule_program method is still absent, and the "
                "retained task-local verifier still imports private _program_body."
            ),
            "remaining_request": (
                "Only retain a smaller low-overhead batch-evaluation request for "
                "unlabeled grids/persistent bridges; document verify_candidate as "
                "the supported fail-closed path for labeled qualification."
            ),
        },
        "shared_changes_made": False,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
