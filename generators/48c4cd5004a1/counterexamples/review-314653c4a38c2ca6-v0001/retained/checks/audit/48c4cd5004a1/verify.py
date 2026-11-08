#!/usr/bin/env python3
"""Compare the bounded audit hypotheses with the public Racket receipt."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
probe = json.loads((OUT / "probe.json").read_text())
receipt = json.loads((OUT / "racket.json").read_text())
identities = json.loads((OUT / "apply-identities.json").read_text())
inputs = json.loads((OUT / "apply-inputs.json").read_text())
assert receipt["generator_sha256"] == probe["source_sha256"]
assert receipt["executed_rule_hash"] == probe["rule_hash"]
assert receipt["rule_hash_matches_catalog"] is True
assert len(receipt["results"]) == len(inputs) == len(identities) == 54
generated, canonical, counterfactuals = [], [], []
for index, (actual, identity, grid) in enumerate(zip(receipt["results"], identities, inputs, strict=True)):
    assert actual["index"] == index and actual["input"] == grid
    assert actual["error"] is None and actual["valid_output"] is True
    if identity["kind"] == "generated":
        expected = probe["generated"][len(generated)]
        assert actual["output"] == expected["facts"]["output"]
        generated.append({"index": index, **identity, "first_touched_fits_racket": actual["output"] == expected["facts"]["first_touched_output"],
                          "input_sha256": actual["input_sha256"]})
    elif identity["kind"] == "canonical":
        expected = probe["canonical"][len(canonical)]
        assert actual["output"] == expected["expected_output"] == expected["facts"]["output"]
        canonical.append({"index": index, **identity, "count_checker_cells_fits_racket": actual["output"] == expected["count_checker_cells_rival"]})
    else:
        expected = probe["witnesses"][len(counterfactuals)]
        assert actual["output"] == expected["facts"]["output"]
        rival = expected.get("count_checker_cells_rival", expected["facts"]["first_touched_output"])
        assert actual["output"] != rival
        counterfactuals.append({"index": index, **identity, "self_check": expected["self_check"],
                               "base": expected["base"], "edit": expected["edit"],
                               "input": grid, "input_sha256": actual["input_sha256"],
                               "racket_output": actual["output"], "rival_output": rival,
                               "racket_output_sha256": actual["output_sha256"]})
report = {
    "task_id": probe["task_id"], "source_sha256": receipt["generator_sha256"],
    "executed_rule_hash": receipt["executed_rule_hash"], "executed_rule_text_sha256": receipt["rule_text_sha256"],
    "canonical_program_sha256": probe["rule_sha256"],
    "probe_source_sha256": hashlib.sha256((OUT / "probe.py").read_bytes()).hexdigest(),
    "passed": True, "reference_executions": len(receipt["results"]),
    "generated_count": len(generated), "first_touched_fits_generated_racket": sum(row["first_touched_fits_racket"] for row in generated),
    "canonical_count": len(canonical), "count_checker_cells_fits_canonical_racket": sum(row["count_checker_cells_fits_racket"] for row in canonical),
    "counterfactuals": counterfactuals, "generated": generated, "canonical": canonical,
    "limitations": ["48 deterministic generated inputs; not a complete seed census", "auditor-authored finite rivals; target declares no CANONICAL_SHORTCUTS", "checkerboard counterfactual is canonical-family/validator evidence, not generated support", "no target source or rule was edited"],
}
(OUT / "verification.json").write_text(json.dumps(report, separators=(",", ":")) + "\n")
print(json.dumps({key: report[key] for key in ("task_id", "source_sha256", "passed", "reference_executions", "generated_count", "first_touched_fits_generated_racket", "canonical_count", "count_checker_cells_fits_canonical_racket")}, sort_keys=True))
