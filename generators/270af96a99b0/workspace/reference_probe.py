#!/usr/bin/env python3
"""Independent geometry oracle and audit tool for ARC task 270af96a99b0.

The production generator supplies inputs only.  This module independently
extracts colored components, computes true exposed-edge perimeter, applies the
canonical source-position tie-break, and packs normalized crops left-to-right.
It is test tooling, not an alternate label authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Callable

TASK_ID = "270af96a99b0"
PROFILE_BY_PERIMETERS = {
    (8, 8, 10, 12): "p8_tie",
    (4, 10, 10, 12): "p10_tie",
    (6, 12, 12, 14): "p12_tie",
}


@dataclass(frozen=True)
class Object:
    cells: tuple[tuple[int, int], ...]
    color: int
    r1: int
    c1: int
    r2: int
    c2: int

    @property
    def area(self) -> int:
        return len(self.cells)

    @property
    def height(self) -> int:
        return self.r2 - self.r1 + 1

    @property
    def width(self) -> int:
        return self.c2 - self.c1 + 1

    @property
    def perimeter(self) -> int:
        occupied = set(self.cells)
        return sum(
            (r + dr, c + dc) not in occupied
            for r, c in self.cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or Path(__file__).resolve().parents[1] / "generator.py")
    spec = importlib.util.spec_from_file_location("reviewed_generator_270af96a99b0", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _shape(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def components(grid: Any) -> list[Object]:
    """Return same-color 4-connected objects in source row-major order."""
    height, width = _shape(grid)
    seen: set[tuple[int, int]] = set()
    result: list[Object] = []
    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append(
                Object(
                    tuple(sorted(cells)),
                    color,
                    min(rows),
                    min(cols),
                    max(rows),
                    max(cols),
                )
            )
    return result


def _pack(objects: list[Object], *, gap: int = 1, alignment: str = "top", fill_bbox: bool = False) -> list[list[int]]:
    if not objects:
        return []
    out_h = max(obj.height for obj in objects)
    out_w = sum(obj.width for obj in objects) + gap * (len(objects) - 1)
    output = [[0 for _ in range(out_w)] for _ in range(out_h)]
    left = 0
    for obj in objects:
        top = 0 if alignment == "top" else out_h - obj.height
        if fill_bbox:
            for r in range(obj.height):
                for c in range(obj.width):
                    output[top + r][left + c] = obj.color
        else:
            for r, c in obj.cells:
                output[top + r - obj.r1][left + c - obj.c1] = obj.color
        left += obj.width + gap
    return output


def solve(grid: Any) -> list[list[int]]:
    ordered = sorted(components(grid), key=lambda obj: (obj.perimeter, obj.r1, obj.c1))
    return _pack(ordered)


def rival(grid: Any, name: str) -> list[list[int]]:
    objects = components(grid)
    if name == "source_order":
        ordered = objects
    elif name == "area_then_position":
        ordered = sorted(objects, key=lambda obj: (obj.area, obj.r1, obj.c1))
    elif name == "bbox_perimeter_then_position":
        ordered = sorted(objects, key=lambda obj: (2 * (obj.height + obj.width), obj.r1, obj.c1))
    elif name == "color_order":
        ordered = sorted(objects, key=lambda obj: obj.color)
    elif name == "descending_perimeter":
        ordered = sorted(objects, key=lambda obj: (obj.perimeter, obj.r1, obj.c1), reverse=True)
    elif name == "bottom_aligned":
        ordered = sorted(objects, key=lambda obj: (obj.perimeter, obj.r1, obj.c1))
        return _pack(ordered, alignment="bottom")
    elif name == "no_gap":
        ordered = sorted(objects, key=lambda obj: (obj.perimeter, obj.r1, obj.c1))
        return _pack(ordered, gap=0)
    elif name == "fill_bbox":
        ordered = sorted(objects, key=lambda obj: (obj.perimeter, obj.r1, obj.c1))
        return _pack(ordered, fill_bbox=True)
    else:
        raise ValueError(f"unknown rival {name!r}")
    return _pack(ordered)


RIVALS = (
    "source_order",
    "area_then_position",
    "bbox_perimeter_then_position",
    "color_order",
    "descending_perimeter",
    "bottom_aligned",
    "no_gap",
    "fill_bbox",
)


def observed(grid: Any) -> dict[str, int | str]:
    height, width = _shape(grid)
    objects = components(grid)
    colors = {obj.color for obj in objects}
    if colors and max(colors) <= 5:
        palette_kind = "low"
    elif colors and min(colors) >= 5:
        palette_kind = "high"
    elif colors and min(colors) <= 4 and max(colors) >= 6:
        palette_kind = "mixed"
    else:
        raise ValueError(f"cannot classify palette {sorted(colors)}")
    signature = tuple(sorted(obj.perimeter for obj in objects))
    try:
        profile = PROFILE_BY_PERIMETERS[signature]
    except KeyError as exc:
        raise ValueError(f"unknown perimeter profile {signature}") from exc
    return {
        "grid_h": height,
        "grid_w": width,
        "palette_kind": palette_kind,
        "shape_profile": profile,
    }


def audit(module, count: int) -> dict[str, Any]:
    counts = Counter()
    per_band: dict[str, Any] = {}
    for band in (None, "easy", "medium", "hard"):
        profiles: set[str] = set()
        shapes: set[tuple[int, int]] = set()
        hashes: set[str] = set()
        local = Counter()
        for index in range(count):
            grid = module.generate(270000 + index, index, difficulty=band)
            local["samples"] += 1
            local["self_check_errors"] += bool(module.self_check(grid))
            local["nondeterministic"] += grid != module.generate(270000 + index, index, difficulty=band)
            obs = observed(grid)
            profiles.add(str(obs["shape_profile"]))
            shapes.add((len(grid), len(grid[0])))
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            expected = solve(grid)
            for name in RIVALS:
                local[f"rival_{name}_disagreements"] += rival(grid, name) != expected
        local["distinct_inputs"] = len(hashes)
        local["distinct_shapes"] = len(shapes)
        per_band[str(band)] = dict(local, profiles=sorted(profiles))
        counts.update(local)
    return {
        "schema": "270af96a99b0-independent-audit-v1",
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "counts": dict(counts),
        "by_band": per_band,
        "warning": "The Python oracle is supplementary evidence; Racket remains authoritative.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    source = args.generator or Path(__file__).resolve().parents[1] / "generator.py"
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(report["counts"].get("self_check_errors", 0) > 0 or report["counts"].get("nondeterministic", 0) > 0)


if __name__ == "__main__":
    raise SystemExit(main())
