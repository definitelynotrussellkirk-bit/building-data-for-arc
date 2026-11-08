"""Recheck retained hashes and bounded ticket receipts before packaging."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
REPORT_PATH = ROOT / "checks/parametric/61c0bcd32328-direction-v1/report.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    report = json.loads(REPORT_PATH.read_text())
    base = REPORT_PATH.parent
    file_results = []
    for row in report["files"]:
        path = base / row["path"]
        file_results.append(
            {
                "path": row["path"],
                "exists": path.is_file(),
                "sha256_matches": path.is_file() and sha(path) == row["sha256"],
                "bytes_match": path.is_file() and path.stat().st_size == row["bytes"],
            }
        )
    public_results = []
    for path in sorted((base / "public").glob("challenge-*.json")):
        digest = sha(path)
        public_results.append(
            {
                "path": path.relative_to(base).as_posix(),
                "filename_hash_matches": path.stem.removeprefix("challenge-") == digest,
            }
        )

    replay = json.loads(
        (ROOT / "checks/tickets/ticket-26b64f8e03519161/receipt.json").read_text()
    )
    witness = json.loads(
        (ROOT / "checks/tickets/ticket-b9b6caf3ff828e0e/witness.json").read_text()
    )
    canonical = next(
        row["program_solution"]
        for row in map(
            json.loads,
            (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines(),
        )
        if row.get("task_id") == "61c0bcd32328"
    )

    result = {
        "schema": "review-final-integrity-v1",
        "selected_task": "61c0bcd32328",
        "generator_sha256": sha(REPO / "generators/61c0bcd32328/generator.py"),
        "prototype_sha256": sha(
            REPO / "generators/61c0bcd32328/workspace/parametric/prototype.py"
        ),
        "canonical_racket_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "normalized_rule_hash": hashlib.sha256(
            " ".join(canonical.split()).encode()
        ).hexdigest()[:12],
        "parametric_report_file_count": len(report["files"]),
        "parametric_files_all_match": all(
            row["exists"] and row["sha256_matches"] and row["bytes_match"]
            for row in file_results
        ),
        "public_ids_all_visible_byte_hashes": all(
            row["filename_hash_matches"] for row in public_results
        ),
        "parametric_file_checks": file_results,
        "public_id_checks": public_results,
        "audit_replay_reproduced": replay["bounded_claim_reproduced"],
        "audit_replay_source_sha256": replay["audited_generator_sha256"],
        "adversarial_witness_lawful": witness["lawful_input"],
        "adversarial_witness_racket_parity": witness["python_mirror_matches_racket"],
        "adversarial_witness_mismatch_cells": witness["mismatch_cell_count"],
    }
    result["all_core_checks"] = (
        result["generator_sha256"]
        == "4f45d334880485ba8e7926f352f6f9c919dad53df3a9b868af43703964dff4ec"
        and result["prototype_sha256"]
        == "c2d7cd2cbbbc6177d0d52b8efc4217d025357ee386dfbeb9450bc90cf2d05b14"
        and result["canonical_racket_sha256"]
        == "0dc3328fe8ad885a19f7c620a4d641ffc733e8cc641a331d01b3e88410c5f64e"
        and result["normalized_rule_hash"] == "e3835c9a174e"
        and result["parametric_files_all_match"]
        and result["public_ids_all_visible_byte_hashes"]
        and result["audit_replay_reproduced"]
        and result["adversarial_witness_lawful"]
        and result["adversarial_witness_racket_parity"]
        and result["adversarial_witness_mismatch_cells"] > 0
    )
    (Path(__file__).with_name("integrity.json")).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        key: result[key]
        for key in (
            "generator_sha256",
            "prototype_sha256",
            "canonical_racket_sha256",
            "normalized_rule_hash",
            "parametric_files_all_match",
            "public_ids_all_visible_byte_hashes",
            "audit_replay_reproduced",
            "adversarial_witness_lawful",
            "adversarial_witness_racket_parity",
            "adversarial_witness_mismatch_cells",
            "all_core_checks",
        )
    }, indent=2, sort_keys=True))
    return 0 if result["all_core_checks"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
