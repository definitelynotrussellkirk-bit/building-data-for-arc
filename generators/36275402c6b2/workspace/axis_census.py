"""Reproduce the independent 14,400-grid exact-axis review census.

Run with the shared runtime on the caller's PYTHONPATH, for example:
    PYTHONPATH=/path/to/runtime python /path/to/workspace/axis_census.py

No runtime or repository roots are inferred. The default source is the
generator.py beside this workspace; --source-path selects another candidate.
Only bounded failures include grids. The complete result is printed as JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys


SEED = 98173
DIFFICULTY = "hard"
SAMPLE_INDICES = (0, 1)
DOMAINS = {
    "grid_h": list(range(11, 16)),
    "grid_w": list(range(11, 16)),
    "rect_h": list(range(4, 8)),
    "rect_w": list(range(4, 8)),
    "frame_color": list(range(1, 10)),
    "pair_count": list(range(2, 4)),
}
MAX_REPORTED_ERRORS = 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-path", type=Path,
        default=Path(__file__).resolve().parent.parent / "generator.py",
        help="Candidate generator.py; runtime imports must already be available.",
    )
    parser.add_argument(
        "--expected-rule-hash", help="Optionally verify the generator RULE_HASH.",
    )
    args = parser.parse_args()
    source = args.source_path.resolve()
    result = {
        "source_path": str(source),
        "source_sha256": None,
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "sample_indices": list(SAMPLE_INDICES),
        "dimension_domains": DOMAINS,
        "joint_axis_combinations": 7200,
        "expected_grid_count": 14400,
        "attempted_grid_count": 0,
        "passed_grid_count": 0,
        "per_parity": {
            str(index): {
                "sample_index": index,
                "attempted": 0,
                "passed": 0,
                "errors": 0,
                "border_source_count_expected": index,
                "side_legend_required": bool(index),
            }
            for index in SAMPLE_INDICES
        },
        "error_count": 0,
        "errors": [],
    }

    def record_error(detail):
        result["error_count"] += 1
        if len(result["errors"]) < MAX_REPORTED_ERRORS:
            result["errors"].append(detail)

    try:
        result["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        spec = importlib.util.spec_from_file_location("axis_census_candidate", source)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import candidate source: {source}")
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        result["rule_hash"] = getattr(generator, "RULE_HASH", None)
        if args.expected_rule_hash is not None:
            result["expected_rule_hash"] = args.expected_rule_hash
            if result["rule_hash"] != args.expected_rule_hash:
                record_error({"stage": "metadata", "message": "RULE_HASH mismatch"})
    except Exception as exc:
        record_error({"stage": "load", "exception": type(exc).__name__, "message": str(exc)})
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    axes = list(DOMAINS)
    for values in itertools.product(*(DOMAINS[axis] for axis in axes)):
        requested = dict(zip(axes, values))
        for parity in SAMPLE_INDICES:
            stats = result["per_parity"][str(parity)]
            stats["attempted"] += 1
            result["attempted_grid_count"] += 1
            grid = None
            try:
                grid = generator.generate(
                    SEED, parity, difficulty=DIFFICULTY, **requested,
                )
                observed = generator.observe_overrides(grid)
                if observed != requested:
                    raise ValueError(f"Exact controls disagree: observed {observed!r}")
                analysis = generator._analysis_or_raise(grid)
                border_sources = sum(
                    value in analysis["sources"]
                    and (row in (0, values[2] - 1) or col in (0, values[3] - 1))
                    for row, crop_row in enumerate(analysis["crop"])
                    for col, value in enumerate(crop_row)
                )
                if border_sources != parity:
                    raise ValueError(
                        f"Expected {parity} border sources, observed {border_sources}"
                    )
                if parity and not any(
                    analysis["bbox"][0] <= row <= analysis["bbox"][2]
                    for _, _, row, _ in analysis["pairs"]
                ):
                    raise ValueError("Required crop-row side legend is absent")
            except Exception as exc:
                stats["errors"] += 1
                detail = {
                    "stage": "grid", "sample_index": parity,
                    "overrides": requested,
                    "exception": type(exc).__name__, "message": str(exc),
                }
                if len(result["errors"]) < MAX_REPORTED_ERRORS and grid is not None:
                    detail["grid"] = grid
                record_error(detail)
            else:
                stats["passed"] += 1
                result["passed_grid_count"] += 1

    result["reported_error_limit"] = MAX_REPORTED_ERRORS
    result["omitted_error_count"] = max(0, result["error_count"] - len(result["errors"]))
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(result["error_count"] != 0)


if __name__ == "__main__":
    sys.exit(main())
