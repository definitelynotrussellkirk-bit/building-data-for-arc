"""Compare saved candidate predictions with public Racket apply evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--racket", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite {args.out}")
    proposal = json.loads(args.candidates.read_text())
    reference = json.loads(args.racket.read_text())
    assert proposal["task_id"] == reference["task_id"] == "c1ae510562f9"
    assert proposal["generator_sha256"] == reference["generator_sha256"]
    assert proposal["rule_hash"] == reference["executed_rule_hash"]
    assert reference["rule_hash_matches_catalog"]
    assert len(proposal["witnesses"]) == len(reference["results"])
    fit = {name for name, status in proposal["canonical_candidate_fit"].items()
           if status["fits_all"]}
    rows = []
    for index, (case, result) in enumerate(zip(proposal["witnesses"], reference["results"])):
        assert case["input"] == result["input"]
        assert result["valid_output"] and result["error"] is None
        assert case["independent_interpretation"] == result["output"]
        refuted = [name for name, output in case["candidate_rival_outputs"].items()
                   if output != result["output"]]
        rows.append({
            "witness_index": index, "name": case["name"],
            "input_sha256": result["input_sha256"],
            "output_sha256": result["output_sha256"],
            "empty_rows": case["independent_empty_rows"],
            "racket_output": result["output"],
            "selected_self_check": case["selected_self_check"],
            "refuted_candidate_rivals": refuted,
            "refuted_canonical_fitting_rivals": sorted(fit.intersection(refuted)),
            "refutes_every_canonical_fitting_candidate": fit.issubset(refuted),
        })
    report = {
        "schema": "c1ae510562f9-semantic-reference-comparison-v1",
        "task_id": proposal["task_id"],
        "generator_sha256": proposal["generator_sha256"],
        "rule_hash": proposal["rule_hash"],
        "catalog_program_solution_sha256": proposal["rule_source_sha256"],
        "rule_text_sha256": reference["rule_text_sha256"],
        "rule_identity_note": (
            "Catalog program_solution bytes and executed rule text bytes have separate SHA-256 values; "
            "the public apply receipt confirms its executed rule hash matches the catalog authority."
        ),
        "candidate_report_sha256": digest(args.candidates),
        "racket_receipt_sha256": digest(args.racket),
        "canonical_fitting_candidates": sorted(fit),
        "witnesses": rows,
        "status": "all_four_reference_outputs_match_independent_interpretation",
        "limits": "Four authored inputs; no production lesson sampling or universal identifiability claim.",
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "witnesses": [
        {"name": row["name"], "empty_rows": row["empty_rows"],
         "canonical_fitting_candidates_refuted": len(row["refuted_canonical_fitting_rivals"])}
        for row in rows]}, indent=2))


if __name__ == "__main__":
    main()
