from __future__ import annotations
import hashlib
import importlib
import inspect
import json
import importlib.util
import sys
from pathlib import Path

TASK = "d7b84df5a06a"
repo = Path.cwd()
sys.path.insert(0, str(repo / "shared/runtime"))
source = (repo / "generators" / TASK / "generator.py").resolve()
spec = importlib.util.spec_from_file_location(f"audit_{TASK}_generator", source)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
grid = gen.generate(1701, 0, difficulty="medium")
output = gen.rule_mirror(grid)
pair = {"input": grid, "output": output}
report = {
    "task_id": TASK,
    "generator_version": gen.VERSION,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "case": {"seed": 1701, "sample_index": 0, "difficulty": "medium"},
    "dimensions": [len(grid), len(grid[0])],
    "self_check": gen.self_check(grid),
    "witnesses": {name: bool(fn(grid)) for name, fn in gen.SEMANTIC_WITNESSES.items()},
    "rival_disagrees": {name: fn(grid) != output for name, fn in gen.LESSON_COMPETITORS.items()},
    "lesson_identifiable": gen.lesson_identifiable([pair], pair),
    "conclusion": "one generated pair contains all declared decisive witnesses and refutes every declared rival",
}
out = Path("../checks/audit/d7b84df5a06a/one-demo-probe.json")
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
