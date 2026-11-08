from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter, deque
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
OUT = ROOT / "checks" / "audit"
TASKS = ("a0e364b16592", "66b8f050cbf2")
BANDS = ("easy", "medium", "hard")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def normalize_grid(grid: Any) -> list[list[int]]:
    if isinstance(grid, list) and grid and all(isinstance(row, str) for row in grid):
        return [[int(ch) for ch in row] for row in grid]
    return [[int(v) for v in row] for row in grid]


def canonical_record(task_id: str) -> dict[str, Any]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def nonzero_components(grid: list[list[int]], *, excluded: set[int]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in excluded or (r, c) in seen:
                continue
            comp: list[tuple[int, int]] = []
            q = deque([(r, c)])
            seen.add((r, c))
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] not in excluded:
                        seen.add((nr, nc))
                        q.append((nr, nc))
            comps.append(comp)
    return comps


def rival_global_bottom_preserve_5(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: ignore blocker-separated segments; pack each whole column globally."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        vals = [grid[r][c] for r in range(h) if grid[r][c] not in (0, 5)]
        for r in range(h):
            if grid[r][c] == 5:
                out[r][c] = 5
        start = h - len(vals)
        for r, value in enumerate(vals, start=start):
            out[r][c] = value
    return out


def rival_origin_only_shift(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: read only (0,0); generated samples always put the token there."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    cmd = grid[0][0]
    directions = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
    if cmd not in directions:
        return out
    dr, dc = directions[cmd]
    for r in range(h):
        for c in range(w):
            if (r, c) != (0, 0) and grid[r][c] >= 5:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    out[nr][nc] = grid[r][c]
    return out


def generated_samples(module, task_id: str) -> list[dict[str, Any]]:
    rows = []
    for band_idx, band in enumerate(BANDS):
        for i in range(100):
            seed = band_idx * 100_000 + i
            grid = module.generate(seed, i, difficulty=band)
            errs = module.self_check(grid, difficulty=band, meta={})
            rows.append({"band": band, "seed": seed, "sample_index": i, "grid": grid, "self_check": errs})
    return rows


def select_64(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # 22 easy + 21 medium + 21 hard, stable source-bound sample.
    limits = {"easy": 22, "medium": 21, "hard": 21}
    used = Counter()
    out = []
    for row in rows:
        band = row["band"]
        if used[band] < limits[band]:
            out.append(row)
            used[band] += 1
    assert len(out) == 64
    return out


def audit_task(task_id: str) -> None:
    module, source = load_generator(task_id)
    canonical = canonical_record(task_id)
    pairs = list(canonical.get("train", []))
    test = canonical.get("test", [])
    if isinstance(test, dict):
        pairs.append(test)
    else:
        pairs.extend(test)
    canonical_inputs = [normalize_grid(pair["input"]) for pair in pairs]
    samples = generated_samples(module, task_id)
    sample64 = select_64(samples)
    task_out = OUT / task_id
    task_out.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "schema": "arc-audit-sampler-probe-v1",
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "sample_recipe": {
            "bands": list(BANDS),
            "per_band": 100,
            "seed": "band_index*100000 + i",
            "sample_index": "i",
        },
        "draws": len(samples),
        "self_check_failures": sum(bool(row["self_check"]) for row in samples),
        "canonical_pairs": len(canonical_inputs),
        "canonical_self_check": [module.self_check(g, difficulty=None, meta={}) for g in canonical_inputs],
    }

    if task_id == "a0e364b16592":
        report.update({
            "generated_with_color_5": sum(any(v == 5 for row in s["grid"] for v in row) for s in samples),
            "generated_without_color_5": sum(not any(v == 5 for row in s["grid"] for v in row) for s in samples),
            "canonical_with_color_5": sum(any(v == 5 for row in g for v in row) for g in canonical_inputs),
            "generated_shapes": sorted({(len(s["grid"]), len(s["grid"][0])) for s in samples}),
            "canonical_shapes": sorted({(len(g), len(g[0])) for g in canonical_inputs}),
            "generated_nonzero_component_sizes": dict(Counter(
                size
                for s in samples
                for size in (len(comp) for comp in nonzero_components(s["grid"], excluded={0, 5}))
            )),
            "shortcut": "global_bottom_gravity_preserve_5",
            "shortcut_basis": "all production samples contain no 5, so segment-local and global gravity are identical",
        })
        rival: Callable[[list[list[int]]], list[list[int]]] = rival_global_bottom_preserve_5
    else:
        cmd_positions = []
        duplicate_marker_colors = 0
        marker_component_sizes = Counter()
        for s in samples:
            g = s["grid"]
            positions = [(r, c, g[r][c]) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] in (1, 2, 3, 4)]
            cmd_positions.extend((r, c) for r, c, _ in positions)
            markers = [g[r][c] for r in range(len(g)) for c in range(len(g[0])) if g[r][c] >= 5]
            duplicate_marker_colors += int(len(set(markers)) < len(markers))
            for comp in nonzero_components(g, excluded={0, 1, 2, 3, 4}):
                marker_component_sizes[len(comp)] += 1

        canonical_cmd_positions = []
        for g in canonical_inputs:
            hits = [(r, c, g[r][c]) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] in (1, 2, 3, 4)]
            canonical_cmd_positions.append(hits[-1] if hits else None)
        report.update({
            "generated_cmd_positions": {f"{r},{c}": n for (r, c), n in Counter(cmd_positions).items()},
            "generated_origin_cmd": sum(s["grid"][0][0] in (1, 2, 3, 4) for s in samples),
            "generated_duplicate_marker_colors": duplicate_marker_colors,
            "generated_marker_component_sizes": dict(marker_component_sizes),
            "canonical_cmd_positions": canonical_cmd_positions,
            "generated_shapes": sorted({(len(s["grid"]), len(s["grid"][0])) for s in samples}),
            "canonical_shapes": sorted({(len(g), len(g[0])) for g in canonical_inputs}),
            "shortcut": "origin_only_direction_token",
            "shortcut_basis": "all production samples place the token at (0,0), so scanning the border/grid is unnecessary",
        })
        rival = rival_origin_only_shift

    (task_out / "sampler_probe.json").write_text(json.dumps(report, indent=2) + "\n")
    (task_out / "generated_inputs_64.json").write_text(json.dumps({"inputs": [s["grid"] for s in sample64]}, indent=2) + "\n")
    (task_out / "generated_sample_manifest_64.json").write_text(json.dumps([
        {k: s[k] for k in ("band", "seed", "sample_index")} for s in sample64
    ], indent=2) + "\n")
    (task_out / "rival_generated_outputs_64.json").write_text(json.dumps({
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "shortcut": report["shortcut"],
        "outputs": [rival(s["grid"]) for s in sample64],
    }, indent=2) + "\n")

    counter_input = json.loads((task_out / "input.json").read_text())
    (task_out / "rival_counterexample_output.json").write_text(json.dumps({
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "shortcut": report["shortcut"],
        "input": counter_input,
        "self_check": module.self_check(counter_input, difficulty=None, meta={}),
        "output": rival(counter_input),
    }, indent=2) + "\n")


for task in TASKS:
    audit_task(task)
