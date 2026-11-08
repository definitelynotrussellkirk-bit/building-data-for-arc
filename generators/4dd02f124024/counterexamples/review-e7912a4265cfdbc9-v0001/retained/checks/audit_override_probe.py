from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(task_id: str):
    path = ROOT / "repo" / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def digest_grid(grid):
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def probe_4dd():
    task_id = "4dd02f124024"
    module, path = load(task_id)
    seed, sample_index, difficulty = 0, 0, "medium"
    cases = []
    for overrides in ({"palette_kind": "warm"}, {"palette_kind": "cool"}):
        grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
        cases.append({
            "overrides": overrides,
            "grid": grid,
            "grid_sha256": digest_grid(grid),
            "shape": [len(grid), len(grid[0])],
            "palette": sorted({value for row in grid for value in row if value != 0}),
            "self_check": module.self_check(grid, difficulty=difficulty, meta=overrides),
        })
    return {
        "schema": "arcpuzzles-audit-override-noop-v1",
        "command": ["python3", "checks/audit_override_probe.py"],
        "cwd": "packet_root",
        "environment": {"PYTHONPATH": "repo:repo/shared/runtime"},
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "declared_axis": module.AXES["palette_kind"],
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "cases": cases,
        "same_grid": cases[0]["grid"] == cases[1]["grid"],
        "finding": "palette_kind warm and cool are accepted but produce the same grid and palette",
    }


def probe_675():
    task_id = "67504673cd7c"
    module, path = load(task_id)
    seed, sample_index, difficulty = 0, 0, "medium"
    cases = []
    for overrides in ({"num_anchors": 2}, {"num_anchors": 5}):
        grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
        anchors = [
            [r, c, grid[r][c]]
            for r in range(len(grid))
            for c in range(len(grid[0]))
            if grid[r][c] not in (0, 5)
        ]
        cases.append({
            "overrides": overrides,
            "grid": grid,
            "grid_sha256": digest_grid(grid),
            "shape": [len(grid), len(grid[0])],
            "anchors": anchors,
            "anchor_count": len(anchors),
            "template_cell_count": sum(value == 5 for row in grid for value in row),
            "self_check": module.self_check(grid, difficulty=difficulty, meta=overrides),
        })
    return {
        "schema": "arcpuzzles-audit-override-noop-v1",
        "command": ["python3", "checks/audit_override_probe.py"],
        "cwd": "packet_root",
        "environment": {"PYTHONPATH": "repo:repo/shared/runtime"},
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "declared_axis": module.AXES["num_anchors"],
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "cases": cases,
        "same_grid": cases[0]["grid"] == cases[1]["grid"],
        "finding": "num_anchors 2 and 5 are accepted but both produce the same 3-anchor grid",
    }


if __name__ == "__main__":
    out_root = ROOT / "checks" / "audit"
    reports = [probe_4dd(), probe_675()]
    for report in reports:
        destination = out_root / report["task_id"] / "override_noop.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(destination.relative_to(ROOT))
