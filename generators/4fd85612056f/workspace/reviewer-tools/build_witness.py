from __future__ import annotations
import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID = "4fd85612056f"
root = find_root(__file__)
gen, source, source_sha = load_selected_generator(TASK_ID, root=root)
request = {
    "seed": 1234,
    "sample_index": 2,
    "difficulty": "medium",
    "overrides": {"target_shape": "cross"},
}
grid = gen.generate(
    request["seed"],
    request["sample_index"],
    difficulty=request["difficulty"],
    **request["overrides"],
)
intended = gen._intended_output(grid)
rival = gen.CANONICAL_SHORTCUTS["same_color_components"](grid)
canonical = gen.CANONICAL_SHORTCUTS["same_color_components"]
record = {
    "schema": "arcpuzzles-shortcut-witness-v1",
    "task_id": TASK_ID,
    "generator_source": str(source.relative_to(root)),
    "generator_sha256": source_sha,
    "rule_hash": gen.RULE_HASH,
    "request": request,
    "input": grid,
    "self_check": gen.self_check(grid),
    "observed_overrides": gen.observe_overrides(grid),
    "intended_python_mirror": intended,
    "same_color_components_rival": rival,
    "outputs_disagree": intended != rival,
    "mixed_color_winner": gen.SEMANTIC_WITNESSES["mixed_color_winner"](grid),
    "input_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
}
out = Path(__file__).resolve().parent
(out / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(out / "analysis.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: record[k] for k in ("generator_sha256", "self_check", "outputs_disagree", "mixed_color_winner")}, sort_keys=True))
