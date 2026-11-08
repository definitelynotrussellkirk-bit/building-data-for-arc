#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "8d7d1364cf11"
SOURCE = REPO / "generators" / TASK / "generator.py"
BG = 4

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def components(grid: list[list[int]]) -> list[list[tuple[int, int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int, int]]] = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] == BG:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c, grid[r][c]))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and (nr, nc) not in seen
                            and grid[nr][nc] != BG
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def transform(grid: list[list[int]], *, choose_last: bool) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    comps = components(grid)
    shapes = [comp for comp in comps if len(comp) > 1]
    dots = [comp[0] for comp in comps if len(comp) == 1]
    output = [[BG] * w for _ in range(h)]
    for dr, dc, dot_color in dots:
        matches = [
            (shape, ar, ac)
            for shape in shapes
            for ar, ac, color in shape
            if color == dot_color
        ]
        if not matches:
            continue
        shape, ar, ac = matches[-1 if choose_last else 0]
        for sr, sc, color in shape:
            nr, nc = dr + sr - ar, dc + sc - ac
            if 0 <= nr < h and 0 <= nc < w:
                output[nr][nc] = color
    return output


def canonical_task() -> dict:
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise RuntimeError(f"missing canonical task {TASK}")


def dot_match_report(grid: list[list[int]]) -> list[dict]:
    comps = components(grid)
    shapes = [comp for comp in comps if len(comp) > 1]
    dots = [comp[0] for comp in comps if len(comp) == 1]
    rows = []
    for r, c, color in dots:
        matches = [
            {"shape_index": i, "row": sr, "col": sc}
            for i, shape in enumerate(shapes)
            for sr, sc, value in shape
            if value == color
        ]
        rows.append({"dot": {"row": r, "col": c, "color": color}, "matches": matches})
    return rows

seed, sample_index, difficulty = 0, 0, "easy"
grid = mod.generate(seed, sample_index, difficulty=difficulty)
first = transform(grid, choose_last=False)
last = transform(grid, choose_last=True)
canonical = canonical_task()
canonical_rows = []
for split in ("train", "test"):
    for index, pair in enumerate(canonical[split]):
        first_fit = transform(pair["input"], choose_last=False) == pair["output"]
        last_fit = transform(pair["input"], choose_last=True) == pair["output"]
        canonical_rows.append({"split": split, "index": index, "first_fit": first_fit, "last_fit": last_fit})

(HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(HERE / "row_major_first.json").write_text(json.dumps(first, indent=2) + "\n")
(HERE / "row_major_last.json").write_text(json.dumps(last, indent=2) + "\n")

racket_path = HERE / "racket.json"
racket_output = None
racket_matches = None
rival_name = None
rival_output = None
if racket_path.is_file():
    racket = json.loads(racket_path.read_text())
    racket_output = racket["results"][0]["output"]
    racket_matches = {
        "row_major_first": racket_output == first,
        "row_major_last": racket_output == last,
    }
    if racket_output == first and last != first:
        rival_name, rival_output = "row_major_last", last
    elif racket_output == last and first != last:
        rival_name, rival_output = "row_major_first", first
    elif first != last:
        rival_name = "row_major_last_if_racket_is_otherwise"
        rival_output = last
    if rival_output is not None:
        (HERE / "rival.json").write_text(json.dumps(rival_output, indent=2) + "\n")

report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "self_check_findings": mod.self_check(grid),
    "dot_matches": dot_match_report(grid),
    "ambiguous_dots": [row for row in dot_match_report(grid) if len(row["matches"]) > 1],
    "canonical_variant_fits": canonical_rows,
    "all_canonical_fit_first": all(row["first_fit"] for row in canonical_rows),
    "all_canonical_fit_last": all(row["last_fit"] for row in canonical_rows),
    "first_last_disagree": first != last,
    "racket_matches": racket_matches,
    "selected_rival": rival_name,
}
assert report["self_check_findings"] == []
assert report["ambiguous_dots"]
assert report["all_canonical_fit_first"] is True
assert report["all_canonical_fit_last"] is True
assert report["first_last_disagree"] is True
if racket_output is not None:
    assert rival_output is not None and rival_output != racket_output
(HERE / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
