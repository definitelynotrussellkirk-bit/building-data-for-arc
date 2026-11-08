#!/usr/bin/env python3
"""Reusable, source-bound oracle and lesson probe for ``cad61106e2b9``."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
GEN_PATH = HOME / "generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(path: Path = GEN_PATH):
    spec = importlib.util.spec_from_file_location("probe_cad61106e2b9", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _norm(grid):
    return [[int(ch) for ch in row] if isinstance(row, str) else list(row) for row in grid]


def canonical_pairs():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != "cad61106e2b9":
                continue
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [
                {"input": _norm(pair["input"]), "output": _norm(pair["output"])}
                for pair in [*row["train"], *test]
            ]
    raise RuntimeError("canonical task not found")


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 4 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append(cells)
    return found


def independent_output(grid):
    output = copy.deepcopy(grid)
    control = next(value for row in grid for value in row if value in (1, 2, 3))
    boxes = []
    for cells in _components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        box = (min(rows), min(cols), max(rows), max(cols))
        expected = {
            (r, c)
            for r in range(box[0], box[2] + 1)
            for c in range(box[1], box[3] + 1)
            if r in (box[0], box[2]) or c in (box[1], box[3])
        }
        if cells != expected:
            raise ValueError(f"non-frame component: {box}")
        boxes.append(box)
    boxes.sort(key=lambda b: (b[2] - b[0] + 1) * (b[3] - b[1] + 1), reverse=True)
    selected = boxes[control - 1]
    inner = boxes[control] if control < len(boxes) else None
    for r in range(selected[0] + 1, selected[2]):
        for c in range(selected[1] + 1, selected[3]):
            if grid[r][c] != 0:
                continue
            if inner is not None and inner[0] <= r <= inner[2] and inner[1] <= c <= inner[3]:
                continue
            output[r][c] = 8
    return output


def run_probe(*, lessons_per_band: int = 10, seed: int = 1907):
    gen = load_generator()
    canonical = canonical_pairs()
    report = {
        "generator_sha256": file_sha256(GEN_PATH),
        "canonical_pairs": len(canonical),
        "canonical_oracle_mismatches": sum(
            independent_output(pair["input"]) != pair["output"] for pair in canonical
        ),
        "generated_examples": 0,
        "generation_failures": [],
        "lesson_failures": [],
        "surviving_competitors": {
            name: 0 for name in sorted(gen.LESSON_COMPETITORS)
        },
    }
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for lesson_index in range(lessons_per_band):
            start = lesson_index * 11
            demos = []
            try:
                for offset in range(gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed + 100 * band_index + lesson_index, start + offset, difficulty=difficulty)
                    expected = independent_output(grid)
                    if gen.self_check(grid):
                        raise AssertionError(gen.self_check(grid))
                    if gen.rule_mirror(grid) != expected:
                        raise AssertionError("generator mirror disagrees with independent oracle")
                    demos.append({"input": grid, "output": expected})
                    report["generated_examples"] += 1
                query_grid = gen.generate(
                    seed + 100 * band_index + lesson_index,
                    start + gen.EXAMPLES_NEEDED,
                    difficulty=difficulty,
                )
                query = {"input": query_grid, "output": independent_output(query_grid)}
                report["generated_examples"] += 1
            except Exception as exc:
                report["generation_failures"].append(
                    {"difficulty": difficulty, "lesson": lesson_index, "error": repr(exc)}
                )
                continue

            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                report["lesson_failures"].append(
                    {"difficulty": difficulty, "lesson": lesson_index, "reasons": reasons}
                )
            for name, rival in gen.LESSON_COMPETITORS.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    report["surviving_competitors"][name] += 1
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1907)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(lessons_per_band=args.lessons_per_band, seed=args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 1 if report["generation_failures"] or report["lesson_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
