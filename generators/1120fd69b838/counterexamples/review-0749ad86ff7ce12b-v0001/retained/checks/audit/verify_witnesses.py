"""Recompute the two final audit witnesses with each task's Racket authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog

ROOT = Path.cwd()
AUDIT_ROOT = ROOT.parent / "checks" / "audit"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_transform_gap(catalog: Catalog) -> dict:
    task_id = "1120fd69b838"
    path = AUDIT_ROOT / task_id / "authority-transform-gap-witness.json"
    witness = json.loads(path.read_text())
    pairs = witness["mismatching_generated_pairs"]
    receipt = catalog.apply(task_id, [p["input"] for p in pairs], reference="canonical", timeout=300)
    actual = [item["output"] for item in receipt["results"]]
    expected = [p["racket_output"] for p in pairs]
    alternatives = [p["full_dihedral_output"] for p in pairs]
    errors = [item["error"] for item in receipt["results"]]
    verified = (
        bool(pairs)
        and all(error is None for error in errors)
        and actual == expected
        and all(a != b for a, b in zip(expected, alternatives))
    )
    return {
        "schema": "audit-racket-verification-v1",
        "task_id": task_id,
        "witness_path": str(path.relative_to(ROOT.parent)),
        "witness_sha256": sha256(path),
        "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
        "result_count": len(actual),
        "errors": errors,
        "all_saved_authority_outputs_reproduced": actual == expected,
        "all_full_dihedral_outputs_differ": all(a != b for a, b in zip(expected, alternatives)),
        "verified": verified,
    }


def verify_first_rect(catalog: Catalog) -> dict:
    task_id = "05a9779042f4"
    path = AUDIT_ROOT / task_id / "first-rect-shortcut-witness.json"
    witness = json.loads(path.read_text())
    labelled = [*witness["demos"], witness["query"]]
    receipt = catalog.apply(task_id, [p["input"] for p in labelled], reference="canonical", timeout=300)
    actual = [item["output"] for item in receipt["results"]]
    expected = [p["output"] for p in labelled]
    rival = [p["rival_output"] for p in labelled]
    errors = [item["error"] for item in receipt["results"]]
    demos_fit = all(a == b for a, b in zip(expected[:-1], rival[:-1]))
    query_separates = expected[-1] != rival[-1]
    verified = all(error is None for error in errors) and actual == expected and demos_fit and query_separates
    return {
        "schema": "audit-racket-verification-v1",
        "task_id": task_id,
        "witness_path": str(path.relative_to(ROOT.parent)),
        "witness_sha256": sha256(path),
        "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
        "result_count": len(actual),
        "errors": errors,
        "all_saved_canonical_outputs_match_racket": actual == expected,
        "rival_fits_all_demos": demos_fit,
        "rival_changes_query": query_separates,
        "verified": verified,
    }


def main() -> int:
    catalog = Catalog(ROOT)
    records = [verify_transform_gap(catalog), verify_first_rect(catalog)]
    for record in records:
        out = AUDIT_ROOT / record["task_id"] / "racket-verification.json"
        out.write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record, sort_keys=True))
    return int(not all(record["verified"] for record in records))


if __name__ == "__main__":
    raise SystemExit(main())
