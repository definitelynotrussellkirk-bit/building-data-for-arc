from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import load_selected_generator

TASK = "4f09f8bfa35a"
root = Path.cwd()
gen, path, source_sha = load_selected_generator(TASK, root=root)

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

cases = [
    ("seed_true", True, 0),
    ("seed_false", False, 0),
    ("sample_index_true", 0, True),
    ("sample_index_false", 0, False),
    ("sample_index_negative", 0, -1),
]
results = {}
for name, seed, sample_index in cases:
    try:
        grid = gen.generate(seed, sample_index)
        results[name] = {
            "accepted": True,
            "seed_repr": repr(seed),
            "sample_index_repr": repr(sample_index),
            "height": len(grid),
            "width": len(grid[0]),
            "self_check": gen.self_check(grid),
            "grid_sha256": digest(grid),
        }
    except Exception as exc:
        results[name] = {
            "accepted": False,
            "seed_repr": repr(seed),
            "sample_index_repr": repr(sample_index),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
report = {
    "schema": "arcpuzzles-audit-scalar-probe-v1",
    "task_id": TASK,
    "generator_path": str(path.relative_to(root)),
    "generator_sha256": source_sha,
    "finding": (
        "generate accepts bool seeds, bool sample indices, and a negative sample index; "
        "each returned grid passes self_check"
    ),
    "results": results,
}
print(json.dumps(report, indent=2, sort_keys=True))
