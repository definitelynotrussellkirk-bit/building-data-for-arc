from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "3faff4c1f734"
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


def describe(module, overrides):
    grid = module.generate(314159, 7, difficulty="hard", **overrides)
    nonzero = [cell for row in grid for cell in row if cell != 0]
    return {
        "overrides": overrides,
        "shape": [len(grid), len(grid[0])],
        "row_markers_observed": sum(row[0] != 0 for row in grid[1:]),
        "col_markers_observed": sum(cell != 0 for cell in grid[0][1:]),
        "distinct_nonzero_colors_observed": len(set(nonzero)),
        "nonzero_colors": sorted(set(nonzero)),
        "sha256": digest(grid),
        "self_check": module.self_check(grid, difficulty="hard", meta=overrides),
        "grid": grid,
    }


def main():
    module = load_module()
    common = {
        "grid_h": 9,
        "grid_w": 10,
        "row_markers": 3,
        "col_markers": 3,
        "position_bias": "border_markers",
        "density": "sparse",
    }
    low = describe(module, {
        **common,
        "palette_kind": "warm",
        "texture": "warm",
        "palette_size": 2,
        "n_distinct_colors": 2,
    })
    high = describe(module, {
        **common,
        "palette_kind": "cool",
        "texture": "cool",
        "palette_size": 9,
        "n_distinct_colors": 9,
    })
    unknown = describe(module, {
        **common,
        "palette_kind": "warm",
        "texture": "warm",
        "palette_size": 2,
        "n_distinct_colors": 2,
        "__override_contract_unknown_axis__": 123,
    })
    payload = {
        "task_id": TASK_ID,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "finding": "advertised palette controls and unknown-key validation are inert",
        "observations": {
            "different_palette_contracts_emit_identical_grid": low["grid"] == high["grid"],
            "requested_two_colors_emits_six": low["distinct_nonzero_colors_observed"] == 6,
            "unknown_key_accepted_without_effect": low["grid"] == unknown["grid"],
            "self_check_accepts_contract_mismatch": not low["self_check"],
        },
        "cases": {
            "requested_two_warm_colors": low,
            "requested_nine_cool_colors": high,
            "unknown_key": unknown,
        },
        "override_lint": {
            "path": "checks/audit/3faff4c1f734/override/checks/3faff4c1f734_audit_override_results.json",
            "finding_count": 7637,
            "categories": {
                "override_mismatch": 4860,
                "generation_error": 2520,
                "grid_validity": 90,
                "other": 90,
                "axis_effect": 73,
                "axis_metadata": 2,
                "unknown_key": 1,
                "axis_provenance": 1,
            },
        },
        "retained_audit": "repo/generators/3faff4c1f734/evidence/review_index.json",
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(OUT),
        "observations": payload["observations"],
        "source_sha256": payload["source_sha256"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
