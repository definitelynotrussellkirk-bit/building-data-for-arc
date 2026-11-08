"""Bind the focused audit's exact inputs, source, and public Racket receipt."""
import hashlib
import json
from pathlib import Path

from probe import OUT, ROOT, SOURCE, TASK, digest, panels


def main():
    probe = json.loads((OUT / "probe.json").read_text())
    inputs = json.loads((OUT / "input.json").read_text())["inputs"]
    receipt = json.loads((OUT / "racket.json").read_text())
    current_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert current_hash == probe["generator_sha256"] == receipt["generator_sha256"]
    assert receipt["task_id"] == TASK
    assert receipt["rule_hash_matches_catalog"] is True
    assert len(receipt["results"]) == len(inputs) == len(probe["cases"])
    comparisons = []
    for index, (case, grid, row) in enumerate(zip(probe["cases"], inputs, receipt["results"])):
        assert case["input_index"] == row["index"] == index
        assert row["input"] == grid
        assert case["input_sha256"] == row["input_sha256"] == digest(grid)
        assert row["error"] is None
        assert row["valid_output"] is True
        mask, a, b = panels(grid)
        comparisons.append({
            "name": case["name"], "input_index": index,
            "reference_matches_cellwise_selector": row["output"] == case["independent_cellwise_output"],
            "reference_equals_a": row["output"] == a,
            "reference_equals_b": row["output"] == b,
            "generator_domain": row["generator_domain"],
            "input_sha256": row["input_sha256"],
            "output_sha256": row["output_sha256"],
        })
    summary = {
        "task_id": TASK, "generator_sha256": current_hash,
        "catalog_rule_hash": receipt["catalog_rule_hash"],
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "rule_text_sha256": receipt["rule_text_sha256"],
        "reference_inputs": len(inputs),
        "unique_reference_inputs": len({digest(grid) for grid in inputs}),
        "cellwise_matches": sum(row["reference_matches_cellwise_selector"] for row in comparisons),
        "comparisons": comparisons,
        "density_pairs": probe["density_pairs"],
        "dimension_endpoint_probes": probe["dimension_endpoint_probes"],
        "input_file_sha256": hashlib.sha256((OUT / "input.json").read_bytes()).hexdigest(),
        "racket_receipt_sha256": hashlib.sha256((OUT / "racket.json").read_bytes()).hexdigest(),
        "scope": "Findings only. No target edit, battery, census, approval, or training admission.",
    }
    with (OUT / "summary.json").open("x") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    print(json.dumps(summary, indent=2))
    for name in ("workspace/probe_curriculum.py", "tests/test_curriculum_probe.py"):
        path = ROOT / "generators" / "832404dc8a5c" / name
        print(json.dumps({"static_review_file": str(path.relative_to(ROOT)),
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
