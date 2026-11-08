#!/usr/bin/env python3
"""Source-bound census for rotational-orbit clipping and collisions.

This probe is deliberately independent of generator.self_check.  It can audit a
historical source file with ``--source`` and emits a replayable JSON report with
the exact source hash, seed schedule and per-band counts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "8c069ab108a1"
BANDS = ("easy", "medium", "hard")


def _rotations(delta_row: int, delta_col: int) -> tuple[tuple[int, int], ...]:
    result: list[tuple[int, int]] = []
    for _ in range(4):
        result.append((delta_row, delta_col))
        delta_row, delta_col = delta_col, -delta_row
    return tuple(result)


def analyze_grid(grid: list[list[int]]) -> dict[str, Any]:
    """Return source-independent orbit integrity measurements for one input."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {
            "anchor_count": 0,
            "seed_count": 0,
            "clipped_orbits": 0,
            "duplicate_orbits": 0,
            "cross_color_duplicate_orbits": 0,
            "clear_complete_orbits": False,
            "malformed": True,
        }
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {
            "anchor_count": 0,
            "seed_count": 0,
            "clipped_orbits": 0,
            "duplicate_orbits": 0,
            "cross_color_duplicate_orbits": 0,
            "clear_complete_orbits": False,
            "malformed": True,
        }

    height = len(grid)
    anchors = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    seeds = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]
    result: dict[str, Any] = {
        "anchor_count": len(anchors),
        "seed_count": len(seeds),
        "clipped_orbits": 0,
        "duplicate_orbits": 0,
        "cross_color_duplicate_orbits": 0,
        "clear_complete_orbits": False,
        "malformed": False,
    }
    if len(anchors) != 1:
        return result

    anchor_row, anchor_col = anchors[0]
    owners: dict[tuple[tuple[int, int], ...], int] = {}
    for row, col, color in seeds:
        orbit = tuple(
            (anchor_row + dr, anchor_col + dc)
            for dr, dc in _rotations(row - anchor_row, col - anchor_col)
        )
        if len(set(orbit)) != 4 or not all(
            0 <= out_row < height and 0 <= out_col < width
            for out_row, out_col in orbit
        ):
            result["clipped_orbits"] += 1
            continue
        key = tuple(sorted(orbit))
        if key in owners:
            result["duplicate_orbits"] += 1
            if owners[key] != color:
                result["cross_color_duplicate_orbits"] += 1
        else:
            owners[key] = color

    result["clear_complete_orbits"] = bool(seeds) and not (
        result["clipped_orbits"] or result["duplicate_orbits"]
    )
    return result


def _load_source(source: Path):
    spec = importlib.util.spec_from_file_location(
        f"orbit_probe_{hashlib.sha256(str(source).encode()).hexdigest()[:12]}",
        source,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "generate", None)):
        raise RuntimeError(f"{source} has no callable generate")
    return module


def run_census(
    source: Path,
    *,
    draws_per_band: int = 1000,
    seed_base: int = 830_000,
) -> dict[str, Any]:
    module = _load_source(source)
    report: dict[str, Any] = {
        "schema": "orbit-integrity-census-v1",
        "task_id": TASK_ID,
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "draws_per_band": draws_per_band,
        "seed_base": seed_base,
        "sampling": "generate(seed_base + band_offset + i, i, difficulty=band)",
        "bands": {},
    }
    for band_index, band in enumerate(BANDS):
        counts = {
            "draws": draws_per_band,
            "generated": 0,
            "generation_errors": 0,
            "grids_with_clipping": 0,
            "grids_with_duplicate_orbits": 0,
            "grids_with_cross_color_duplicate_orbits": 0,
            "clear_complete_orbits": 0,
            "total_clipped_orbits": 0,
            "total_duplicate_orbits": 0,
            "total_cross_color_duplicate_orbits": 0,
        }
        errors: list[dict[str, Any]] = []
        for index in range(draws_per_band):
            seed = seed_base + band_index * draws_per_band + index
            try:
                grid = module.generate(seed, index, difficulty=band)
                measurement = analyze_grid(grid)
            except Exception as exc:  # retained with replay seed
                counts["generation_errors"] += 1
                if len(errors) < 10:
                    errors.append(
                        {
                            "seed": seed,
                            "sample_index": index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                continue
            counts["generated"] += 1
            clipped = int(measurement["clipped_orbits"])
            duplicate = int(measurement["duplicate_orbits"])
            cross_color = int(measurement["cross_color_duplicate_orbits"])
            counts["total_clipped_orbits"] += clipped
            counts["total_duplicate_orbits"] += duplicate
            counts["total_cross_color_duplicate_orbits"] += cross_color
            counts["grids_with_clipping"] += int(clipped > 0)
            counts["grids_with_duplicate_orbits"] += int(duplicate > 0)
            counts["grids_with_cross_color_duplicate_orbits"] += int(cross_color > 0)
            counts["clear_complete_orbits"] += int(measurement["clear_complete_orbits"])
        counts["error_examples"] = errors
        report["bands"][band] = counts

    report["aggregate"] = {
        key: sum(int(report["bands"][band][key]) for band in BANDS)
        for key in (
            "draws",
            "generated",
            "generation_errors",
            "grids_with_clipping",
            "grids_with_duplicate_orbits",
            "grids_with_cross_color_duplicate_orbits",
            "clear_complete_orbits",
            "total_clipped_orbits",
            "total_duplicate_orbits",
            "total_cross_color_duplicate_orbits",
        )
    }
    return report


def main() -> int:
    here = Path(__file__).resolve()
    default_source = here.parents[1] / "generator.py"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=default_source)
    parser.add_argument("--draws-per-band", type=int, default=1000)
    parser.add_argument("--seed-base", type=int, default=830_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.draws_per_band < 1:
        parser.error("--draws-per-band must be positive")
    source = args.source.resolve()
    report = run_census(
        source,
        draws_per_band=args.draws_per_band,
        seed_base=args.seed_base,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["aggregate"]["generation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
