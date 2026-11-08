"""Independent oracle and diagnostics for ARC task 00b92ce63593.

This module is test support, not an alternate generator.  It intentionally
re-implements the public rule and the two strongest canonical-fitting rivals
without importing helpers from ``generator.py``.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "00b92ce63593"


def load_generator(path: str | os.PathLike[str] | None = None):
    candidate = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    candidate = candidate.resolve()
    spec = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", candidate)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the selected rule authority."""
    out = deepcopy(grid)
    if not out:
        return out
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            out[row][col] = 0 if value == 0 else header[col]
    return out


def only_color7(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: apply the column legend only to orange (7)."""
    out = deepcopy(grid)
    if not out:
        return out
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if value == 7:
                out[row][col] = header[col]
    return out


def keep_off_legend(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: recolor under legends but preserve other cells."""
    out = deepcopy(grid)
    if not out:
        return out
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if value != 0 and header[col] != 0:
                out[row][col] = header[col]
    return out


def erase_off_legend_non7_only(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting interaction shortcut: preserve orange off-legend cells."""
    out = deepcopy(grid)
    if not out:
        return out
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if value == 0:
                out[row][col] = 0
            elif header[col] != 0:
                out[row][col] = header[col]
            elif value != 7:
                out[row][col] = 0
    return out


def erase_off_legend_7_only(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting interaction shortcut: preserve non-orange off-legend cells."""
    out = deepcopy(grid)
    if not out:
        return out
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if value == 0:
                out[row][col] = 0
            elif header[col] != 0:
                out[row][col] = header[col]
            elif value == 7:
                out[row][col] = 0
    return out


RIVALS = {
    "only_color7": only_color7,
    "keep_off_legend": keep_off_legend,
    "erase_off_legend_non7_only": erase_off_legend_non7_only,
    "erase_off_legend_7_only": erase_off_legend_7_only,
}


def observed(grid: list[list[int]]) -> dict[str, Any]:
    height = len(grid)
    width = len(grid[0])
    legend_cols = [col for col, value in enumerate(grid[0]) if value != 0]
    legend = set(legend_cols)
    counts = [
        sum(grid[row][col] != 0 for row in range(1, height))
        for col in legend_cols
    ]
    if not counts or len(set(counts)) != 1:
        raise ValueError(f"legend body counts are not a single observable axis: {counts}")
    body_values = [
        grid[row][col]
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    unique = set(body_values)
    if unique == {7}:
        policy = "uniform7"
    elif len(unique) == 1 and 7 not in unique:
        policy = "uniform_other"
    elif len(unique) >= 2:
        policy = "mixed"
    else:
        raise ValueError("body color policy is not observable")
    return {
        "grid_h": height,
        "grid_w": width,
        "n_legend": len(legend_cols),
        "body_cells": counts[0],
        "body_colors": policy,
        "off_legend": sum(
            grid[row][col] != 0
            for row in range(1, height)
            for col in range(width)
            if col not in legend
        ),
    }


def audit(module, *, per_band: int = 100) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "00b92ce63593-independent-audit-v1",
        "task_id": TASK_ID,
        "version": getattr(module, "VERSION", None),
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "canonical": {},
        "per_band": {},
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "oracle_matches": sum(rule_output(pair["input"]) == pair["output"] for pair in pairs),
        "rival_fits": {
            name: sum(rival(pair["input"]) == pair["output"] for pair in pairs)
            for name, rival in RIVALS.items()
        },
    }
    for band in (None, "easy", "medium", "hard"):
        inputs: set[str] = set()
        profiles: dict[str, int] = {}
        rival_disagreements = {name: 0 for name in RIVALS}
        self_check_errors = 0
        nondeterministic = 0
        for index in range(per_band):
            seed = 9100 + index
            grid = module.generate(seed, index, difficulty=band)
            self_check_errors += bool(module.self_check(deepcopy(grid)))
            nondeterministic += grid != module.generate(seed, index, difficulty=band)
            truth = rule_output(grid)
            for name, rival in RIVALS.items():
                rival_disagreements[name] += rival(grid) != truth
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            inputs.add(digest)
            profile = str(module.schedule_profile(seed, index, band))
            profiles[profile] = profiles.get(profile, 0) + 1
        report["per_band"][str(band)] = {
            "samples": per_band,
            "distinct_inputs": len(inputs),
            "profiles": profiles,
            "self_check_errors": self_check_errors,
            "nondeterministic": nondeterministic,
            "rival_disagreements": rival_disagreements,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    module = load_generator(args.generator)
    result = audit(module, per_band=args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
