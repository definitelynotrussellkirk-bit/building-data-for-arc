#!/usr/bin/env python3
"""Independent semantic oracle and distribution probe for e5dc3d423bd9.

This module deliberately does not import generator.py.  It recognizes exact
same-color hollow rectangular frames, applies the selected rule, and implements
the canonical-fitting wrong rule that marks *every* frame at its floor center.
Future reviews can also run it as a source-bound census of a candidate generator.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "e5dc3d423bd9"
BANDS = (None, "easy", "medium", "hard")


def _rectangular_grid(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
    )


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return nonzero same-color 4-connected components in row-major order."""
    if not _rectangular_grid(grid):
        raise ValueError("expected a nonempty rectangular grid")
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr + 1, cc), (rr - 1, cc), (rr, cc + 1), (rr, cc - 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            out.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rs), min(cs), max(rs), max(cs)),
                }
            )
    return out


def _frame_from_component(component: dict[str, Any]) -> dict[str, Any] | None:
    r1, c1, r2, c2 = component["bbox"]
    height, width = r2 - r1 + 1, c2 - c1 + 1
    if height < 3 or width < 3:
        return None
    perimeter = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    if set(component["cells"]) != perimeter:
        return None
    return {
        **component,
        "height": height,
        "width": width,
        "odd": height % 2 == 1 and width % 2 == 1,
        "center_floor": ((r1 + r2) // 2, (c1 + c2) // 2),
    }


def frames(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return exact hollow rectangular frame components only."""
    return [frame for component in components(grid) if (frame := _frame_from_component(component))]


def oracle(grid: list[list[int]]) -> list[list[int]]:
    """Selected rule: mark the exact center of odd-by-odd hollow frames."""
    out = [list(row) for row in grid]
    for frame in frames(grid):
        if frame["odd"]:
            r, c = frame["center_floor"]
            out[r][c] = frame["color"]
    return out


def mark_every_frame_floor_center(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule that fits all canonical pairs but mishandles even frames."""
    out = [list(row) for row in grid]
    for frame in frames(grid):
        r, c = frame["center_floor"]
        out[r][c] = frame["color"]
    return out


def grid_facts(grid: list[list[int]]) -> dict[str, Any]:
    found = frames(grid)
    colors = [frame["color"] for frame in found]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(found),
        "n_odd": sum(frame["odd"] for frame in found),
        "n_even": sum(not frame["odd"] for frame in found),
        "distinct_colors": len(colors) == len(set(colors)),
        "frame_dims": sorted((frame["height"], frame["width"]) for frame in found),
    }


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("generator_under_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def census(generator_path: Path, *, draws_per_band: int = 100, seed_base: int = 730_000) -> dict[str, Any]:
    """Probe self-check, shortcut disagreement, observability, and uniqueness."""
    gen = _load_generator(generator_path)
    source_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "generator": str(generator_path),
        "generator_sha256": source_sha,
        "draws_per_band": draws_per_band,
        "bands": {},
    }
    for band_index, band in enumerate(BANDS):
        unique: set[str] = set()
        failures: list[dict[str, Any]] = []
        n_even = n_odd = disagreements = replay_matches = 0
        for index in range(draws_per_band):
            seed = seed_base + band_index * 100_000 + index
            sample_index = index * 17 + 5
            grid = gen.generate(seed, sample_index, difficulty=band)
            facts = grid_facts(grid)
            n_even += facts["n_even"]
            n_odd += facts["n_odd"]
            unique.add(json.dumps(grid, separators=(",", ":")))
            truth = oracle(grid)
            rival = mark_every_frame_floor_center(grid)
            disagreements += truth != rival
            findings = list(gen.self_check(copy.deepcopy(grid)))
            observed = gen.observe_overrides(copy.deepcopy(grid)) if hasattr(gen, "observe_overrides") else None
            replay = gen.generate(seed, sample_index, difficulty=band, **observed) if observed else None
            replay_matches += replay == grid
            if findings or facts["n_even"] != 1 or not facts["distinct_colors"] or truth == rival:
                failures.append(
                    {
                        "index": index,
                        "seed": seed,
                        "facts": facts,
                        "self_check": findings,
                        "truth_equals_rival": truth == rival,
                    }
                )
        report["bands"][str(band)] = {
            "draws": draws_per_band,
            "unique_inputs": len(unique),
            "odd_frames": n_odd,
            "even_frames": n_even,
            "oracle_rival_disagreements": disagreements,
            "override_replay_matches": replay_matches,
            "failures": failures[:10],
            "failure_count": len(failures),
        }
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generator.py",
    )
    parser.add_argument("--draws-per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=730_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = census(args.generator.resolve(), draws_per_band=args.draws_per_band, seed_base=args.seed_base)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if all(not band["failure_count"] for band in result["bands"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
