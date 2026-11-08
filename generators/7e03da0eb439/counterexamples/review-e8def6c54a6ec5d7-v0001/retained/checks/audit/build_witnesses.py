from __future__ import annotations

import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical(task_id: str):
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def comps_of_value(grid, value):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != value or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == value and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def dot_any_odd_red_bbox(grid):
    """Canonical-fitting shortcut: ignore whether the red bbox is hollow."""
    out = deepcopy(grid)
    for cells in comps_of_value(grid, 2):
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        h, w = r2 - r1 + 1, c2 - c1 + 1
        if h >= 3 and w >= 3 and h % 2 == 1 and w % 2 == 1:
            out[(r1 + r2) // 2][(c1 + c2) // 2] = 8
    return out


def self_tile_predicate(grid, predicate):
    h, w = len(grid), len(grid[0])
    out = [[0] * (w * w) for _ in range(h * h)]
    for tr in range(h):
        for tc in range(w):
            if predicate(grid[tr][tc]):
                for r in range(h):
                    for c in range(w):
                        out[tr * h + r][tc * w + c] = grid[r][c]
    return out


def self_tile_gt_one(grid):
    """Canonical-fitting shortcut: use v>1, indistinguishable on colors {0,1,2}."""
    return self_tile_predicate(grid, lambda value: value > 1)


def pairs(row):
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def write(task_id, grid, rival, *, seed, sample_index, difficulty, overrides,
          rival_name, rival_description, canonical_fit):
    directory = ROOT / "checks" / "audit" / task_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "input.json").write_text(json.dumps(grid, separators=(",", ":")) + "\n")
    (directory / "rival.json").write_text(json.dumps(rival, separators=(",", ":")) + "\n")
    generator_path = REPO / "generators" / task_id / "generator.py"
    metadata = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
        "rival": rival_name,
        "rival_description": rival_description,
        "canonical_pairs_fit": canonical_fit,
        "canonical_pairs_total": canonical_fit,
        "input_file": f"checks/audit/{task_id}/input.json",
        "rival_file": f"checks/audit/{task_id}/rival.json",
        "construction_script": "checks/audit/build_witnesses.py",
    }
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return metadata


def main():
    task = "02b1f274e160"
    gen = load_generator(task)
    row = canonical(task)
    fit = sum(dot_any_odd_red_bbox(pair["input"]) == pair["output"] for pair in pairs(row))
    assert fit == len(pairs(row))
    witness = None
    for seed in range(200):
        grid = gen.generate(seed, 0, difficulty=None, texture="solid_rect")
        rival = dot_any_odd_red_bbox(grid)
        # A witness has an extra 8 over input at a center that is not guaranteed
        # to be a true hollow frame.  Canonical output is checked later by Racket.
        if rival != grid and gen.self_check(grid) == []:
            witness = seed, grid, rival
            break
    assert witness is not None
    seed, grid, rival = witness
    write(task, grid, rival, seed=seed, sample_index=0, difficulty=None,
          overrides={"texture": "solid_rect"},
          rival_name="dot_any_odd_red_bbox",
          rival_description=("set the center of every red component with an odd >=3x3 "
                             "bounding box, without checking that it is exactly a hollow outline"),
          canonical_fit=fit)

    task = "7e03da0eb439"
    gen = load_generator(task)
    row = canonical(task)
    fit = sum(self_tile_gt_one(pair["input"]) == pair["output"] for pair in pairs(row))
    assert fit == len(pairs(row))
    witness = None
    for seed in range(200):
        grid = gen.generate(seed, 0, difficulty=None, grid_size=3,
                            texture="mixed_full", non_2_palette_size=3)
        rival = self_tile_gt_one(grid)
        if any(value > 2 for row_ in grid for value in row_) and gen.self_check(grid) == []:
            witness = seed, grid, rival
            break
    assert witness is not None
    seed, grid, rival = witness
    write(task, grid, rival, seed=seed, sample_index=0, difficulty=None,
          overrides={"grid_size": 3, "texture": "mixed_full", "non_2_palette_size": 3},
          rival_name="self_tile_values_gt_one",
          rival_description=("stamp the input at every cell whose value is greater than 1, "
                             "rather than only cells equal to 2"),
          canonical_fit=fit)


if __name__ == "__main__":
    main()
