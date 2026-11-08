"""Independent probes for generator 0a9ee3cbb232.

The Python oracle here is review tooling, not label authority.  It computes the
written horizontal-run rule directly from pixels and exposes repeatable
curriculum/rival checks for future reviewers.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

TASK = "0a9ee3cbb232"
ROOT = Path(__file__).resolve().parents[3]
CANVAS_PROFILES = ((10, 14), (10, 10), (13, 15), (10, 19), (15, 10))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_row():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def run_counts(grid):
    counts = {}
    for color in (3, 2):
        total = 0
        for row in grid:
            active = False
            for value in row:
                if value == color:
                    if not active:
                        total += 1
                    active = True
                else:
                    active = False
        counts[color] = total
    return counts[3], counts[2]


def tally(n3, n2):
    out = [[0] * 3 for _ in range(2)]
    for index in range(6):
        if index < n3:
            out[index // 3][index % 3] = 3
        elif index < n3 + n2:
            out[index // 3][index % 3] = 2
    return out


def rule_output(grid):
    return tally(*run_counts(grid))


def component_count(grid, color):
    h, w = len(grid), len(grid[0])
    todo = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    components = 0
    while todo:
        components += 1
        queue = deque([todo.pop()])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if 0 <= point[0] < h and 0 <= point[1] < w and point in todo:
                    todo.remove(point)
                    queue.append(point)
    return components


def connected_components_output(grid):
    return tally(component_count(grid, 3), component_count(grid, 2))


def occupied_rows_output(grid):
    return tally(
        sum(any(value == 3 for value in row) for row in grid),
        sum(any(value == 2 for value in row) for row in grid),
    )


def drop_twos_on_overflow_output(grid):
    n3, n2 = run_counts(grid)
    return tally(n3, 0 if n3 + n2 > 6 else n2)


def observed(grid):
    palette = {value for row in grid for value in row}
    background = next(iter(palette - {2, 3}))
    return {
        "canvas_profile": CANVAS_PROFILES.index((len(grid), len(grid[0]))),
        "n_3": run_counts(grid)[0],
        "n_2": run_counts(grid)[1],
        "background": background,
    }


def selected_rule_sources():
    row = canonical_row()
    selected = {"canonical": row["program_solution"]}
    for path in sorted((ROOT / "shared/data/base/solutions").rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("task_id") != TASK:
            continue
        selected[str(path.relative_to(ROOT))] = data["racket_target"]["target_code"]
    return selected


def normalized(text):
    return " ".join(text.split())


def lesson(seed, start, band, count=4):
    generator = load_generator()
    pairs = []
    for offset in range(count):
        grid = generator.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": rule_output(grid)})
    return pairs
