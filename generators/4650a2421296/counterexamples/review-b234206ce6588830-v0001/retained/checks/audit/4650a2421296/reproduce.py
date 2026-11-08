#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, load_selected_generator

TASK = "4650a2421296"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest_json(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def chamber_census(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    chambers = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] == 5 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (1 <= nr < height - 1 and 1 <= nc < width - 1):
                        continue
                    if grid[nr][nc] == 5 or (nr, nc) in seen:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            chambers.append({
                "size": len(cells),
                "red_seeds": sum(grid[r][c] == 2 for r, c in cells),
                "bounds": {
                    "row_min": min(r for r, _ in cells),
                    "row_max": max(r for r, _ in cells),
                    "col_min": min(c for _, c in cells),
                    "col_max": max(c for _, c in cells),
                },
            })
    return sorted(chambers, key=lambda row: (row["bounds"]["row_min"], row["bounds"]["col_min"]))


generator, source, source_hash = load_selected_generator(TASK, root=ROOT)
kwargs = {"difficulty": "easy", "n_chambers": 9}
grid = generator.generate(0, 0, **kwargs)
without_override = generator.generate(0, 0, difficulty="easy")
chambers = chamber_census(grid)
row = Catalog(ROOT).describe(TASK)
report = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": TASK,
    "classification": "advertised exact override is accepted but ignored",
    "source": {
        "path": source.relative_to(ROOT).as_posix(),
        "sha256": source_hash,
        "version": generator.VERSION,
        "catalog_rule_hash": row["rule_hash"],
    },
    "call": {"seed": 0, "sample_index": 0, **kwargs},
    "advertised_axis": generator.AXES["n_chambers"],
    "requested_n_chambers": 9,
    "realized_n_chambers": len(chambers),
    "chambers": chambers,
    "self_check": generator.self_check(grid),
    "same_as_call_without_n_chambers": grid == without_override,
    "input_sha256": digest_json(grid),
    "input": grid,
    "scope": "findings-only audit; target source was not edited",
}
HERE.joinpath("input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
HERE.joinpath("reproducer.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "requested": 9,
    "realized": len(chambers),
    "self_check": report["self_check"],
    "same_without_override": report["same_as_call_without_n_chambers"],
    "source_sha256": source_hash,
}))
