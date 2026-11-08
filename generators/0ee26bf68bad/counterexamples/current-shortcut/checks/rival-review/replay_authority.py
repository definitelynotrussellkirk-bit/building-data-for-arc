"""Replay retained witness labels with the selected canonical Racket authority.

Run from WORK:
  python3 run_with_racket.py python3 ../checks/rival-review/replay_authority.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge


RIVAL_NAMES = (
    "color_frequency", "objects8", "contour8", "bbox_area", "bbox_frame", "bbox_strip"
)
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def components(grid, *, diagonal=False, aggregate=False):
    points = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = []
    while points:
        start = min(points)
        color = grid[start[0]][start[1]]
        if aggregate:
            cells = {p for p in points if grid[p[0]][p[1]] == color}
            points -= cells
        else:
            cells = {start}
            points.remove(start)
            pending = [start]
            while pending:
                r, c = pending.pop()
                for dr, dc in DIRS4 + (DIAGONALS if diagonal else ()):
                    point = r + dr, c + dc
                    if point in points and grid[point[0]][point[1]] == color:
                        points.remove(point)
                        cells.add(point)
                        pending.append(point)
        result.append((color, cells))
    return result


def bbox(cells):
    return (
        min(r for r, c in cells), min(c for r, c in cells),
        max(r for r, c in cells), max(c for r, c in cells),
    )


def rival(grid, name):
    """Diagnostic alternative rule. This function never supplies reference labels."""
    def rank(obj):
        a, b, c, d = bbox(obj[1])
        size = (c - a + 1) * (d - b + 1) if name == "bbox_area" else len(obj[1])
        return -size, a, b

    color, cells = min(
        components(grid, diagonal=name == "objects8", aggregate=name == "color_frequency"),
        key=rank,
    )
    a, b, c, d = bbox(cells)
    output = [[0] * (d - b + 1) for _ in range(c - a + 1)]
    directions = DIRS4 + (DIAGONALS if name == "contour8" else ())
    for r in range(a, c + 1):
        for column in range(b, d + 1):
            edge = r in (a, c) or column in (b, d)
            if name == "bbox_frame":
                paint = edge
            elif name == "bbox_strip":
                paint = edge and (r, column) in cells
            else:
                paint = (r, column) in cells and any(
                    (r + dr, column + dc) not in cells for dr, dc in directions
                )
            if paint:
                output[r - a][column - b] = color
    return output


def main() -> None:
    root = Path.cwd()
    evidence = Path(__file__).with_name("authoritative-witnesses.json")
    receipt = json.loads(evidence.read_text())
    canonical = next(
        row
        for line in (root / "shared/data/canonical/puzzles.jsonl").open()
        if (row := json.loads(line)).get("task_id") == receipt["task_id"]
    )
    program = canonical["program_solution"]
    assert hashlib.sha256(program.encode()).hexdigest() == receipt["program_source_sha256"]
    prelude = root / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt"
    assert hashlib.sha256(prelude.read_bytes()).hexdigest() == receipt["prelude_sha256"]
    assert program.startswith("(rule! ") and program.endswith(")")
    body = program[len("(rule! ") : -1]
    bridge = RacketBridge()
    checked = []
    try:
        bridge.eval_text("(define (review-authority g) " + body + ")")
        for split in ("train", "test"):
            for index, pair in enumerate(canonical[split]):
                bridge.define_grid("review-grid", pair["input"])
                actual = bridge.eval_text("(review-authority review-grid)")
                assert actual == pair["output"], (split, index, actual)
                for name in RIVAL_NAMES:
                    assert rival(pair["input"], name) == actual, (split, index, name)
                checked.append(f"canonical_{split}_{index}")
        for case in receipt["cases"]:
            bridge.define_grid("review-grid", case["input"])
            actual = bridge.eval_text("(review-authority review-grid)")
            assert actual == case["racket_output"], (case["name"], actual)
            for name in RIVAL_NAMES:
                prediction = rival(case["input"], name)
                saved = case["rivals"][name]
                assert prediction == saved["prediction"], (case["name"], name)
                assert (prediction != actual) == saved["differs"], (case["name"], name)
            checked.append(case["name"])
    finally:
        bridge.shutdown()
    print(json.dumps({"status": "pass", "racket_labels_replayed": len(checked),
                      "canonical_fitting_rivals": list(RIVAL_NAMES),
                      "checked": checked}, sort_keys=True))


if __name__ == "__main__":
    main()
