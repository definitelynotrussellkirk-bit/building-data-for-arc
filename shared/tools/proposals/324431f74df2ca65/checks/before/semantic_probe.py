from __future__ import annotations

import importlib.util
import json
from collections import deque
from pathlib import Path

ROOT = Path.cwd()
GEN_PATH = ROOT / "generators" / "75be7448827f" / "generator.py"
OUT = ROOT.parent / "checks" / "before" / "semantic_probe.json"

spec = importlib.util.spec_from_file_location("selected_generator", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gen)


def frames(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    result = []
    while remaining:
        start = min(remaining)
        q = deque([start])
        remaining.remove(start)
        cells = {start}
        while q:
            r, c = q.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if p in remaining:
                    remaining.remove(p)
                    cells.add(p)
                    q.append(p)
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        interior = [grid[r][c] for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        count = sum(v != 0 for v in interior)
        area = len(interior)
        result.append({
            "bbox": [r0, c0, r1, c1],
            "shape": [r1 - r0 - 1, c1 - c0 - 1],
            "count": count,
            "area": area,
            "density": count / area if area else None,
            "crop": [row[c0 + 1:c1] for row in grid[r0 + 1:r1]],
        })
    return sorted(result, key=lambda x: x["bbox"])


def analyze(grid):
    fs = frames(grid)
    counts = [f["count"] for f in fs]
    densities = [f["density"] for f in fs]
    max_count = max(counts) if counts else None
    max_density = max(densities) if densities else None
    count_winners = [i for i, x in enumerate(counts) if x == max_count]
    density_winners = [i for i, x in enumerate(densities) if x == max_density]
    return {
        "frames": fs,
        "count_winners": count_winners,
        "density_winners": density_winners,
        "unique_count": len(count_winners) == 1,
        "unique_density": len(density_winners) == 1,
        "same_unique_winner": len(count_winners) == len(density_winners) == 1 and count_winners[0] == density_winners[0],
    }


def canonical_inputs():
    ledger = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.open():
        item = json.loads(line)
        if item.get("task_id") == "75be7448827f":
            pairs = []
            for split in ("train", "test"):
                for index, pair in enumerate(item.get(split, [])):
                    pairs.append((f"{split}{index}", pair["input"], pair.get("output")))
            return pairs
    raise RuntimeError("canonical task missing")


report = {
    "generator_path": str(GEN_PATH.relative_to(ROOT)),
    "canonical": {},
    "bands": {},
    "override_equivalence": {},
}

for name, grid, output in canonical_inputs():
    info = analyze(grid)
    info["labeled_output"] = output
    report["canonical"][name] = info

for band in (None, "easy", "medium", "hard"):
    key = "default" if band is None else band
    stats = {
        "samples": 1000,
        "count_ties": 0,
        "density_ties": 0,
        "different_unique_winner": 0,
        "same_unique_winner": 0,
        "self_check_failures": 0,
        "frame_count_histogram": {},
        "first_count_tie": None,
        "first_different_winner": None,
    }
    for i in range(stats["samples"]):
        seed = 10_000 + i
        grid = gen.generate(seed, i, difficulty=band)
        errors = gen.self_check(grid, difficulty=band)
        if errors:
            stats["self_check_failures"] += 1
        info = analyze(grid)
        n = len(info["frames"])
        stats["frame_count_histogram"][str(n)] = stats["frame_count_histogram"].get(str(n), 0) + 1
        if not info["unique_count"]:
            stats["count_ties"] += 1
            if stats["first_count_tie"] is None:
                stats["first_count_tie"] = {"seed": seed, "sample_index": i, "grid": grid, **info}
        if not info["unique_density"]:
            stats["density_ties"] += 1
        if info["same_unique_winner"]:
            stats["same_unique_winner"] += 1
        elif info["unique_count"] and info["unique_density"]:
            stats["different_unique_winner"] += 1
            if stats["first_different_winner"] is None:
                stats["first_different_winner"] = {"seed": seed, "sample_index": i, "grid": grid, **info}
    report["bands"][key] = stats

base_seed = 123
base_index = 17
controls = {
    "palette_kind": ["default", "warm", "cool", "varied"],
    "palette_size": [2, 3, 4, 5],
    "position_bias": ["scattered_frames"],
    "n_distinct_colors": [2, 3, 4, 5],
    "density": ["sparse"],
    "texture": ["default", "warm", "cool", "varied"],
}
for name, values in controls.items():
    grids = []
    errors = []
    for value in values:
        try:
            grids.append(gen.generate(base_seed, base_index, **{name: value}))
            errors.append(None)
        except Exception as exc:  # evidence only
            grids.append(None)
            errors.append(f"{type(exc).__name__}: {exc}")
    report["override_equivalence"][name] = {
        "values": values,
        "errors": errors,
        "unique_grid_count": len({json.dumps(g) for g in grids if g is not None}),
    }

OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({
    "canonical": {k: {"counts": [f["count"] for f in v["frames"]],
                       "densities": [round(f["density"], 4) for f in v["frames"]],
                       "count_winners": v["count_winners"],
                       "density_winners": v["density_winners"]}
                  for k, v in report["canonical"].items()},
    "bands": {k: {kk: vv for kk, vv in v.items() if kk not in {"first_count_tie", "first_different_winner"}}
              for k, v in report["bands"].items()},
    "override_equivalence": report["override_equivalence"],
    "out": str(OUT),
}, indent=2))
