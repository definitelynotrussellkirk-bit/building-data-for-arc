#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path[:0] = [str(ROOT / "shared/runtime"), str(ROOT / "src")]
from reviewer_support import load_selected_generator

TASK_ID = "758360aea29b"

def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def call(gen, *, seed=991, sample_index=0, difficulty="easy", overrides=None):
    overrides = dict(overrides or {})
    try:
        grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
    except Exception as exc:
        return {"accepted": False, "exception": f"{type(exc).__name__}: {exc}"}
    return {
        "accepted": True,
        "shape": [len(grid), len(grid[0])],
        "palette": sorted({value for row in grid for value in row}),
        "grid_sha256": grid_hash(grid),
        "self_check": gen.self_check(grid, difficulty=difficulty),
        "grid": grid if overrides.get("texture") == "no_objects" else None,
    }

def main():
    gen, path, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    default = call(gen)
    warm = call(gen, overrides={"texture": "warm"})
    palette_warm = call(gen, overrides={"palette_kind": "warm"})
    report = {
        "schema": "arc-audit-contract-probe-v1",
        "task_id": TASK_ID,
        "generator": str(path.relative_to(ROOT)),
        "generator_sha256": source_hash,
        "working_directory": str(Path.cwd()),
        "calls": {
            "default": default,
            "texture_warm": warm,
            "palette_kind_warm": palette_warm,
            "texture_no_objects": call(gen, overrides={"texture": "no_objects"}),
            "unknown_axis": call(gen, overrides={"unknown_axis": 1}),
            "fractional_n_objects": call(gen, overrides={"n_objects": 2.75}),
            "boolean_seed": call(gen, seed=True),
        },
        "observations": {
            "texture_warm_is_dead": default.get("grid_sha256") == warm.get("grid_sha256"),
            "palette_kind_warm_is_dead": default.get("grid_sha256") == palette_warm.get("grid_sha256"),
            "advertised_no_objects_is_self_invalid": bool(
                call(gen, overrides={"texture": "no_objects"}).get("self_check")
            ),
            "unknown_axis_accepted": call(gen, overrides={"unknown_axis": 1}).get("accepted"),
            "fractional_n_objects_accepted": call(gen, overrides={"n_objects": 2.75}).get("accepted"),
            "boolean_seed_accepted": call(gen, seed=True).get("accepted"),
        },
        "scope": "Generator call contract and declared-axis behavior only; no label claim.",
    }
    out = Path(__file__).with_name("contract_findings.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["observations"], indent=2, sort_keys=True))
    print(out)

if __name__ == "__main__":
    main()
