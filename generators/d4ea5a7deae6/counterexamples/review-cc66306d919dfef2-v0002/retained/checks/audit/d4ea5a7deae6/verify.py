"""Verify the saved public authority output against the declared A2 rival."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
actual = json.loads((HERE / "racket.json").read_text())
inp = json.loads((HERE / "input.json").read_text())["inputs"][0]
rival = json.loads((HERE / "rival.json").read_text())["outputs"][0]
mirror = json.loads((HERE / "mirror.json").read_text())["outputs"][0]
binding = json.loads((HERE / "binding.json").read_text())
out = actual["results"][0]["output"]
assert actual["results"][0]["error"] is None
assert actual["results"][0]["valid_output"]
assert actual["results"][0]["input"] == inp
assert actual["executed_rule_hash"] == binding["canonical_rule_hash"]
assert actual["generator_sha256"] == binding["generator_sha256"]
source = HERE.parents[2] / "repo/generators/d4ea5a7deae6/generator.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == binding["generator_sha256"]
assert out == mirror
diffs = [{"row": r, "col": c, "actual_racket": out[r][c], "rival": rival[r][c]}
         for r in range(len(out)) for c in range(len(out[0]))
         if out[r][c] != rival[r][c]]
assert diffs == [{"row": 4, "col": 9, "actual_racket": 0, "rival": 5},
                 {"row": 4, "col": 10, "actual_racket": 0, "rival": 5}]
binding["executed_rule_text_sha256"] = actual["rule_text_sha256"]
binding["canonical_rule_text_sha256_note"] = "Raw authoring program text SHA; public execution uses its normalized runtime text, recorded separately. Both resolve to rule hash efb277668cb4."
(HERE / "binding.json").write_text(json.dumps(binding, indent=2) + "\n")
comparison = {
    "finding_id": "A2", "checked": True,
    "racket_output_matches_python_mirror": True,
    "rival_differs_from_actual_racket": True,
    "mismatch_count": len(diffs), "differences_zero_based": diffs,
    "generator_sha256": binding["generator_sha256"],
    "executed_rule_hash": actual["executed_rule_hash"],
    "executed_rule_text_sha256": actual["rule_text_sha256"],
    "input_sha256_from_public_apply": actual["results"][0]["input_sha256"],
    "actual_output_sha256_from_public_apply": actual["results"][0]["output_sha256"],
    "self_check": binding["self_check"],
    "documented_domain": binding["documented_domain"],
    "generated_domain": binding["generated_domain"],
}
(HERE / "comparison.json").write_text(json.dumps(comparison, indent=2) + "\n")
print(json.dumps(comparison))
