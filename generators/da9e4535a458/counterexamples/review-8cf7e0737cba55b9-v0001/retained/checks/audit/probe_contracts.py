from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit"


def load(task_id: str):
    path = ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def largest_body_size(module, grid):
    comps = module._components(grid, ignore_row0=True)
    return max((len(c) for c in comps), default=0)


def main():
    # da9e4535a458: declared full-domain exact override rejected in easy band.
    da, da_path = load("da9e4535a458")
    da_case = {
        "difficulty": "easy",
        "seed": 0,
        "sample_index": 0,
        "overrides": {"grid_h": 14},
        "declared_axis": da.AXES["grid_h"],
    }
    try:
        da.generate(0, 0, difficulty="easy", grid_h=14)
        da_case["outcome"] = "unexpectedly accepted"
    except Exception as exc:
        da_case["outcome"] = "rejected"
        da_case["exception_type"] = type(exc).__name__
        da_case["exception"] = str(exc)
    da_report = {
        "schema": "arc-audit-contract-repro-v1",
        "task_id": "da9e4535a458",
        "generator_sha256": hashlib.sha256(da_path.read_bytes()).hexdigest(),
        "finding": "A value advertised as valid for grid_h is rejected in the easy band; no incompatibility declaration exists.",
        "case": da_case,
        "official_gate": {
            "command": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "check", "da9e4535a458", "--stage", "override", "--timeout", "600", "--phase", "after", "--out", "../checks/audit/da9e4535a458-override"],
            "cwd": "packet_root",
            "exit_code": 1,
            "evidence": "checks/audit/da9e4535a458-override/result.json",
        },
    }
    (OUT / "da9e4535a458" / "contract_repro.json").write_text(json.dumps(da_report, indent=2) + "\n")

    # 4f09f8bfa35a: exact axes are ignored and unknown keys are accepted.
    four, four_path = load("4f09f8bfa35a")
    base_seed = 0
    calls = []
    grids = {}
    for label, overrides in [
        ("request_one_command", {"n_commands": 1}),
        ("request_five_commands", {"n_commands": 5}),
        ("request_two_cells", {"shape_size": 2}),
        ("request_nine_cells", {"shape_size": 9}),
        ("unknown_key", {"unknown_axis": 7}),
    ]:
        grid = four.generate(base_seed, 0, **overrides)
        observed = {
            "n_commands": sum(v in (2, 3, 4, 5) for v in grid[0]),
            "shape_size": largest_body_size(four, grid),
            "self_check": four.self_check(grid),
        }
        calls.append({"label": label, "overrides": overrides, "observed": observed})
        grids[label] = grid
    four_report = {
        "schema": "arc-audit-contract-repro-v1",
        "task_id": "4f09f8bfa35a",
        "generator_sha256": hashlib.sha256(four_path.read_bytes()).hexdigest(),
        "finding": "n_commands and shape_size overrides are ignored, while an unknown override is silently accepted.",
        "seed": base_seed,
        "sample_index": 0,
        "declared_axes": {k: four.AXES[k] for k in ("n_commands", "shape_size")},
        "cases": calls,
        "same_grid_for_n_commands_1_and_5": grids["request_one_command"] == grids["request_five_commands"],
        "same_grid_for_shape_size_2_and_9": grids["request_two_cells"] == grids["request_nine_cells"],
        "input_grid_for_rule_check": grids["request_one_command"],
    }
    (OUT / "4f09f8bfa35a" / "contract_repro.json").write_text(json.dumps(four_report, indent=2) + "\n")
    (OUT / "4f09f8bfa35a" / "input.json").write_text(json.dumps(grids["request_one_command"], indent=2) + "\n")


if __name__ == "__main__":
    main()
