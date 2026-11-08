from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "repo/generators/generic_waypoint_route_gen1/generator.py"
SPEC = importlib.util.spec_from_file_location("audit_waypoint_route", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


task = GEN.generate_task(23, difficulty="medium")
tampered = deepcopy(task)
pairs = tampered["train"] + tampered["test"]
records = []
for index, pair in enumerate(pairs):
    grid = pair["input"]
    h, w = len(grid), len(grid[0])
    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    separator_columns = [
        c
        for c in range(w)
        if grid[0][c] != bg and all(grid[r][c] == grid[0][c] for r in range(h))
    ]
    start = max(separator_columns) + 1
    original = deepcopy(grid)
    for r in range(h):
        for c in range(start):
            if c not in separator_columns:
                grid[r][c] = bg
    original_output = GEN._apply(original)
    tampered_output = GEN._apply(grid)
    records.append(
        {
            "pair_index": index,
            "shape": [h, w],
            "background": bg,
            "separator_columns": separator_columns,
            "last_panel_start": start,
            "earlier_nonbackground_before": sum(
                original[r][c] != bg
                for r in range(h)
                for c in range(start)
                if c not in separator_columns
            ),
            "earlier_nonbackground_after": sum(
                grid[r][c] != bg
                for r in range(h)
                for c in range(start)
                if c not in separator_columns
            ),
            "original_input_sha256": sha(original),
            "tampered_input_sha256": sha(grid),
            "output_unchanged": original_output == tampered_output == pair["output"],
        }
    )

report = {
    "task_id": GEN.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": 23,
    "difficulty": "medium",
    "shortcut": "ignore every panel before the last full-height separator",
    "records": records,
    "tampered_self_check_task": GEN.self_check_task(tampered),
    "all_outputs_unchanged": all(record["output_unchanged"] for record in records),
    "tampered_task": tampered,
}
OUT = Path(__file__).with_name("dead-context-report.json")
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: report[key] for key in ("task_id", "generator_sha256", "shortcut", "records", "tampered_self_check_task", "all_outputs_unchanged")}, indent=2))
