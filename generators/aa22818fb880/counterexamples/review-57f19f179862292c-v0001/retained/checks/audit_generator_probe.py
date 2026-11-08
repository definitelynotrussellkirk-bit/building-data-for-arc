from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from collections import Counter, deque
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))


def load(tid: str):
    path = REPO / "generators" / tid / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{tid}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plus_centers(grid):
    h, w = len(grid), len(grid[0])
    result = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            color = grid[r][c]
            if color and sum(
                grid[r + dr][c + dc] == color
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ) == 3:
                result.append((r, c, color))
    return result


def components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        comp = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        result.append(comp)
    return result


aa = load("aa22818fb880")
bb = load("98e86aae9095")

try:
    aa.generate(0, 0, difficulty="easy", grid_h=5)
    aa_boundary = {"accepted": True}
except Exception as exc:
    aa_boundary = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}

try:
    aa_unknown_grid = aa.generate(0, 0, difficulty="medium", __unknown_axis__=1)
    aa_unknown = {"accepted": True, "shape": [len(aa_unknown_grid), len(aa_unknown_grid[0])]}
except Exception as exc:
    aa_unknown = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}

underplacement = None
for seed in range(500):
    grid = aa.generate(seed, 0, difficulty="easy", n_motifs=2)
    actual = len(plus_centers(grid))
    if actual != 2:
        underplacement = {
            "seed": seed,
            "difficulty": "easy",
            "overrides": {"n_motifs": 2},
            "actual_partial_plus_centers": actual,
            "self_check": aa.self_check(grid, difficulty="easy"),
            "grid": grid,
        }
        break

color_count_violations = []
aa_draws = 0
for band in ("easy", "medium", "hard"):
    for seed in range(100):
        grid = aa.generate(seed, seed % 7, difficulty=band)
        aa_draws += 1
        counts = Counter(value for row in grid for value in row if value)
        if any(count != 4 for count in counts.values()):
            color_count_violations.append({"band": band, "seed": seed, "counts": dict(counts)})

inert = {}
for axis, left, right in (
    ("shape", 0, 3),
    ("sequence", 0, 3),
    ("palette_kind", "warm", "cool"),
):
    left_grid = bb.generate(17, 0, difficulty="medium", **{axis: left})
    right_grid = bb.generate(17, 0, difficulty="medium", **{axis: right})
    inert[axis] = {
        "left": left,
        "right": right,
        "identical": left_grid == right_grid,
        "grid_sha256": hashlib.sha256(json.dumps(left_grid).encode()).hexdigest(),
    }

try:
    bb_unknown_grid = bb.generate(0, 0, difficulty="medium", __unknown_axis__=1)
    bb_unknown = {"accepted": True, "shape": [len(bb_unknown_grid), len(bb_unknown_grid[0])]}
except Exception as exc:
    bb_unknown = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}

multi_key_component = []
bb_draws = 0
for band in ("easy", "medium", "hard"):
    for seed in range(200):
        grid = copy.deepcopy(bb.generate(seed, seed % 11, difficulty=band))
        key = grid[-1][0]
        grid[-1][0] = 0
        grid[0] = [0] * len(grid[0])
        n_components = len(components_of_color(grid, key))
        bb_draws += 1
        if n_components != 1:
            multi_key_component.append({"band": band, "seed": seed, "components": n_components})

report = {
    "aa22818fb880": {
        "declared_valid_grid_h_5_on_easy": aa_boundary,
        "unknown_override": aa_unknown,
        "underplacement": underplacement,
        "generated_color_count_census": {
            "draws": aa_draws,
            "violations_of_exactly_four_cells_per_color": len(color_count_violations),
            "examples": color_count_violations[:3],
        },
    },
    "98e86aae9095": {
        "inert_declared_axes": inert,
        "unknown_override": bb_unknown,
        "generated_key_component_census": {
            "draws": bb_draws,
            "draws_with_component_count_other_than_one": len(multi_key_component),
            "examples": multi_key_component[:3],
        },
    },
}
print(json.dumps(report, indent=2, sort_keys=True))
(ROOT / "checks/audit_generator_findings.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
