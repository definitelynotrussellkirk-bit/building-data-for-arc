"""Compare independent diagnostic predictions with the retained public apply receipt."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", type=Path, default=Path("checks/semantic-review/analysis.json"))
    parser.add_argument("--authority", type=Path, default=Path("checks/semantic-review/racket.json"))
    parser.add_argument("--out", type=Path, default=Path("checks/semantic-review/authority_verification.json"))
    args = parser.parse_args()
    analysis = json.loads(args.analysis.read_text())
    authority = json.loads(args.authority.read_text())
    assert len(analysis["witnesses"]) == len(authority["results"]) == 4
    assert analysis["generator_sha256"] == authority["generator_sha256"]
    # The canonical program is already whitespace-normalized. The public
    # receipt's rule_text_sha256 instead hashes the executable callable wrapper.
    assert analysis["rule_sha256"][:12] == authority["executed_rule_hash"]
    assert authority["rule_hash_matches_catalog"]
    comparisons = []
    for witness, result in zip(analysis["witnesses"], authority["results"]):
        assert witness["input"] == result["input"]
        assert result["valid_output"] and not result["error"]
        assert witness["python_bfs4_diagnostic_output"] == result["output"]
        comparisons.append({"name": witness["name"], "matches": True,
                            "input_sha256": result["input_sha256"],
                            "output_sha256": result["output_sha256"]})
    assert all(not p["bfs4_differences"] for p in analysis["canonical_profiles"])
    result = {
        "stage": "baseline independent semantic diagnostics",
        "generator_sha256": analysis["generator_sha256"],
        "canonical_program_sha256": analysis["rule_sha256"],
        "executed_callable_sha256": authority["rule_text_sha256"],
        "executed_rule_hash": authority["executed_rule_hash"],
        "canonical_pairs_matched": 3,
        "authority_inputs_matched": 4,
        "authority_receipt_sha256": hashlib.sha256(args.authority.read_bytes()).hexdigest(),
        "analysis_sha256": hashlib.sha256(args.analysis.read_bytes()).hexdigest(),
        "verification_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "comparisons": comparisons,
    }
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
