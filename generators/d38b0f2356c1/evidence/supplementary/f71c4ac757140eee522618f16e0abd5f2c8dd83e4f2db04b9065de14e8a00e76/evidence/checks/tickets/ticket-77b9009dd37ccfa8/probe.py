#!/usr/bin/env python3
"""Source-exact replay of the retained negative-sample-index audit witness."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import load_selected_generator  # noqa: E402

TASK = "d38b0f2356c1"
EXPECTED_SOURCE = "ed0473c8a5872873ad3268da8640a840ba697dd69c2cd491f0c31ea430b6254b"
EXPECTED_MANIFEST = "8d170af6f57f17c340eff3f5cb160c9a944e4c3a0fc47fdf9676c638eb6e7b5b"
EXPECTED_INDEX = "1996416578219986389c3d336761cc4947edb8c017dde9be0e335680853b6282"
EXPECTED_RECORD = "98f0df968d4e4c076442d8fa8f8d5bf57feb941bf653cfcf146570a9a8b298c5"
RETURN_ID = "review-24c37bc1b0e2c645:v0001"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_hash(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def run_case(module, name: str, sample_index: int) -> dict:
    row = {"case": name, "seed": 123, "sample_index": sample_index, "difficulty": "hard"}
    try:
        grid = module.generate(123, sample_index, difficulty="hard")
        row.update(
            status="accepted",
            shape=[len(grid), len(grid[0])],
            grid_sha256=grid_hash(grid),
            self_check=module.self_check(grid),
            observed_overrides=module.observe_overrides(grid),
        )
    except Exception as exc:
        row.update(status="rejected", error=f"{type(exc).__name__}: {exc}")
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)

    task = REPO / "generators" / TASK
    manifest_path = task / "counterexamples/review-24c37bc1b0e2c645-v0001/audit_assets.json"
    index_path = task / "evidence/review_index.json"
    retained_path = task / (
        "counterexamples/review-24c37bc1b0e2c645-v0001/retained/checks/audit/"
        "d38b0f2356c1/strict-scalar-probe.json"
    )
    index = json.loads(index_path.read_text())
    audit = next(row for row in index["audits"] if row["return_id"] == RETURN_ID)
    record_hash = hashlib.sha256(
        json.dumps(audit, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    retained = json.loads(retained_path.read_text())
    retained_rows = {row["case"]: row for row in retained["cases"]}

    module, source, source_hash = load_selected_generator(TASK, root=REPO)
    current = {
        "control": run_case(module, "control", 0),
        "negative_sample_index": run_case(module, "negative_sample_index", -1),
    }
    comparisons = {}
    for name, row in current.items():
        expected = retained_rows[name]
        fields = ("status", "shape", "grid_sha256", "self_check", "observed_overrides")
        comparisons[name] = {
            "fields": list(fields),
            "exact_match": all(row.get(field) == expected.get(field) for field in fields),
            "current": row,
            "retained": {field: expected.get(field) for field in fields},
        }

    identities = {
        "source_sha256": source_hash,
        "source_matches": source_hash == EXPECTED_SOURCE,
        "assets_manifest_sha256": sha(manifest_path),
        "assets_manifest_matches": sha(manifest_path) == EXPECTED_MANIFEST,
        "audit_index_sha256": sha(index_path),
        "audit_index_matches": sha(index_path) == EXPECTED_INDEX,
        "audit_record_sha256": record_hash,
        "audit_record_matches": record_hash == EXPECTED_RECORD,
        "retained_probe_source_sha256": retained.get("source_sha256"),
    }
    reproduced = (
        all(value for key, value in identities.items() if key.endswith("_matches"))
        and all(row["exact_match"] for row in comparisons.values())
        and current["negative_sample_index"].get("status") == "accepted"
        and current["negative_sample_index"].get("self_check") == []
    )
    payload = {
        "schema": "ticket-audit-replay-v1",
        "ticket_id": "ticket-77b9009dd37ccfa8",
        "task_id": TASK,
        "audit_return_id": RETURN_ID,
        "source_path": str(source.relative_to(REPO)),
        "identities": identities,
        "comparisons": comparisons,
        "claim_reproduced": reproduced,
        "disposition": (
            "The bounded negative-sample-index claim reproduced exactly; the existing audit remains unresolved."
            if reproduced
            else "The bounded claim did not reproduce exactly; maintainer assessment is still required."
        ),
        "stopping_reason": "completed the single source-exact control/witness replay",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(0 if reproduced else 1)


if __name__ == "__main__":
    main()
