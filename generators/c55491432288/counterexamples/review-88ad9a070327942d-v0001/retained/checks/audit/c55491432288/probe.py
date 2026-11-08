"""Bounded read-only generator audit; run through outer review.py run."""
from pathlib import Path
import hashlib
import importlib.util
import json

from arcpuzzles.catalog import Catalog

TASK = "c55491432288"
ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
source = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_c55491432288", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
record = Catalog(ROOT).get(TASK)
rule = record["variants"][0]["program_solution"]
identity = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
    "rule_hash": record["rule_hash"],
}
rows = []
for band in (None, "easy", "hard"):
    for sample_index in range(12):
        grid = module.generate(0, sample_index, difficulty=band)
        problems = module.self_check(grid, difficulty=band)
        rows.append({"seed": 0, "sample_index": sample_index, "difficulty": band,
                     "shape": [len(grid), len(grid[0])],
                     "pivot_count": sum(cell == 8 for row in grid for cell in row),
                     "problems": problems})
        assert not problems, (band, sample_index, problems)
overrides = {"grid_h": 9, "grid_w": 10}
grid = module.generate(0, 0, difficulty="easy", **overrides)
problems = module.self_check(grid, difficulty="easy")
shape = [len(grid), len(grid[0])]
assert not problems
assert shape != [9, 10], "Expected ignored-axis witness changed; reconsider finding"
(OUT / "input.json").write_text(json.dumps(grid) + "\n")
degenerate = module.generate(0, 0, texture="no_pivot")
(OUT / "no-pivot-input.json").write_text(json.dumps(degenerate) + "\n")
try:
    module.self_check(degenerate)
except Exception as exc:
    failure = {"exception": type(exc).__name__, "message": str(exc)}
else:
    raise AssertionError("Expected no-pivot validator exception changed")
assert failure["exception"] == "IndexError"
result = {**identity, "scope": {"seed": 0, "sample_indices": [0, 11],
                              "difficulty_bands": [None, "easy", "hard"],
                              "ordinary_generation_cases": len(rows)},
          "ordinary_checks": rows,
          "findings": [
              {"id": "A-c554-1", "kind": "reproduced override defect",
               "seed": 0, "sample_index": 0, "difficulty": "easy",
               "overrides": overrides, "expected_shape": [9, 10],
               "actual_shape": shape, "validator_problems": problems,
               "input_path": "checks/audit/c55491432288/input.json"},
              {"id": "A-c554-2", "kind": "reproduced validator crash",
               "seed": 0, "sample_index": 0, "overrides": {"texture": "no_pivot"},
               "input_path": "checks/audit/c55491432288/no-pivot-input.json",
               "exception": failure,
               "scope_note": "Declared degenerate texture, outside normal admitted domain; reject cleanly rather than crash."}
          ]}
(OUT / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({**identity, "ordinary_cases": len(rows), "findings": result["findings"]}))
