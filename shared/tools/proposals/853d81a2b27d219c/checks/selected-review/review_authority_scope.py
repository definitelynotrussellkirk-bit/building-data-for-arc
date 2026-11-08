"""Review a saved selected-authority proposal without modifying repository source."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys


def sha(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--proposal", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles.authority_sync import _replace_target
    from arcpuzzles.review_full_return import _allowed

    proposal = json.loads(args.proposal.read_text())
    contract = json.loads((repo.parent / "ASSIGNMENT.json").read_text())
    task_id = contract["task_id"]
    canonical = next(
        row["program_solution"]
        for row in map(json.loads, (repo / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
        if row.get("task_id") == task_id
    )
    inspected = []
    for proposed in proposal["files"]:
        path = repo / proposed["path"]
        original = path.read_bytes()
        row = json.loads(original)
        candidate = _replace_target(original.decode(), row["racket_target"]["target_code"], canonical)
        after = json.loads(candidate)
        expected = copy.deepcopy(row)
        expected["racket_target"]["target_code"] = canonical
        checks = {
            "old_hash_matches_proposal": sha(original) == proposed["old_sha256"],
            "new_hash_matches_proposal": sha(candidate) == proposed["new_sha256"],
            "path_allowed_by_return_contract": _allowed("repo/" + proposed["path"], contract),
            "only_selected_target_code_changes": after == expected,
            "archival_raw_code_preserved": after["racket_target"]["raw_code"] == row["racket_target"]["raw_code"],
            "metadata_preserved": {k: v for k, v in after["racket_target"].items() if k != "target_code"}
            == {k: v for k, v in row["racket_target"].items() if k != "target_code"},
        }
        inspected.append({
            "path": proposed["path"],
            "before_sha256": sha(original),
            "proposed_after_sha256": sha(candidate),
            "archival_raw_code_sha256": sha(row["racket_target"]["raw_code"]),
            "canonicalization_status": row["racket_target"].get("canonicalization_status"),
            "checks": checks,
        })
    report = {
        "task_id": task_id,
        "generator_sha256": sha((repo / "generators" / task_id / "generator.py").read_bytes()),
        "canonical_source_sha256": sha(canonical),
        "canonical_rule_hash": sha(" ".join(canonical.split()))[:12],
        "proposal_sha256": sha(args.proposal.read_bytes()),
        "proposal_patch_sha256": sha(proposal["patch"]),
        "applied": False,
        "files": inspected,
        "passed": all(all(row["checks"].values()) for row in inspected),
        "limits": "Structural and token-equivalence proposal review only; no new Racket execution.",
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
