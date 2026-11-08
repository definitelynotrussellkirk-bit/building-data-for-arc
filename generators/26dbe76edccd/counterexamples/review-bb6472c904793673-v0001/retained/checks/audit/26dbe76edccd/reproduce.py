#!/usr/bin/env python3
"""Minimal source-bound reproduction of 26dbe76edccd's override defects."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "26dbe76edccd"


def packet_root() -> Path:
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        candidate = parent / "repo" / "generators" / TASK_ID / "generator.py"
        if candidate.is_file():
            return parent
    raise RuntimeError("could not locate return root containing repo/generators")


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shape(grid):
    return [len(grid), len(grid[0])]


def colors(grid):
    return sorted({value for row in grid for value in row if value not in (0, 5)})


def main() -> int:
    root = packet_root()
    source = root / "repo" / "generators" / TASK_ID / "generator.py"
    module = load_generator(source)
    seed, sample_index = 17, 0
    base = module.generate(seed, sample_index)

    ignored = {}
    for name, override in {
        "palette_kind_warm": {"palette_kind": "warm"},
        "palette_kind_cool": {"palette_kind": "cool"},
        "n_distinct_colors_1": {"n_distinct_colors": 1},
        "palette_size_1": {"palette_size": 1},
        "unknown_key": {"bogus_axis": 1},
    }.items():
        grid = module.generate(seed, sample_index, **override)
        ignored[name] = {
            "override": override,
            "same_as_base": grid == base,
            "shape": shape(grid),
            "non_marker_colors": colors(grid),
        }

    rejected = {}
    for name, override in {
        "grid_h_min": {"grid_h": 4},
        "grid_h_max": {"grid_h": 14},
        "grid_w_min": {"grid_w": 5},
        "grid_w_max": {"grid_w": 18},
        "seeds_max": {"seeds": 10},
    }.items():
        try:
            module.generate(seed, sample_index, **override)
        except Exception as exc:  # exact public symptom retained below
            rejected[name] = {
                "override": override,
                "exception": type(exc).__name__,
                "message": str(exc),
            }
        else:
            rejected[name] = {"override": override, "exception": None}

    degenerate = module.generate(seed, sample_index, texture="no_seeds")
    report = {
        "schema": "arcpuzzles-audit-reproduction-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_version": getattr(module, "VERSION", None),
        "seed": seed,
        "sample_index": sample_index,
        "base": {"shape": shape(base), "non_marker_colors": colors(base)},
        "ignored_overrides": ignored,
        "declared_boundaries_rejected": rejected,
        "degenerate_texture": {
            "override": {"texture": "no_seeds"},
            "shape": shape(degenerate),
            "self_check_errors": module.self_check(degenerate),
        },
        "reproduced": (
            all(item["same_as_base"] for item in ignored.values())
            and all(item["exception"] == "ValueError" for item in rejected.values())
            and bool(module.self_check(degenerate))
        ),
        "domain_note": (
            "Every override above is advertised by AXES except bogus_axis, which "
            "should fail closed. The no_seeds texture is also advertised but emits "
            "a grid rejected by the generator's own self_check."
        ),
    }
    output = Path(__file__).with_name("finding.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
