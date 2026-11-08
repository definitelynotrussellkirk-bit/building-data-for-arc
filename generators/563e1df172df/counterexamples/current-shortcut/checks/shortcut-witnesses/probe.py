"""Retain generated witnesses for the generator's actual canonical shortcuts."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator


root = find_root(Path.cwd())
gen, source, source_hash = load_selected_generator("563e1df172df", root=root)
pairs = canonical_pairs(gen.TASK_ID, root=root, labeled_only=True)
out = Path(__file__).resolve().parent
cases = []
fit = {}
for name, rival in gen.CANONICAL_SHORTCUTS.items():
    fit[name] = {"matched": sum(rival(p["input"]) == p["output"] for p in pairs),
                 "total": len(pairs)}
    assert fit[name]["matched"] == len(pairs), name
    for index in range(gen.LESSON_SCHEDULE_PERIOD):
        grid = gen.generate(1729, index, difficulty="easy")
        predicted = rival(grid)
        if predicted != gen.rule_mirror(grid):
            assert gen.self_check(grid) == []
            cases.append({"rival": name, "seed": 1729, "sample_index": index,
                          "difficulty": "easy", "overrides": {}, "input": grid,
                          "rival_output": predicted, "self_check_errors": [],
                          "observed_profile": gen.observe_overrides(grid)})
            break
    else:
        raise AssertionError("No generated counterexample: " + name)

input_path = out / "input.json"
input_path.write_text(json.dumps([case["input"] for case in cases]) + "\n")
receipt_path = out / "racket.json"
if receipt_path.exists():
    raise FileExistsError("Retained apply receipt already exists")
command = [sys.executable, "-m", "arcpuzzles", "apply", gen.TASK_ID,
           "--input", str(input_path), "--out", str(receipt_path)]
result = subprocess.run(command, cwd=root, text=True, capture_output=True)
(out / "apply.log").write_text(result.stdout + result.stderr)
assert result.returncode == 0, result.stderr
receipt = json.loads(receipt_path.read_text())
assert receipt["generator_sha256"] == source_hash
for case, row in zip(cases, receipt["results"], strict=True):
    assert row["valid_output"] and not row["error"]
    assert row["output"] == gen.rule_mirror(case["input"])
    assert row["output"] != case["rival_output"]
    case.update({"racket_output": row["output"], "input_sha256": row["input_sha256"],
                 "output_sha256": row["output_sha256"]})
report = {"task_id": gen.TASK_ID, "generator_sha256": source_hash,
          "rule_hash": receipt["executed_rule_hash"],
          "canonical_fit": fit, "cases": cases,
          "command": {"argv": command, "cwd": str(root), "exit_code": result.returncode},
          "scope": "One generated Racket-labelled witness for each actual declared canonical shortcut.",
          "source_path": str(source),
          "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"generator_sha256": source_hash, "canonical_fit": fit,
                  "generated_racket_witnesses": len(cases)}))
