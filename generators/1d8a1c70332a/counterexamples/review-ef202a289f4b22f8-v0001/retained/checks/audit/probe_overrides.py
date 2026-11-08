from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter, deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[2] / "repo"
OUT_ROOT = Path(__file__).resolve().parent


def load(task: str):
    path = REPO / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        q = deque([start])
        cells = []
        while q:
            r, c = q.popleft()
            cells.append((r, c))
            for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                p = (r+dr, c+dc)
                if p in unseen:
                    unseen.remove(p)
                    q.append(p)
        out.append(cells)
    return out


def probe_1d():
    task = "1d8a1c70332a"
    gen, path = load(task)
    requested = {
        "grid_h": 22,
        "grid_w": 24,
        "anchor_size": 10,
        "anchor_color": 9,
        "palette_size": 2,
        "position_bias": "anchor_plus_marker",
        "n_distinct_colors": 2,
        "texture": "warm",
    }
    grid = gen.generate(20261008, 17, difficulty="medium", **requested)
    non_marker = [(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,1)]
    observed = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "anchor_size": len(non_marker),
        "anchor_colors": sorted({v for _,_,v in non_marker}),
        "color_1_cells": sum(v == 1 for row in grid for v in row),
        "self_check": gen.self_check(grid),
    }
    try:
        typo = gen.generate(20261008, 17, difficulty="medium", typo_axis=123)
        typo_result = {"accepted": True, "grid_h": len(typo), "grid_w": len(typo[0])}
    except Exception as exc:  # evidence, not a test harness
        typo_result = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "task_id": task,
        "generator_sha256": sha(path),
        "requested": requested,
        "observed": observed,
        "exact_controls_honored": (
            observed["grid_h"] == 22
            and observed["grid_w"] == 24
            and observed["anchor_size"] == 10
            and observed["anchor_colors"] == [9]
        ),
        "unknown_override": typo_result,
    }


def probe_9c():
    task = "9c69eb63c11a"
    gen, path = load(task)
    advertised_boundary = {
        "grid_h": 14,
        "grid_w": 14,
        "palette_kind": "warm",
        "n_blobs": 5,
        "palette_size": 5,
        "position_bias": "spread",
        "n_distinct_colors": 5,
        "size_spread": "distinct",
        "texture": "warm",
    }
    try:
        gen.generate(20261008, 18, difficulty="medium", **advertised_boundary)
        boundary_result = {"accepted": True}
    except Exception as exc:
        boundary_result = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}

    requested = dict(advertised_boundary)
    requested["grid_h"] = 11
    requested["grid_w"] = 12
    grid = gen.generate(20261008, 19, difficulty="medium", **requested)
    comps = components(grid)
    observed = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "component_count": len(comps),
        "component_sizes": sorted(map(len, comps)),
        "nonzero_colors": sorted({v for row in grid for v in row if v}),
        "self_check": gen.self_check(grid),
    }
    try:
        typo = gen.generate(20261008, 19, difficulty="medium", typo_axis=123)
        typo_result = {"accepted": True, "grid_h": len(typo), "grid_w": len(typo[0])}
    except Exception as exc:
        typo_result = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "task_id": task,
        "generator_sha256": sha(path),
        "advertised_boundary_request": advertised_boundary,
        "advertised_boundary_result": boundary_result,
        "supported_dimension_request_with_other_advertised_controls": requested,
        "observed": observed,
        "five_blob_controls_honored": (
            observed["component_count"] == 5
            and len(observed["nonzero_colors"]) == 5
        ),
        "unknown_override": typo_result,
    }


report = {"probes": [probe_1d(), probe_9c()]}
output = OUT_ROOT / "override_probe.json"
output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
