"""Verify retained Racket evidence and produce compact audit counterexamples."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
probe = json.loads((HERE / "probe.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
assert racket["generator_sha256"] == probe["generator_sha256"]
assert racket["executed_rule_hash"] == probe["rule_hash"]
assert all(result["valid_output"] and result["error"] is None for result in racket["results"])
assert racket["results"][0]["output"] == probe["cases"][0]["expected_canonical_output"]
assert racket["results"][1]["output"] != probe["cases"][1]["input"]
assert racket["results"][1]["output"][5][5] == 4
cases = []
for case, actual in zip(probe["cases"], racket["results"]):
    cases.append(dict(case, actual_racket_output=actual["output"],
                      input_sha256=actual["input_sha256"], output_sha256=actual["output_sha256"]))
report = {"task_id": probe["task_id"], "generator_sha256": probe["generator_sha256"],
          "rule_hash": probe["rule_hash"], "rule_text_sha256": racket["rule_text_sha256"],
          "cases": cases,
          "reference_command": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", probe["task_id"],
                                "--input", "../checks/audit/c1f63ca7d07b/input.json", "--out", "../checks/audit/c1f63ca7d07b/racket.json"],
          "cwd": "packet_root", "runtime_cwd": "WORK/repo", "exit_code": 0}
(HERE / "counterexamples.json").write_text(json.dumps(report, indent=2) + "\n")
receipts = {"verification_commands": [
    {"cwd": "packet_root", "argv": probe["command"], "exit_code": 0,
     "evidence_paths": ["WORK/checks/audit/c1f63ca7d07b/probe.json"]},
    {"cwd": "packet_root", "argv": report["reference_command"], "exit_code": 0,
     "evidence_paths": ["WORK/checks/audit/c1f63ca7d07b/racket.json"]},
    {"cwd": "packet_root", "argv": ["python3", "review.py", "run", "python3", "../checks/audit/c1f63ca7d07b/verify.py"],
     "exit_code": 0, "evidence_paths": ["WORK/checks/audit/c1f63ca7d07b/counterexamples.json"]}]}
(HERE / "receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
print("Verified canonical tie rejection and falsely equidistant fixture against retained Racket labels.")
