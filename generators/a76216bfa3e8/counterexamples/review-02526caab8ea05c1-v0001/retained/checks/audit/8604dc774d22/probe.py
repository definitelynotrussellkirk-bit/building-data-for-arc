"""Generate fresh source-bound audit inputs; public apply supplies their labels."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
TASK = "8604dc774d22"
SOURCE = REPO / "generators" / TASK / "generator.py"
SHA = "a3fcdf7e17ce18931c5f89f8f044ac5a7e5c276d1106e3aa764255a56a8c84d6"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_8604", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
cases = []
for band in ("easy", "medium", "hard"):
    for index in range(5):
        grid = mod.generate(31, index, difficulty=band)
        cases.append({"kind": "default", "seed": 31, "sample_index": index,
                      "difficulty": band, "overrides": {}, "input": grid,
                      "self_check_result": mod.self_check(grid),
                      "observed_axes": mod.observe_overrides(grid),
                      "python_mirror_output": mod.rule_mirror(grid),
                      "rival_outputs": {name: fn(grid) for name, fn in mod.SEMANTIC_RIVALS.items()}})
canonical = REPO / "shared/data/canonical/puzzles.jsonl"
rows = [json.loads(line) for line in canonical.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK]
assert len(rows) == 1
row = rows[0]
tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
for index, pair in enumerate(row["train"] + tests):
    cases.append({"kind": "canonical", "canonical_pair_index": index,
                  "input": pair["input"], "canonical_stored_output": pair["output"],
                  "self_check_result": mod.self_check(pair["input"]),
                  "python_mirror_output": mod.rule_mirror(pair["input"]),
                  "rival_outputs": {name: fn(pair["input"]) for name, fn in mod.SEMANTIC_RIVALS.items()}})
data = {"task_id": TASK, "generator_sha256": SHA, "rule_hash": mod.RULE_HASH,
        "canonical_rule_exact_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
        "cases": cases}
(HERE / "inputs.json").write_text(json.dumps({"inputs": [case["input"] for case in cases]}) + "\n")
(HERE / "probe.json").write_text(json.dumps(data, indent=2) + "\n")
print(json.dumps({"task_id": TASK, "cases": len(cases),
                  "self_check_failures": sum(bool(case["self_check_result"]) for case in cases),
                  "generator_sha256": SHA}))
