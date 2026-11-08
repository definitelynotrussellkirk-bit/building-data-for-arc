from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
GEN_PATH = ROOT / "generators/0a4310a68bdf/generator.py"
spec = importlib.util.spec_from_file_location("audit_0a4310a68bdf", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def summarize_grid(grid: list[list[int]]) -> dict[str, Any]:
    return {
        "height": len(grid),
        "width": len(grid[0]) if grid else None,
        "colors": sorted({v for row in grid for v in row}),
        "self_check": mod.self_check(grid),
        "grid": grid,
    }


def invoke(label: str, **kwargs: Any) -> dict[str, Any]:
    try:
        grid = mod.generate(20261012, 0, **kwargs)
        return {"label": label, "kwargs": kwargs, "status": "returned", **summarize_grid(grid)}
    except Exception as exc:  # Evidence captures the public failure surface.
        return {
            "label": label,
            "kwargs": kwargs,
            "status": "raised",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }

cases = [
    invoke("baseline_default"),
    invoke(
        "advertised_tiny_grid_ignores_exact_dimensions",
        grid_h=10,
        grid_w=10,
        palette_size=2,
        texture="tiny_grid",
    ),
    invoke(
        "advertised_monochrome_breaks_color_invariant",
        grid_h=4,
        grid_w=5,
        palette_size=2,
        texture="monochrome",
    ),
    invoke("advertised_grid_h_1_default", grid_h=1),
    invoke("advertised_grid_h_10_easy", difficulty="easy", grid_h=10),
    invoke("advertised_palette_10_default", palette_size=10),
    invoke("advertised_palette_2_hard", difficulty="hard", palette_size=2),
    invoke("unknown_override_is_silently_accepted", unknown_axis=123),
    invoke("unknown_difficulty_is_silently_treated_as_default", difficulty="impossible"),
    invoke("bg_density_above_advertised_range", bg_density=2.0),
    invoke("negative_noise_overlay", noise_overlay=-1.0),
]

# self_check is part of the public validator contract; capture malformed-input behavior.
validator_cases = []
for label, value in [
    ("empty", []),
    ("ragged", [[1, 2], [3]]),
    ("non_arc_color", [[10, 1], [2, 3]]),
    ("bool_cell", [[True, 1], [2, 3]]),
]:
    try:
        result = mod.self_check(value)
        validator_cases.append({"label": label, "status": "returned", "result": result})
    except Exception as exc:
        validator_cases.append(
            {
                "label": label,
                "status": "raised",
                "exception_type": type(exc).__name__,
                "exception": str(exc),
            }
        )

result = {
    "schema": "arc-audit-probe-v1",
    "task_id": mod.TASK_ID,
    "generator_version": mod.VERSION,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "axes": mod.AXES,
    "cases": cases,
    "validator_cases": validator_cases,
    "command": [
        "python3",
        "run_with_racket.py",
        "python3",
        "../checks/audit/0a4310a68bdf/probe.py",
    ],
    "effective_cwd": str(ROOT),
}
out = ROOT.parent / "checks/audit/0a4310a68bdf/probe.json"
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
