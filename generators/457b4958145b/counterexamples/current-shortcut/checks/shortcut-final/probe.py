"""Retain one fixed witness and one final production draw with public labels."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

WORK = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
GENERATOR = WORK / "repo/generators/457b4958145b/generator.py"
sys.path.insert(0, str(WORK / "repo/shared/runtime"))
spec = importlib.util.spec_from_file_location("shortcut_final_generator", GENERATOR)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
fixture = json.loads((GENERATOR.parent / "counterexamples/combined_contrast.json").read_text())
generated = generator.generate(384874255, 2, difficulty="easy")
inputs = [fixture["input"], generated]
(OUT / "input.json").write_text(json.dumps(inputs, indent=1) + "\n")
argv = [".venv-review/bin/python", "run_with_racket.py", "../.venv-review/bin/python", "-m", "arcpuzzles", "apply",
        "457b4958145b", "--input", "../checks/shortcut-final/input.json", "--out", "../checks/shortcut-final/racket.json"]
run = subprocess.run(argv, cwd=WORK, text=True, capture_output=True)
(OUT / "apply.stdout.log").write_text(run.stdout)
(OUT / "apply.stderr.log").write_text(run.stderr)
if run.returncode:
    raise SystemExit(run.returncode)
labels = json.loads((OUT / "racket.json").read_text())
cases = []
for index, grid in enumerate(inputs):
    label = labels["results"][index]
    rivals = {name: fn(grid) for name, fn in generator.CANONICAL_SHORTCUTS.items()}
    case = {"kind": "constructed_witness" if index == 0 else "final_production_draw",
            "generate_call": None if index == 0 else {"seed": 384874255, "sample_index": 2, "difficulty": "easy", "overrides": {}},
            "input": grid, "output": label["output"], "input_sha256": label["input_sha256"],
            "output_sha256": label["output_sha256"], "self_check": generator.self_check(grid),
            "valid_output": label["valid_output"], "error": label["error"], "rival_outputs": rivals,
            "refuted": {name: output != label["output"] for name, output in rivals.items()}}
    cases.append(case)
assert cases[0]["output"] == fixture["output"]
assert all(not case["self_check"] and case["valid_output"] and case["error"] is None
           and all(case["refuted"].values()) for case in cases)
receipt = {"generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
           "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "command": ["python3", "-B", "checks/shortcut-final/probe.py"], "cwd": str(WORK),
           "public_apply_command": argv, "public_apply_exit_code": run.returncode,
           "canonical_rule_sha256": fixture["provenance"]["canonical_program_solution_sha256"],
           "executed_rule_hash": labels["executed_rule_hash"], "cases": cases, "exit_code": 0}
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"receipt": str(OUT / "receipt.json"), "case_count": len(cases),
                  "rivals": list(generator.CANONICAL_SHORTCUTS), "all_refuted": True,
                  "constructed_centroid_output": cases[0]["rival_outputs"]["centroid"], "exit_code": 0}))
