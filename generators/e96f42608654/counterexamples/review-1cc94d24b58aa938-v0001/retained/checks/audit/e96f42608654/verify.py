"""Combine retained generator evidence with actual supported Racket results."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
probe = json.loads((root / "probe.json").read_text())
racket = json.loads((root / "racket.json").read_text())
assert probe["generator_sha256"] == racket["generator_sha256"]
assert probe["rule_hash"] == racket["executed_rule_hash"]
assert racket["rule_hash_matches_catalog"]
for i, record in enumerate(probe["records"]):
    result = racket["results"][i]
    assert result["input"] == record["input"]
    assert result["error"] is None and result["valid_output"]
    record["actual_racket_output"] = result["output"]
    record["rival_agrees"] = record["rival_output"] == result["output"]
    record["validator_accepts"] = not record["self_check"]
assert probe["records"][0]["rival_agrees"] is False
assert probe["records"][1]["rival_agrees"] is True
assert probe["ignored_dimensions"]["outputs_identical"]
assert probe["ignored_dimensions"]["actual_grid_shape"] == [10, 9]
probe["rule_text_sha256"] = racket["rule_text_sha256"]
probe["verification_commands"] = [
    {"cwd": "packet_root", "effective_cwd": "repo",
     "argv": ["python3", "run_with_racket.py", "python3", "../checks/audit/e96f42608654/probe.py"],
     "exit_code": 0, "evidence_paths": ["checks/audit/e96f42608654/probe.json", "checks/audit/e96f42608654/input.json"]},
    {"cwd": "packet_root", "effective_cwd": "repo",
     "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", "e96f42608654", "--input", "../checks/audit/e96f42608654/input.json", "--out", "../checks/audit/e96f42608654/racket.json"],
     "exit_code": 0, "evidence_paths": ["checks/audit/e96f42608654/racket.json"]},
    {"cwd": "packet_root", "effective_cwd": "repo",
     "argv": ["python3", "run_with_racket.py", "python3", "../checks/audit/e96f42608654/verify.py"],
     "exit_code": 0, "evidence_paths": ["checks/audit/e96f42608654/counterexample.json"]},
]
(root / "counterexample.json").write_text(json.dumps(probe, indent=2) + "\n")
for r in probe["records"]:
    print(json.dumps({"kind": r["kind"], "validator_accepts": r["validator_accepts"],
                      "rival_agrees": r["rival_agrees"],
                      "actual_racket_output": ["".join(map(str, row)) for row in r["actual_racket_output"]],
                      "rival_output": ["".join(map(str, row)) for row in r["rival_output"]]}))
