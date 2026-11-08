from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

TASK_ID = "41ea3019baeb"
REPO = Path(__file__).resolve().parents[3] / "repo"
OUT = Path(__file__).resolve().parent
SOURCE = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def turn(value, dr, dc):
    if value == 6:
        return {(0, 1): (-1, 0), (0, -1): (1, 0), (-1, 0): (0, 1), (1, 0): (0, -1)}[(dr, dc)]
    if value == 7:
        return {(0, 1): (1, 0), (0, -1): (-1, 0), (-1, 0): (0, -1), (1, 0): (0, 1)}[(dr, dc)]
    return dr, dc


def mirror_interactions(grid, start):
    h, w = len(grid), len(grid[0])
    row, col = start
    dr, dc = 0, 1
    touched = []
    for _ in range(h * w * 8):
        row, col = row + dr, col + dc
        if not (0 <= row < h and 0 <= col < w):
            break
        value = grid[row][col]
        if value in (5, 6, 7):
            touched.append((row, col, value))
        if value == 5 or (value != 0 and value not in (6, 7)):
            break
        dr, dc = turn(value, dr, dc)
    return touched


def straight_right(grid):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            for cc in range(c + 1, len(row)):
                if grid[r][cc] != 0:
                    break
                out[r][cc] = 8
    return out


def canonical_input():
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        obj = json.loads(line)
        if obj.get("task_id") == TASK_ID:
            pair = obj["train"][0]
            return pair["input"] if isinstance(pair, dict) else pair[0]
    raise RuntimeError("canonical task absent")


def main():
    gen = load_generator()
    counts = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        stats = Counter()
        for index in range(100):
            seed = 50000 + 10000 * band_index + index
            grid = gen.generate(seed, index, difficulty=band)
            errors = gen.self_check(grid)
            emitters = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
            touched = [hit for emitter in emitters for hit in mirror_interactions(grid, emitter)]
            stats["draws"] += 1
            stats["validator_pass"] += not errors
            stats["zero_mirror_interactions"] += not touched
            stats["at_least_one_mirror_interaction"] += bool(touched)
            stats["at_least_two_mirror_interactions"] += len(touched) >= 2
        counts[band] = dict(stats)

    lesson = [gen.generate(1000, index, difficulty="easy") for index in range(4)]
    lesson_rivals = [straight_right(grid) for grid in lesson]
    canonical = canonical_input()
    report = {
        "schema": "arc-audit-mirror-shortcut-probe-v2",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "counts": counts,
        "sample_recipe": {
            "distribution": "100 draws/band; seed=50000+10000*band_index+index; sample_index=index",
            "lesson": "difficulty=easy, seed=1000, sample_index=0..3",
        },
        "lesson_validator_errors": [gen.self_check(grid) for grid in lesson],
        "lesson_mirror_interaction_counts": [
            sum(len(mirror_interactions(grid, (r, c))) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
            for grid in lesson
        ],
    }
    (OUT / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (OUT / "lesson-inputs.json").write_text(json.dumps(lesson, indent=2) + "\n")
    (OUT / "lesson-rivals.json").write_text(json.dumps(lesson_rivals, indent=2) + "\n")
    (OUT / "canonical-input.json").write_text(json.dumps(canonical, indent=2) + "\n")
    (OUT / "canonical-rival.json").write_text(json.dumps(straight_right(canonical), indent=2) + "\n")


if __name__ == "__main__":
    main()
