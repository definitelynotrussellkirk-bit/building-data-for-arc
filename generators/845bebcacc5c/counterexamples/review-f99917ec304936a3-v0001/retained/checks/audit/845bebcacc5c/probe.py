from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "845bebcacc5c"
SOURCE = Path("generators") / TASK_ID / "generator.py"
OUT = Path("../checks/audit") / TASK_ID / "reproduction.json"


def load_module():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(grid):
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(raw).hexdigest()


def call(module, **overrides):
    grid = module.generate(314159, 7, difficulty="medium", **overrides)
    return {
        "overrides": overrides,
        "shape": [len(grid), len(grid[0])],
        "blue_count": sum(cell == 1 for row in grid for cell in row),
        "sha256": digest(grid),
        "self_check": module.self_check(grid, difficulty="medium", meta=overrides),
        "grid": grid,
    }


def capture_error(module, *, difficulty, **overrides):
    try:
        grid = module.generate(314159, 7, difficulty=difficulty, **overrides)
    except Exception as exc:  # evidence capture
        return {
            "accepted": False,
            "difficulty": difficulty,
            "overrides": overrides,
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    return {
        "accepted": True,
        "difficulty": difficulty,
        "overrides": overrides,
        "shape": [len(grid), len(grid[0])],
        "sha256": digest(grid),
    }


def main():
    module = load_module()
    common = {
        "grid_h": 7,
        "grid_w": 10,
        "dot_count": 4,
        "palette_size": 1,
        "position_bias": "scattered",
        "n_distinct_colors": 1,
        "density": "sparse",
    }
    default = call(module, **common, palette_kind="default", texture="default")
    alternate = call(module, **common, palette_kind="warm", texture="cool")
    unknown = call(
        module,
        **common,
        palette_kind="default",
        texture="default",
        __override_contract_unknown_axis__=123,
    )
    declared_but_band_rejected = capture_error(
        module,
        difficulty="easy",
        grid_h=12,
        grid_w=14,
        dot_count=10,
    )
    payload = {
        "task_id": TASK_ID,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "finding": "advertised override contract is not exact",
        "observations": {
            "ignored_palette_and_texture": default["grid"] == alternate["grid"],
            "unknown_key_accepted_without_effect": default["grid"] == unknown["grid"],
            "declared_full_domain_rejected_by_easy_band": not declared_but_band_rejected["accepted"],
        },
        "cases": {
            "default": default,
            "alternate_palette_texture": alternate,
            "unknown_key": unknown,
            "declared_full_domain_easy": declared_but_band_rejected,
        },
        "override_lint": {
            "path": "checks/audit/845bebcacc5c/override/checks/845bebcacc5c_audit_override_results.json",
            "finding_count": 9710,
            "categories": {
                "override_mismatch": 4860,
                "self_check": 3330,
                "generation_error": 1500,
                "axis_effect": 16,
                "axis_metadata": 2,
                "unknown_key": 1,
                "axis_provenance": 1,
            },
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(OUT),
        "observations": payload["observations"],
        "source_sha256": payload["source_sha256"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
