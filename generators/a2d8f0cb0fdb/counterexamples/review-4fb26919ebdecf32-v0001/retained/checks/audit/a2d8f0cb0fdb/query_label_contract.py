from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators" / "a2d8f0cb0fdb" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_a2d8f0cb0fdb", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

demos = []
for index in range(mod.EXAMPLES_NEEDED):
    grid = mod.generate(1234, index, difficulty="medium")
    demos.append({"input": grid, "output": mod.rule_mirror(grid)})
query_grid = mod.generate(1234, mod.EXAMPLES_NEEDED, difficulty="medium")
correct = mod.rule_mirror(query_grid)
wrong = [row[:] for row in correct]
wrong[1][0] = 9 if wrong[1][0] != 9 else 8
result = mod.lesson_identifiable(demos, {"input": query_grid, "output": wrong})
record = {
    "task_id": mod.TASK_ID,
    "generator_version": mod.VERSION,
    "seed": 1234,
    "query_sample_index": mod.EXAMPLES_NEEDED,
    "correct_query_output": correct,
    "wrong_query_output": wrong,
    "lesson_identifiable_result": result,
    "defect": "lesson_identifiable does not compare query['output'] with rule_mirror(query['input'])",
}
out = Path(__file__).with_name("wrong_query_accepted.json")
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"result": result, "wrong_differs": wrong != correct}, indent=2))
print(out)
if result != [] or wrong == correct:
    raise SystemExit("reproduction did not trigger")
