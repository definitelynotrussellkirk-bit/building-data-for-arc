from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def first_selected_crop(grid: list[list[int]]) -> list[list[int]]:
    sel = grid[0][0]
    h, w = len(grid), len(grid[0])
    start = next(
        (r, c)
        for r in range(1, h)
        for c in range(w)
        if grid[r][c] == sel
    )
    seen = {start}
    queue = deque([start])
    cells = []
    while queue:
        r, c = queue.popleft()
        cells.append((r, c))
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if nr < 1 or nr >= h or nc < 0 or nc >= w:
                continue
            if (nr, nc) in seen or grid[nr][nc] != sel:
                continue
            seen.add((nr, nc))
            queue.append((nr, nc))
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    occupied = set(cells)
    return [
        [sel if (r, c) in occupied else 0 for c in range(left, right + 1)]
        for r in range(top, bottom + 1)
    ]


def digest(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


easy = json.loads((ROOT / "easy_identity_racket.json").read_text())
hard = json.loads((ROOT / "nonidentity_racket.json").read_text())
rows = []
for source, label in ((easy, "easy_identity"), (hard, "hard_key_2")):
    for result in source["results"]:
        rival = first_selected_crop(result["input"])
        rows.append({
            "cohort": label,
            "index": result["index"],
            "key": result["input"][0][-1],
            "input_sha256": result["input_sha256"],
            "racket_output_sha256": result["output_sha256"],
            "rival_output_sha256": digest(rival),
            "rival_matches_racket": rival == result["output"],
            "rival_output": rival,
            "racket_output": result["output"],
        })

report = {
    "schema": "audit-semantic-shortcut-v1",
    "task_id": easy["task_id"],
    "generator_sha256": easy["generator_sha256"],
    "rule_text_sha256": easy["rule_text_sha256"],
    "executed_rule_hash": easy["executed_rule_hash"],
    "rival": "ignore transform key and crop the first selector-colored body blob unchanged",
    "easy_identity_matches": sum(r["rival_matches_racket"] for r in rows if r["cohort"] == "easy_identity"),
    "easy_identity_total": sum(r["cohort"] == "easy_identity" for r in rows),
    "hard_key_2_matches": sum(r["rival_matches_racket"] for r in rows if r["cohort"] == "hard_key_2"),
    "hard_key_2_total": sum(r["cohort"] == "hard_key_2" for r in rows),
    "finding": (
        "Every sampled easy input has key=1, so the key-ignoring identity rival agrees with all "
        "four independent Racket labels; a legal hard key=2 input refutes the rival. An easy-only "
        "lesson therefore cannot teach the transform-key semantics."
    ),
    "rows": rows,
    "source_reports": [
        "checks/audit/346480121fcb/easy_identity_racket.json",
        "checks/audit/346480121fcb/nonidentity_racket.json",
    ],
}
(ROOT / "ignore_key_rival.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: report[k] for k in (
    "generator_sha256", "rule_text_sha256", "easy_identity_matches",
    "easy_identity_total", "hard_key_2_matches", "hard_key_2_total", "finding"
)}, indent=2))
