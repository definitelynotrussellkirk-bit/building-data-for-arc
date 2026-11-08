from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK = "1b6b40a92e4f"
root = Path.cwd()
gen, source_path, source_sha = load_selected_generator(TASK, root=root)
grid = [[0 for _ in range(10)] for _ in range(9)]
# Two disconnected color-2 components, one color-3 component, and an illegal
# input color 9. This violates the generator's own palette/connectivity domain.
grid[1][1] = 2
grid[3][3] = 2
grid[6][6] = 3
grid[6][7] = 3
grid[0][9] = 9
result = {
    "schema": "audit-counterexample-v1",
    "task_id": TASK,
    "generator_source": str(source_path.relative_to(root)),
    "generator_sha256": source_sha,
    "input": grid,
    "self_check": gen.self_check(grid),
    "violations": [
        "color 2 has two disconnected components",
        "input contains undeclared color 9",
        "normalized shape overlap/unique-cell preconditions are not checked",
    ],
    "finding": "self_check returns no errors for a grid outside all declared ordinary invariants",
}
out = Path(__file__).with_name("selfcheck-counterexample.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
