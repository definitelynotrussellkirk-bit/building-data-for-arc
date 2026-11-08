"""Independent oracle and audit tooling for ARC generator 33d2674e3094.

The Python implementation here is deliberately independent of ``generator.py``.
It is supplementary review evidence only; the selected Racket program remains
the label authority.  ``racket_outputs`` executes that program and never falls
back silently to this mirror.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[3]
TASK = "33d2674e3094"
sys.path.insert(0, str(ROOT / "shared/runtime"))

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
PROFILE_BY_SHAPE = {(8, 13): "p8x13", (9, 12): "p9x12", (10, 11): "p10x11"}
AREA_PATTERN_BY_SIZES = {
    (4, 4, 3): "tie_443",
    (6, 5, 3): "distinct_653",
    (6, 4, 3): "distinct_643",
}


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_33d2674e3094", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict[str, Any]:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(tests)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty row sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be non-empty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be integer ARC colors in 0..9")
    return len(grid), width


def objects(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    """Return monochrome cardinal components and their exact crops."""
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r0, c0 = current
                for dr, dc in CARDINAL:
                    nr, nc = r0 + dr, c0 + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            crop = [[0 for _ in range(c2 - c1 + 1)] for _ in range(r2 - r1 + 1)]
            for r, c in cells:
                crop[r - r1][c - c1] = color
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "area": len(cells),
                    "bbox": (r1, r2, c1, c2),
                    "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
                    "crop": crop,
                }
            )
    return result


def authority_key(obj: dict[str, Any]) -> tuple[int, int, int, int, int]:
    r1, r2, c1, c2 = obj["bbox"]
    return (-obj["area"], r1, r2, c1, c2)


def _gallery(crops: Sequence[Sequence[Sequence[int]]], *, bottom: bool = False) -> list[list[int]]:
    if not crops:
        return [[0]]
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    left = 0
    for crop in crops:
        top = height - len(crop) if bottom else 0
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                output[top + r][left + c] = value
        left += len(crop[0]) + 1
    return output


def _ordered_output(
    grid: Sequence[Sequence[int]],
    key: Callable[[dict[str, Any]], Any],
    *,
    bottom: bool = False,
) -> list[list[int]]:
    ordered = sorted(objects(grid), key=key)
    return _gallery([obj["crop"] for obj in ordered], bottom=bottom)


def rule_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Mirror: descending cell area, bbox tie-break, top-aligned gallery."""
    return _ordered_output(grid, authority_key)


def ascending_area_output(grid):
    return _ordered_output(
        grid,
        lambda obj: (obj["area"], *obj["bbox"]),
    )


def bbox_area_output(grid):
    return _ordered_output(
        grid,
        lambda obj: (-obj["bbox_area"], *obj["bbox"]),
    )


def scan_order_output(grid):
    """Wrong shortcut: ordinary row-major top-left discovery order."""
    def key(obj):
        r1, r2, c1, c2 = obj["bbox"]
        return (r1, c1, r2, c2)
    return _ordered_output(grid, key)


def color_order_output(grid):
    return _ordered_output(grid, lambda obj: (obj["color"], *obj["bbox"]))


def descending_color_order_output(grid):
    return _ordered_output(grid, lambda obj: (-obj["color"], *obj["bbox"]))


def tie_by_color_output(grid):
    return _ordered_output(
        grid,
        lambda obj: (-obj["area"], obj["color"], *obj["bbox"]),
    )


def bottom_aligned_output(grid):
    return _ordered_output(grid, authority_key, bottom=True)


RIVALS = {
    "ascending_area": ascending_area_output,
    "bbox_area": bbox_area_output,
    "scan_order": scan_order_output,
    "color_order": color_order_output,
    "descending_color_order": descending_color_order_output,
    "tie_by_color": tie_by_color_output,
    "bottom_aligned": bottom_aligned_output,
}


def observed(grid: Sequence[Sequence[int]]) -> dict[str, str]:
    height, width = _validate_grid(grid)
    sizes = tuple(sorted((obj["area"] for obj in objects(grid)), reverse=True))
    return {
        "profile": PROFILE_BY_SHAPE.get((height, width), "unknown"),
        "area_pattern": AREA_PATTERN_BY_SIZES.get(sizes, "unknown"),
    }


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the selected canonical Racket program over a batch."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids})
        )
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count: int) -> tuple[dict[str, Any], list[list[list[int]]]]:
    report: dict[str, Any] = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_matches": 0,
        "canonical_self_check_errors": [],
        "by_band": {},
    }
    canonical_rows = canonical_pairs()
    report["canonical_matches"] = sum(
        rule_output(pair["input"]) == pair["output"] for pair in canonical_rows
    )
    report["canonical_self_check_errors"] = [
        module.self_check(pair["input"]) for pair in canonical_rows
    ]
    parity_grids = [deepcopy(pair["input"]) for pair in canonical_rows]

    for band in ("easy", "medium", "hard"):
        counts = Counter()
        profiles = Counter()
        patterns = Counter()
        fingerprints: set[str] = set()
        for index in range(count):
            grid = module.generate(1000 + index, index, difficulty=band)
            counts["draws"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(
                1000 + index, index, difficulty=band
            )
            counts["changed"] += rule_output(grid) != grid
            stats = observed(grid)
            profiles[stats["profile"]] += 1
            patterns[stats["area_pattern"]] += 1
            fingerprints.add(
                hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            )
            for name, rival in RIVALS.items():
                counts[f"refutes_{name}"] += rival(grid) != rule_output(grid)
            if index < 12:
                parity_grids.append(deepcopy(grid))
        report["by_band"][band] = {
            **dict(counts),
            "profiles": dict(profiles),
            "area_patterns": dict(patterns),
            "distinct_inputs": len(fingerprints),
        }
    return report, parity_grids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, parity_grids = audit(module, args.count)
    source = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        report["canonical_matches"] != len(canonical_pairs())
        or any(report["canonical_self_check_errors"])
        or any(row.get("self_check_errors") for row in report["by_band"].values())
        or any(row.get("nondeterministic") for row in report["by_band"].values())
    )
    if args.racket:
        try:
            outputs = racket_outputs(parity_grids)
            mismatches = [
                index
                for index, (grid, output) in enumerate(zip(parity_grids, outputs))
                if rule_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"by_band": report["by_band"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
