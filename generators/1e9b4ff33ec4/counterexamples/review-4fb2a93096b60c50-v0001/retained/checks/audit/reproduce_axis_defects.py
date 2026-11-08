#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

REPO = Path.cwd()
OUT = REPO.parent / "checks" / "audit"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    digest = sha256(path)
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}_{digest[:12]}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path, digest


def inner_positions(grid: list[list[int]]) -> tuple[int, list[list[int]]]:
    counts = Counter(v for row in grid for v in row)
    bg = counts.most_common(1)[0][0]
    non_bg = [c for c in counts if c != bg]
    inner = min(non_bg, key=lambda c: counts[c])
    positions = [[r, c] for r, row in enumerate(grid) for c, value in enumerate(row) if value == inner]
    return inner, positions


def audit_38e() -> dict:
    task_id = "38eaf32b0d29"
    gen, path, digest = load(task_id)
    kwargs = {"difficulty": "medium", "grid_size": 15, "n_outer_marks": 8}
    tr = gen.generate(123, 0, inner_position="tr", **kwargs)
    br = gen.generate(123, 0, inner_position="br", **kwargs)
    _, tr_pos = inner_positions(tr)
    _, br_pos = inner_positions(br)
    result = {
        "task_id": task_id,
        "finding": "advertised inner_position='br' aliases top-right instead of bottom-right",
        "generator_path": str(path.relative_to(REPO.parent)),
        "generator_sha256": digest,
        "seed": 123,
        "sample_index": 0,
        "difficulty": "medium",
        "shared_overrides": {"grid_size": 15, "n_outer_marks": 8},
        "compared_overrides": ["tr", "br"],
        "tr_inner_positions": tr_pos,
        "br_inner_positions": br_pos,
        "expected_br_interior_position": [13, 13],
        "byte_identical_grids": tr == br,
        "input_sha256": grid_sha(br),
        "self_check_errors": gen.self_check(br, difficulty="medium"),
        "documented_domain": gen.AXES["inner_position"],
        "input": br,
    }
    assert result["byte_identical_grids"] is True
    assert br_pos == tr_pos == [[1, 13]]
    assert result["self_check_errors"] == []
    dest = OUT / task_id
    (dest / "input.json").write_text(json.dumps(br, indent=2) + "\n")
    (dest / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def audit_1e9() -> dict:
    task_id = "1e9b4ff33ec4"
    gen, path, digest = load(task_id)
    kinds = ["default", "warm", "cool", "varied"]
    found = None
    for seed in range(1000, 1200):
        grids = {
            kind: gen.generate(seed, 0, difficulty="medium", palette_kind=kind)
            for kind in kinds
        }
        if len({grid_sha(g) for g in grids.values()}) == 1 and all(
            gen.self_check(g, difficulty="medium") == [] for g in grids.values()
        ):
            found = (seed, grids)
            break
    assert found is not None
    seed, grids = found
    grid = grids[kinds[0]]
    result = {
        "task_id": task_id,
        "finding": "four advertised palette_kind settings are a silent no-op",
        "generator_path": str(path.relative_to(REPO.parent)),
        "generator_sha256": digest,
        "seed": seed,
        "sample_index": 0,
        "difficulty": "medium",
        "compared_overrides": kinds,
        "all_grids_identical": len({grid_sha(g) for g in grids.values()}) == 1,
        "per_setting_input_sha256": {kind: grid_sha(g) for kind, g in grids.items()},
        "per_setting_self_check_errors": {
            kind: gen.self_check(g, difficulty="medium") for kind, g in grids.items()
        },
        "documented_domain": gen.AXES["palette_kind"],
        "input": grid,
    }
    assert result["all_grids_identical"] is True
    assert all(not errs for errs in result["per_setting_self_check_errors"].values())
    dest = OUT / task_id
    (dest / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (dest / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps({"38eaf32b0d29": audit_38e(), "1e9b4ff33ec4": audit_1e9()}, indent=2))
