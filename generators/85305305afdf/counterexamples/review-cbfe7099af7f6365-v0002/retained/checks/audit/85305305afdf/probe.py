from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import load_selected_generator

TASK = "85305305afdf"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK
GEN, SOURCE, SHA = load_selected_generator(TASK, root=ROOT)
seed, sample_index, difficulty = 20261007, 11, "medium"

def attempt(**kwargs):
    try:
        grid = GEN.generate(seed, sample_index, difficulty=difficulty, **kwargs)
        return {"status": "accepted", "grid": grid, "self_check": GEN.self_check(grid)}
    except Exception as exc:
        return {"status": "raised", "exception": type(exc).__name__, "message": str(exc)}

base = attempt()
textures = {name: attempt(texture=name) for name in ("default", "warm", "cool", "varied")}
right_edge = attempt(texture="cell_at_right_edge")
unknown = attempt(typo_axis=99)
bounds = {
    "grid_h=12": attempt(grid_h=12),
    "grid_w=16": attempt(grid_w=16),
    "cells=12": attempt(cells=12),
}
record = {
    "schema": "audit-85305305afdf-v1",
    "task_id": TASK,
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SHA,
    "generator_version": GEN.VERSION,
    "replay": {"seed": seed, "sample_index": sample_index, "difficulty": difficulty},
    "base": base,
    "helpful_textures": textures,
    "helpful_textures_equal_base": {name: row.get("grid") == base.get("grid") for name, row in textures.items()},
    "right_edge": right_edge,
    "right_edge_identity_rival": right_edge.get("grid"),
    "unknown_override": unknown,
    "unknown_override_equal_base": unknown.get("grid") == base.get("grid"),
    "declared_upper_bound_attempts": bounds,
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "probe.json").write_text(json.dumps(record, indent=2) + "\n")
(OUT / "input.json").write_text(json.dumps(right_edge["grid"], indent=2) + "\n")
(OUT / "identity_rival.json").write_text(json.dumps(right_edge["grid"], indent=2) + "\n")
print(json.dumps(record, indent=2))
