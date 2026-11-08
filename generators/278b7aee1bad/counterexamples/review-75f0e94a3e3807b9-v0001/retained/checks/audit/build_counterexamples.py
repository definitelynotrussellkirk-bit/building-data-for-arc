#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2] / "repo"
OUT = Path(__file__).resolve().parent


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def audit_278() -> None:
    tid = "278b7aee1bad"
    gen, source = load_generator(tid)
    # Three colors occur exactly twice, but every pair is diagonal rather than
    # horizontal/vertical. This violates the documented source domain while
    # satisfying the current validator's count-only check.
    grid = [[0 for _ in range(10)] for _ in range(8)]
    for color, a, b in (
        (1, (1, 1), (2, 2)),
        (2, (3, 3), (4, 4)),
        (3, (5, 5), (6, 6)),
    ):
        grid[a[0]][a[1]] = color
        grid[b[0]][b[1]] = color
    errors = gen.self_check(grid, difficulty="easy", meta={})
    pair_positions = {}
    for color in (1, 2, 3):
        positions = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        pair_positions[str(color)] = positions
    aligned = {
        color: bool(pos[0][0] == pos[1][0] or pos[0][1] == pos[1][1])
        for color, pos in pair_positions.items()
    }
    payload = {
        "task_id": tid,
        "generator_sha256": sha256(source),
        "documented_invariants": list(gen.INVARIANTS),
        "input": grid,
        "pair_positions": pair_positions,
        "aligned_by_color": aligned,
        "self_check_errors": errors,
        "reproduced_defect": errors == [] and not all(aligned.values()),
        "explanation": (
            "self_check counts colors occurring exactly twice but never verifies that each pair is aligned, "
            "that orientations are mixed, or that spans cross."
        ),
    }
    out_dir = OUT / f"{tid}-counterexample"
    dump(out_dir / "input.json", grid)
    dump(out_dir / "validator-witness.json", payload)


def audit_784() -> None:
    tid = "784b131b3b93"
    gen, source = load_generator(tid)
    requested = 1
    overrides = {
        "grid_h": 3,
        "half_w": 3,
        "left_color": 1,
        "right_color": 2,
        "left_density": 0.0,
        "right_density": 0.0,
        "panel_pattern": "random",
        "both_zero_target": requested,
    }
    grid = gen.generate(0, 0, difficulty="easy", **overrides)
    h, width = len(grid), len(grid[0])
    half = width // 2
    actual = sum(
        1
        for r in range(h)
        for c in range(half)
        if grid[r][c] == 0 and grid[r][c + half] == 0
    )
    errors = gen.self_check(grid, difficulty="easy", meta=overrides)
    payload = {
        "task_id": tid,
        "generator_sha256": sha256(source),
        "seed": 0,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": overrides,
        "input": grid,
        "requested_both_zero_target": requested,
        "observed_both_zero_count": actual,
        "self_check_errors": errors,
        "reproduced_defect": actual != requested and errors == [],
        "explanation": (
            "both_zero_target is treated as a minimum by _ensure_both_zero, and the later forced evidence rewrite "
            "can change the count again; an accepted exact override therefore does not equal the realized value."
        ),
    }
    out_dir = OUT / f"{tid}-counterexample"
    dump(out_dir / "input.json", grid)
    dump(out_dir / "target-witness.json", payload)


if __name__ == "__main__":
    audit_278()
    audit_784()
