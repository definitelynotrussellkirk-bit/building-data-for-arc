"""Replay one retained query-rotation weakness through protected Racket."""
from pathlib import Path
import hashlib
import json
import sys

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import validate_grid
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, load_selected_generator


HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK = "8604dc774d22"
EXPECTED = "a3fcdf7e17ce18931c5f89f8f044ac5a7e5c276d1106e3aa764255a56a8c84d6"
module, source_path, source_sha = load_selected_generator(TASK, root=ROOT)
assert source_sha == EXPECTED
catalog = Catalog(ROOT)
row = catalog.describe(TASK)
programs = {item["program_solution"] for item in catalog._variants()[row.get("rule_task_id", TASK)]}
assert len(programs) == 1
canonical = programs.pop()
filtered = "(filter (lambda (o) (= (obj-color o) 3)) (objects g 0))"
assert canonical.count(filtered) == 1
rival = canonical.replace(filtered, "(objects g 0)")
wrapped = {name: wrap_rule(program) for name, program in
           (("canonical", canonical), ("color_blind_l", rival))}

bridge = RacketBridge(max_calls_before_restart=32)
try:
    identity = bridge.runtime_identity
    assert identity["backend"] == "racket" and identity["protected"] is True

    def execute(name, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, line)) + ")" for line in grid) + ")"
        return validate_grid(bridge.eval_text(f"({wrapped[name]} {literal})"))

    pairs = []
    for index in range(5):
        grid = module.generate(31, index, difficulty="easy")
        assert module.self_check(grid) == []
        output = execute("canonical", grid)
        alternate = execute("color_blind_l", grid)
        assert output == module.rule_mirror(grid)
        assert alternate == module.SEMANTIC_RIVALS["color_blind_l"](grid)
        pairs.append({"sample_index": index, "input": grid, "output": output,
                      "rival_output": alternate})
finally:
    bridge.close()

demo_indices, query_index = [0, 2, 3, 4], 1
demos = [{"input": pairs[index]["input"], "output": pairs[index]["output"]}
         for index in demo_indices]
query = {"input": pairs[query_index]["input"]}
assert all(pairs[index]["output"] == pairs[index]["rival_output"] for index in demo_indices)
target = pairs[query_index]
differences = [
    {"row": r, "col": c, "canonical": target["output"][r][c], "rival": target["rival_output"][r][c]}
    for r in range(len(target["input"])) for c in range(len(target["input"][0]))
    if target["output"][r][c] != target["rival_output"][r][c]
]
assert len(differences) == 3
assert all(cell["canonical"] == 5 and cell["rival"] == 4 for cell in differences)
rotated_hook = module.lesson_identifiable(demos, query)
assert any("color-blind" in reason for reason in rotated_hook)
ordered_hook = module.lesson_identifiable(
    [{"input": pair["input"], "output": pair["output"]} for pair in pairs[:4]],
    {"input": pairs[4]["input"]},
)
assert ordered_hook == []

binding = {
    "task_id": TASK,
    "generator_path": source_path.relative_to(ROOT).as_posix(),
    "generator_sha256": source_sha,
    "generator_version": module.VERSION,
    "rule_hash": row["rule_hash"],
    "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
result = {
    "status": "confirmed_existing_teaching_ambiguity",
    "source_binding": binding,
    "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv], "exit_code": 0},
    "settings": {"seed": 31, "difficulty": "easy", "sample_indices": list(range(5)), "overrides": {}},
    "racket": identity,
    "racket_evaluations": 10,
    "programs": {"canonical": canonical, "color_blind_l": rival},
    "pairs": pairs,
    "lesson": {"demonstration_indices": demo_indices, "query_index": query_index,
               "rival_fits_all_demos": True, "different_query_cells": differences,
               "rotated_hook_reasons": rotated_hook, "ordered_hook_reasons": ordered_hook},
    "generator_changed": False,
    "limits": "One existing easy-band seed/window and one plausible rival; no claim about other seeds, bands, rivals, or universal identifiability.",
}
(HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
summary = {
    "status": result["status"], "source_binding": binding,
    "input_count": 5, "racket_evaluations": 10,
    "rival": "color_blind_l", "demonstration_indices": demo_indices,
    "query_index": query_index, "different_query_cell_count": len(differences),
    "ordered_hook_passed": True, "rotated_hook_rejected": True,
    "generator_changed": False, "result_path": "checks/8604dc774d22/result.json",
    "suggested_disposition": "Keep the existing unresolved rotation finding; duplicate indispensable witnesses if arbitrary holdout is required, or explicitly retain fixed query ordering.",
    "limits": result["limits"],
}
(HERE / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
print(json.dumps(summary, sort_keys=True))
