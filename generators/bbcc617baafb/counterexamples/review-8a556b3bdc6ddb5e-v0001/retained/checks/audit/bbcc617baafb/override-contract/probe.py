from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json

from reviewer_support import load_selected_generator


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def mode_output(grid):
    output = []
    for r0 in range(0, len(grid), 3):
        row = []
        for c0 in range(0, len(grid[0]), 3):
            counts = Counter(
                grid[r][c]
                for r in range(r0, r0 + 3)
                for c in range(c0, c0 + 3)
            )
            top = max(counts.values())
            modes = [value for value, count in counts.items() if count == top]
            row.append(modes[0] if len(modes) == 1 else None)
        output.append(row)
    return output


root = Path(__file__).resolve().parents[4] / "repo"
generator, source, source_sha = load_selected_generator("bbcc617baafb", root=root)
base = generator.generate(17, 0, difficulty="easy")
cases = [
    {"block_h": 6},
    {"block_w": 6},
    {"palette_size": 1},
    {"unknown_axis": 123},
]
rows = []
for overrides in cases:
    try:
        grid = generator.generate(17, 0, difficulty="easy", **overrides)
        rows.append(
            {
                "overrides": overrides,
                "status": "accepted",
                "same_as_default": grid == base,
                "shape": [len(grid), len(grid[0])],
                "grid_sha256": grid_sha(grid),
                "mode_output": mode_output(grid),
                "self_check": generator.self_check(grid, difficulty="easy"),
            }
        )
    except Exception as exc:
        rows.append(
            {
                "overrides": overrides,
                "status": "rejected",
                "exception": type(exc).__name__,
                "message": str(exc),
            }
        )
report = {
    "schema": "arcpuzzles-audit-override-probe-v1",
    "task_id": "bbcc617baafb",
    "generator_path": str(source.relative_to(root)),
    "generator_sha256": source_sha,
    "seed": 17,
    "sample_index": 0,
    "difficulty": "easy",
    "default": {
        "shape": [len(base), len(base[0])],
        "grid_sha256": grid_sha(base),
        "mode_output": mode_output(base),
        "self_check": generator.self_check(base, difficulty="easy"),
    },
    "cases": rows,
    "conclusion": (
        "Advertised block_h, block_w, and palette_size overrides are accepted "
        "but produce the exact default grid; an unknown key is also silently accepted."
    ),
}
print(json.dumps(report, indent=2))
