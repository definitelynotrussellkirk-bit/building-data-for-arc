from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "0c2ab7de69d1"
SOURCE_SHA = "aae633b9d9b4dd317998f47490cd9b84b8ce701bc6c91d4fcc48e8ca5e6c6d75"
RULE_HASH = "ca5f7e2b1e40"
RETAINED_ROOT = (
    REPO
    / "generators"
    / TASK
    / "counterexamples"
    / "review-529f49df89b85e1d-v0001"
)
RETAINED = RETAINED_ROOT / "retained" / "checks" / "audit" / TASK


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    source = REPO / "generators" / TASK / "generator.py"
    if sha256(source) != SOURCE_SHA:
        raise AssertionError("pinned generator source hash changed")

    manifest = load_json(RETAINED_ROOT / "audit_assets.json")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != 8:
        raise AssertionError("expected exactly eight pinned audit asset files")
    for entry in files:
        path = REPO / entry["path"]
        if sha256(path) != entry["sha256"]:
            raise AssertionError(f"asset hash mismatch: {entry['path']}")

    for name in ("input.json", "rival_outputs.json", "search_report.json"):
        if (HERE / name).read_bytes() != (RETAINED / name).read_bytes():
            raise AssertionError(f"regenerated witness differs from retained {name}")

    search = load_json(HERE / "search_report.json")
    if search["seed"] != 0 or search["difficulty"] != "medium":
        raise AssertionError("unexpected retained witness seed/difficulty")
    if search["demonstrations_fit_rival_python_mirror"] != [True, True, True]:
        raise AssertionError("rival no longer fits all demonstrations")
    if search["query_disagrees_python_mirror"] is not True:
        raise AssertionError("query no longer refutes rival")
    if search["all_inputs_pass_self_check"] is not True:
        raise AssertionError("retained witness is not lawful")

    inputs = load_json(HERE / "input.json")
    rivals = load_json(HERE / "rival_outputs.json")
    racket = load_json(RETAINED / "racket.json")
    if racket["generator_sha256"] != SOURCE_SHA:
        raise AssertionError("retained Racket receipt has wrong generator hash")
    if racket["executed_rule_hash"] != RULE_HASH:
        raise AssertionError("retained Racket receipt has wrong executed rule hash")
    if racket["catalog_rule_hash"] != RULE_HASH or racket["rule_hash_matches_catalog"] is not True:
        raise AssertionError("retained Racket receipt does not match catalog rule")
    if [result["input"] for result in racket["results"]] != inputs:
        raise AssertionError("retained Racket inputs do not match regenerated witness")
    if not all(result["valid_output"] and result["error"] is None for result in racket["results"]):
        raise AssertionError("retained Racket receipt contains invalid output")

    outputs = [result["output"] for result in racket["results"]]
    differences: list[list[list[int]]] = []
    agreements: list[bool] = []
    for expected, rival in zip(outputs, rivals, strict=True):
        cells = [
            [row, col, expected[row][col], rival[row][col]]
            for row in range(len(expected))
            for col in range(len(expected[row]))
            if expected[row][col] != rival[row][col]
        ]
        differences.append(cells)
        agreements.append(not cells)

    expected_query_differences = [[6, 1, 5, 8], [6, 2, 5, 8], [6, 3, 5, 8]]
    if agreements[:3] != [True, True, True] or agreements[3] is not False:
        raise AssertionError("retained authority no longer shows demonstration-only ambiguity")
    if differences[3] != expected_query_differences:
        raise AssertionError("retained authority query differences changed")

    receipt = {
        "authority": {
            "demonstration_agreements": agreements[:3],
            "generator_sha256_matches": True,
            "inputs_match_regenerated_witness": True,
            "outputs_valid": True,
            "query_agreement": agreements[3],
            "query_differences": differences[3],
            "racket_asset_sha256": sha256(RETAINED / "racket.json"),
            "rule_hash_matches_catalog": True,
            "status": "pinned_protected_racket_receipt_verified_live_replay_blocked",
        },
        "generator_sha256": SOURCE_SHA,
        "limitations": [
            "Live authority replay was not retried after the single bounded probe: source-tree runner expected puzzle_generators/per_puzzle/0c2ab7de69d1, which is only constructed by a staged runtime. The exact regenerated inputs were instead checked against the pinned protected-Racket receipt bound to the same generator SHA and canonical rule hash.",
            "One deterministic four-pair lesson witness; no peer battery or census.",
            "Finding remains source-bound and requires maintainer triage.",
        ],
        "pinned_asset_files_verified": len(files),
        "plausible_shortcut": "Reflect every eligible above-divider source even when its reflected destination is occupied.",
        "retained_witness_reproduced_byte_exact": True,
        "rule_hash": RULE_HASH,
        "schema": "arcpuzzles-ticket-adversarial-witness-v1",
        "single_probe_outcome": "Regenerated retained witness exactly; optional live authority step hit unstaged runner import boundary.",
        "status": "finding",
        "task_id": TASK,
        "ticket_id": HERE.name,
        "witness": {
            "all_inputs_lawful": True,
            "demonstrations": [0, 1, 2],
            "demos_fit_rival": [True, True, True],
            "difficulty": "medium",
            "query": 3,
            "query_differences": differences[3],
            "query_refutes_rival": True,
            "seed": 0,
        },
    }
    (HERE / "receipt.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "asset_files_verified": len(files),
                "query_differences": differences[3],
                "status": "finding",
                "ticket_id": HERE.name,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
