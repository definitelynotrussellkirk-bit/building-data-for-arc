from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK = "22d736100571"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("audit_22d736100571", GEN_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def call(**kwargs):
    try:
        grid = GEN.generate(0, 0, **kwargs)
    except Exception as exc:
        return {
            "status": "raised",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }
    return {
        "status": "returned",
        "shape": [len(grid), len(grid[0]) if grid else 0],
        "self_check": GEN.self_check(grid),
        "grid": grid,
    }

cases = {
    "declared_grid_h_rejected_in_easy_band": {
        "kwargs": {"difficulty": "easy", "grid_h": 4},
    },
    "declared_n_spans_rejected_in_easy_band": {
        "kwargs": {"difficulty": "easy", "n_spans": 1},
    },
    "degenerate_texture_ignores_exact_dimensions": {
        "kwargs": {
            "difficulty": "easy",
            "texture": "no_gap",
            "grid_h": 20,
            "grid_w": 22,
        },
    },
    "declared_no_spans_texture_violates_self_check": {
        "kwargs": {"difficulty": "easy", "texture": "no_spans"},
    },
    "unknown_override_is_silently_accepted": {
        "kwargs": {"difficulty": "easy", "__override_contract_unknown_axis__": 1},
    },
}
for case in cases.values():
    case["outcome"] = call(**case["kwargs"])

out_dir = Path(__file__).resolve().parent
no_gap_grid = cases["degenerate_texture_ignores_exact_dimensions"]["outcome"]["grid"]
(out_dir / "no-gap-input.json").write_text(json.dumps(no_gap_grid, indent=2) + "\n")

report = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "finding_id": "A22-override-contract",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "reviewed_rule_hash": "8557e6e9275d",
    "seed": 0,
    "sample_index": 0,
    "command": {
        "cwd": "WORK",
        "argv": [
            "PYTHONPATH=repo/shared/runtime",
            "python3",
            "checks/audit/22d736100571/repro.py",
        ],
    },
    "cases": cases,
    "notes": [
        "AXES advertises grid_h 4..20, grid_w 5..22, and n_spans 1..8, but difficulty-specific draw ranges reject legal exact values.",
        "The degenerate texture fast path bypasses dimensions and returns a fixed 9x10 grid.",
        "The no_spans texture returns a blank grid that fails the generator's own self_check.",
        "An unknown override key is accepted, so misspelled controls can appear successful.",
    ],
}
(out_dir / "repro.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2))
