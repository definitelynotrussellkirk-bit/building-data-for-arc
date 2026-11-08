"""One bounded ordered-lesson audit of a missing tie-priority comparison."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator

TASK = "126da449328f"
PRIORITY = ("top", "left", "bottom", "right")
generator, source, source_sha = load_selected_generator(TASK)
root = find_root(source)
grids = [generator.generate(6, i) for i in range(2, 9)]


def independent_rival(grid):
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color:
                continue
            distances = {"top": r, "bottom": h - r - 1, "left": c, "right": w - c - 1}
            side = min(PRIORITY, key=lambda candidate: distances[candidate])
            if side == "top":
                cells = [(y, c) for y in range(r + 1)]
            elif side == "bottom":
                cells = [(y, c) for y in range(r, h)]
            elif side == "left":
                cells = [(r, x) for x in range(c + 1)]
            else:
                cells = [(r, x) for x in range(c, w)]
            for y, x in cells:
                out[y][x] = color
    return out


executed = Catalog(root).apply(TASK, grids)
rows = []
for index, grid, result in zip(range(2, 9), grids, executed["results"]):
    assert not result.get("error") and result.get("output") is not None, result
    assert generator.self_check(grid) == []
    rival = independent_rival(grid)
    rows.append({"sample_index": index, "input": grid, "output": result["output"],
                 "rival_output": rival, "rival_matches": rival == result["output"],
                 "observables": generator.semantic_observables(grid)})
assert len(rows) == 7
assert [row["rival_matches"] for row in rows] == [True] * 6 + [False]
hook = generator.lesson_identifiable(rows[:6], rows[6])
assert hook == [], hook
query = rows[-1]
differences = [[r, c] for r, row in enumerate(query["output"]) for c, color in enumerate(row)
               if color != query["rival_output"][r][c]]
report = {
    "task_id": TASK, "status": "concrete_ordered_lesson_ambiguity",
    "consumer": "ordered lesson construction and tie-priority semantic rivals",
    "source_path": str(source.relative_to(root)), "source_sha256": source_sha,
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "command": "PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python ../checks/126da449328f/probe.py",
    "command_returncode": 0, "seed": 6, "demonstration_indices": list(range(2, 8)), "query_index": 8,
    "rival_priority": list(PRIORITY), "canonical_priority": ["top", "bottom", "left", "right"],
    "rival_description": "Use the nearest border and otherwise preserve the canonical rule, but put left ahead of bottom in the equal-distance priority.",
    "observation": "All six required demonstration profiles occur and the current lesson hook accepts the lesson, yet the alternate total priority fits every demonstration and changes the query.",
    "lesson_identifiable_reasons": hook, "query_differing_cells": differences,
    "racket_run": True,
    "racket_scope": "All seven canonical labels freshly executed through public Catalog.apply; independent Python rival, not an executed Racket rival.",
    "executed_rule_hash": executed.get("executed_rule_hash"), "rule_text_sha256": executed.get("rule_text_sha256"),
    "recommendation": "Require a bottom-left tie witness within each six-demo window, completing top>bottom>left>right using the existing top-bottom and left-right witnesses; also check alternative total tie orders rather than only the six currently named rivals.",
    "existing_audit": "The current unresolved historical QA/order-policy audit was not edited or cleared. This is a fresh current-source ordered-window finding, not an arbitrary-query rotation claim.",
    "limits": ["One retained lawful ordered six-demonstration window and one alternate total priority; no full battery or broad correctness claim.", "The candidate search was capped at twenty seeds and exited at seed6; it used Python diagnostics before the retained seven-label Racket replay.", "No generator, authority, approval, or audit disposition was changed."],
    "pairs": rows,
}
path = Path(__file__).with_name("peer-review.json")
path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": report["status"], "source_sha256": source_sha,
                  "rule_hash": report["executed_rule_hash"], "hook_reasons": hook,
                  "query_differing_cells": differences, "racket_run": True}))
print(path)
