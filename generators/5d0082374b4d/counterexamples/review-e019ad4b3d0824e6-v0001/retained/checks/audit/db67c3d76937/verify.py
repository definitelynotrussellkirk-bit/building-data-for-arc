"""Compare retained audit cases/rivals with the supported Racket receipt."""
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
prepared = json.loads((HERE / "probe-inputs.json").read_text())
receipt = json.loads((HERE / "racket.json").read_text())
_, _, source_sha = load_selected_generator(prepared["task_id"], root=find_root(__file__))
assert source_sha == prepared["source_sha256"] == receipt["generator_sha256"]
assert receipt["rule_hash_matches_catalog"] is True
assert len(prepared["cases"]) == len(receipt["results"]) == 41

rows = []
for case, actual in zip(prepared["cases"], receipt["results"]):
    assert case["apply_index"] == actual["index"]
    assert case["input"] == actual["input"]
    assert actual["error"] is None and actual["valid_output"] is True
    assert case["self_check"] == actual["generator_domain"]["errors"]
    if case["kind"] == "canonical":
        assert case["output"] == actual["output"]
    rows.append({
        "apply_index": case["apply_index"],
        "kind": case["kind"],
        **{k: case[k] for k in ("difficulty", "seed", "sample_index", "variant", "split", "pair_index") if k in case},
        "nonzero_color_count": case["nonzero_color_count"],
        "generator_domain": actual["generator_domain"],
        "rival_matches": {name: grid == actual["output"] for name, grid in case["rival_outputs"].items()},
        "input_sha256": actual["input_sha256"],
    })

generated = [row for row in rows if row["kind"] == "generated"]
canonical = [row for row in rows if row["kind"] == "canonical"]
rivals = list(prepared["cases"][0]["rival_outputs"])
summary = {
    "task_id": prepared["task_id"],
    "status": "distribution_defect_reproduced",
    "source_sha256": source_sha,
    "executed_rule_hash": receipt["executed_rule_hash"],
    "rule_text_sha256": receipt["rule_text_sha256"],
    "canonical_program_sha256": prepared["canonical_program_sha256"],
    "probe_sha256": hashlib.sha256((HERE / "probe.py").read_bytes()).hexdigest(),
    "verification_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "sampling": prepared["sampling"],
    "generated": {
        "draws": len(generated),
        "unique_inputs": len({row["input_sha256"] for row in generated}),
        "domain_valid": sum(row["generator_domain"]["status"] == "valid" for row in generated),
        "exactly_two_nonzero_colors": sum(row["nonzero_color_count"] == 2 for row in generated),
        "per_band": {
            band: {
                "draws": sum(row["difficulty"] == band for row in generated),
                "rival_matches": {name: sum(row["difficulty"] == band and row["rival_matches"][name] for row in generated) for name in rivals},
            } for band in ("easy", "medium", "hard")
        },
        "rival_matches": {name: sum(row["rival_matches"][name] for row in generated) for name in rivals},
    },
    "canonical": {
        "pairs": len(canonical),
        "authority_matches_stored_labels": len(canonical),
        "domain_rejected": sum(row["generator_domain"]["status"] == "invalid" for row in canonical),
        "three_nonzero_colors": sum(row["nonzero_color_count"] == 3 for row in canonical),
        "rival_matches": {name: sum(row["rival_matches"][name] for row in canonical) for name in rivals},
    },
    "cases": rows,
    "limits": [
        "This is a distribution/teaching-support finding, not a within-generated-domain query ambiguity witness.",
        "The canonical counterexample is outside the current generator validator domain; that rejection is the defect.",
        "Only 36 finite production draws (28 unique inputs), all five canonical pairs, and the two named rivals were measured.",
        "The stronger all-ordinary-draws statement follows from the inspected fixed-two-pair construction, not the finite sample alone.",
        "No full battery, lesson census, or target mutation was performed.",
    ],
}
assert summary["generated"]["domain_valid"] == 36
assert summary["generated"]["exactly_two_nonzero_colors"] == 36
assert all(count == 36 for count in summary["generated"]["rival_matches"].values())
assert summary["canonical"]["domain_rejected"] == 4
assert all(count == 1 for count in summary["canonical"]["rival_matches"].values())

# A different canonical example from the prior audit: two horizontal spans plus
# a vertical span. The lower horizontal span is invisible to both shortcuts.
case = next(case for case in prepared["cases"] if case["kind"] == "canonical" and case["split"] == "train" and case["pair_index"] == 2)
actual = receipt["results"][case["apply_index"]]
witness = {
    "task_id": prepared["task_id"],
    "finding_id": "A-db67-1",
    "source_sha256": source_sha,
    "executed_rule_hash": receipt["executed_rule_hash"],
    "rule_text_sha256": receipt["rule_text_sha256"],
    "origin": {"kind": "canonical", "variant": case["variant"], "split": case["split"], "pair_index": case["pair_index"]},
    "input_shape": [len(case["input"]), len(case["input"][0])],
    "input": case["input"],
    "racket_output": actual["output"],
    "canonical_output_matches_racket": actual["output"] == case["output"],
    "generator_domain": actual["generator_domain"],
    "rival_outputs": case["rival_outputs"],
    "differences": {
        name: [
            {"row": r, "column": c, "racket": actual["output"][r][c], "rival": value}
            for r, row in enumerate(grid) for c, value in enumerate(row)
            if value != actual["output"][r][c]
        ] for name, grid in case["rival_outputs"].items()
    },
    "receipt_path": "checks/audit/db67c3d76937/racket.json",
    "receipt_index": case["apply_index"],
    "authority_command": receipt["command"],
    "authority_cwd": receipt["cwd"],
    "authority_exit_code": 0,
    "lawfulness": "Canonical and Racket-labeled; rejected by the current two-color generator domain.",
}
(HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(HERE / "reproduction.json").write_text(json.dumps(witness, indent=2) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "cases"}, indent=2))
