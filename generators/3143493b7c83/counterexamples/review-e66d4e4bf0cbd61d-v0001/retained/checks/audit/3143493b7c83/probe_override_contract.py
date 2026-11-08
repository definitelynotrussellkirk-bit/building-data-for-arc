#!/usr/bin/env python3
"""Source-bound audit probe for 3143493b7c83 override validation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


def load_generator(repo_root: Path):
    source = repo_root / "generators/3143493b7c83/generator.py"
    spec = importlib.util.spec_from_file_location("audit_3143493b7c83_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def main() -> int:
    repo_root = Path.cwd()
    module, source = load_generator(repo_root)

    unknown_axis_error = None
    unknown_grid = None
    try:
        unknown_grid = module.generate(
            20261003,
            0,
            difficulty="medium",
            __override_contract_unknown_axis__=123,
        )
    except Exception as exc:  # pragma: no cover - evidence path
        unknown_axis_error = f"{type(exc).__name__}: {exc}"

    invalid_bool_error = None
    invalid_bool_grid = None
    invalid_bool_observed = None
    try:
        invalid_bool_grid = module.generate(
            20261003,
            1,
            difficulty="medium",
            corner_box="definitely-not-a-bool",
        )
        invalid_bool_observed = module.observe_overrides(invalid_bool_grid)
    except Exception as exc:  # pragma: no cover - evidence path
        invalid_bool_error = f"{type(exc).__name__}: {exc}"

    result = {
        "schema": "arcpuzzles-audit-override-probe-v1",
        "task_id": module.TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash_declared": module.RULE_HASH,
        "command": [
            "python3",
            "run_with_racket.py",
            "python3",
            "../checks/audit/3143493b7c83/probe_override_contract.py",
        ],
        "cwd": "packet_root",
        "unknown_axis_probe": {
            "axis": "__override_contract_unknown_axis__",
            "value": 123,
            "raised": unknown_axis_error is not None,
            "error": unknown_axis_error,
            "returned_grid": unknown_grid is not None,
            "self_check_errors": module.self_check(unknown_grid) if unknown_grid is not None else None,
        },
        "invalid_bool_probe": {
            "axis": "corner_box",
            "declared_type": module.AXES["corner_box"]["type"],
            "value": "definitely-not-a-bool",
            "raised": invalid_bool_error is not None,
            "error": invalid_bool_error,
            "returned_grid": invalid_bool_grid is not None,
            "observed": invalid_bool_observed,
            "self_check_errors": module.self_check(invalid_bool_grid) if invalid_bool_grid is not None else None,
        },
        "observe_overrides_keys": sorted(invalid_bool_observed or {}),
        "declared_axes": sorted(module.AXES),
        "decoy_mode_observable_via_observe_overrides": bool(
            invalid_bool_observed and "decoy_mode" in invalid_bool_observed
        ),
    }
    out = Path(__file__).with_name("manual_contract_probe.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
