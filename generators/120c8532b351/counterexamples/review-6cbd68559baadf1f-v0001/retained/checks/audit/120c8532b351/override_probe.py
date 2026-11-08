#!/usr/bin/env python3
"""Small reproducer for 120c8532b351's advertised override contract."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

PACKET_ROOT = Path(__file__).resolve().parents[3]
REPO = PACKET_ROOT / "repo"
TASK = "120c8532b351"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load():
    path = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module, path


def attempt(fn):
    try:
        value = fn()
        return {"status": "returned", "value": value}
    except Exception as exc:
        return {"status": "raised", "exception": type(exc).__name__, "message": str(exc)}


def main():
    module, path = load()
    unknown = attempt(lambda: module.generate(0, 0, __override_contract_unknown_axis__=1))
    if unknown["status"] == "returned":
        grid = unknown.pop("value")
        unknown.update({"shape": [len(grid), len(grid[0])], "self_check": module.self_check(grid)})

    advertised_boundary = attempt(lambda: module.generate(0, 0, difficulty="medium", grid_h=5))
    all_unique = attempt(lambda: module.generate(0, 0, texture="all_unique"))

    palette = attempt(lambda: module.generate(
        0, 0, difficulty="medium", grid_h=4, grid_w=4, other_palette_size=6
    ))
    if palette["status"] == "returned":
        grid = palette.pop("value")
        counts = Counter(v for row in grid for v in row)
        minority = min(counts, key=counts.get)
        palette.update({
            "shape": [len(grid), len(grid[0])],
            "requested_other_palette_size": 6,
            "observed_nonminority_palette_size": len(set(counts) - {minority}),
            "counts": dict(sorted(counts.items())),
            "self_check": module.self_check(grid),
        })

    result = {
        "schema": "120c8532b351-override-audit-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "declared_axes": module.AXES,
        "cases": {
            "unknown_key_is_silently_accepted": unknown,
            "advertised_grid_h_5_is_rejected": advertised_boundary,
            "declared_all_unique_texture_crashes": all_unique,
            "other_palette_size_6_is_silently_clamped": palette,
        },
        "supported_gate_evidence": "checks/audit/120c8532b351/override/checks/120c8532b351_before_override.log",
    }
    out = Path(__file__).with_name("override_probe.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["cases"], indent=2))


if __name__ == "__main__":
    main()
