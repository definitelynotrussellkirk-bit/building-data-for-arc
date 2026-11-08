from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERATOR = HERE.parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("retained_e410357cf67e", GENERATOR)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
DATA = json.loads((HERE / "counterexamples.json").read_text())

assert DATA["generator_sha256"] == hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
assert DATA["rule_hash"] == GEN.RULE_HASH
for case in DATA["canonical_support"]:
    assert GEN.self_check(case["input"]) == []
    assert GEN.rule_mirror(case["input"]) == case["output"]

witness = DATA["active_wall_witness"]
grid = GEN.generate(
    witness["seed"],
    witness["sample_index"],
    difficulty=witness["difficulty"],
    **witness["overrides"],
)
assert grid == witness["input"]
assert GEN.rule_mirror(grid) == witness["canonical_output"]
assert GEN.SEMANTIC_RIVALS["ignore_walls"](grid) == witness["ignore_walls_output"]
assert witness["canonical_output"] != witness["ignore_walls_output"]
print(json.dumps({"passed": True, "task_id": GEN.TASK_ID, "witness": witness["id"]}))
