#!/usr/bin/env python3
"""Source-bound shortcut and curriculum probe for task 0f801939eff6.

The probe is intentionally independent of ``generator.rule_mirror`` for its
component, color-frequency, and position-tiebreak calculations.  By default it
also evaluates the three retained witnesses through the selected canonical
Racket authority.  Run from a review packet with::

    python3 review.py run python3 generators/0f801939eff6/workspace/shortcut_probe.py \
        --samples-per-band 100 --out ../checks/final-shortcut-probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import json
from pathlib import Path
import sys
import types
from typing import Any


def _bootstrap_reviewer_support() -> None:
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        helper = parent / "shared" / "runtime" / "reviewer_support.py"
        if helper.is_file():
            sys.path.insert(0, str(helper.parent))
            return
        helper = parent / "reviewer_support.py"
        if helper.is_file():
            sys.path.insert(0, str(parent))
            return


_bootstrap_reviewer_support()
from reviewer_support import canonical_pairs, find_root, load_selected_generator  # noqa: E402


TASK_ID = "0f801939eff6"


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append(
                {
                    "color": color,
                    "size": len(cells),
                    "anchor": min(cells),
                    "cells": sorted(cells),
                }
            )
    return found


def component_rule(grid: list[list[int]]) -> list[list[int]]:
    ordered = sorted(components(grid), key=lambda item: (-item["size"], item["color"]))
    row = [item["color"] for item in ordered for _ in range(item["size"])]
    return [row or [0]]


def color_frequency_rule(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value != 0)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    row = [color for color, count in ordered for _ in range(count)]
    return [row or [0]]


def position_tiebreak_rule(grid: list[list[int]]) -> list[list[int]]:
    ordered = sorted(components(grid), key=lambda item: (-item["size"], item["anchor"]))
    row = [item["color"] for item in ordered for _ in range(item["size"])]
    return [row or [0]]


def handcrafted_counterexample() -> list[list[int]]:
    grid = [[0] * 10 for _ in range(7)]
    for row, col in ((0, 0), (0, 1), (1, 0), (1, 1)):
        grid[row][col] = 2
    for row, col in ((3, 3), (3, 4), (3, 5)):
        grid[row][col] = 3
    grid[6][9] = 2
    return grid


def _ensure_scripts_namespace(root: Path) -> None:
    """Expose repository ``shared/tools`` under its runtime name ``scripts``."""
    try:
        __import__("scripts.comment_solutions")
        return
    except ModuleNotFoundError as exc:
        if exc.name not in {"scripts", "scripts.comment_solutions"}:
            raise
    candidates = (root / "shared" / "tools", root / "tools")
    tools = next((candidate for candidate in candidates if candidate.is_dir()), None)
    if tools is None:
        raise FileNotFoundError("cannot locate shared tools for scripts namespace")
    package = sys.modules.get("scripts")
    if package is None:
        package = types.ModuleType("scripts")
        package.__path__ = [str(tools)]
        sys.modules["scripts"] = package
    else:
        paths = list(getattr(package, "__path__", []))
        if str(tools) not in paths:
            paths.append(str(tools))
            package.__path__ = paths
    __import__("scripts.comment_solutions")


def _canonical_rule_source(root: Path) -> str:
    path = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    if not path.is_file():
        path = root / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(f"canonical rule source missing for {TASK_ID}")


def _authoritative_outputs(root: Path, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    _ensure_scripts_namespace(root)
    from puzzle_generators import runner

    callable_text = runner.wrap_rule(_canonical_rule_source(root))
    bridge, fn_name = runner._open_bridge_with_rule(callable_text)
    try:
        return [runner._apply_rule(bridge, fn_name, grid) for grid in grids]
    finally:
        shutdown = getattr(bridge, "shutdown", None)
        if callable(shutdown):
            shutdown()
        else:
            close = getattr(bridge, "close", None)
            if callable(close):
                close()


def _witness_record(grid: list[list[int]], rival, authority=None) -> dict[str, Any]:
    intended = component_rule(grid)
    shortcut = rival(grid)
    return {
        "input": grid,
        "components": [
            {"color": item["color"], "size": item["size"], "anchor": item["anchor"]}
            for item in components(grid)
        ],
        "component_rule_output": intended,
        "shortcut_output": shortcut,
        "shortcut_refuted": intended != shortcut,
        "authoritative_output": authority,
        "authority_matches_component_rule": None if authority is None else authority == intended,
    }


def build_report(*, samples_per_band: int = 100, include_authority: bool = True) -> dict[str, Any]:
    if type(samples_per_band) is not int or samples_per_band < 1:
        raise ValueError("samples_per_band must be a positive literal integer")
    root = find_root(__file__)
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    pairs = canonical_pairs(TASK_ID, root=root)

    old_grid = handcrafted_counterexample()
    repeated_grid = gen.generate(
        4242, 1, difficulty="medium", grid_h=9, grid_w=12,
        scene_profile="repeated_distinct",
    )
    tie_grid = gen.generate(
        4243, 2, difficulty="medium", grid_h=9, grid_w=12,
        scene_profile="unique_tie",
    )
    grids = [old_grid, repeated_grid, tie_grid]
    authoritative = _authoritative_outputs(root, grids) if include_authority else [None] * 3

    profile_counts: Counter[str] = Counter()
    generated = color_refuted = position_refuted = invalid = 0
    examples: dict[str, dict[str, Any]] = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(samples_per_band):
            sample_index = index
            grid = gen.generate(9300 + 101 * band_index + index, sample_index, difficulty=band)
            findings = gen.self_check(grid)
            invalid += bool(findings)
            generated += 1
            profile = gen.observe_overrides(grid).get("scene_profile")
            profile_counts[str(profile)] += 1
            if component_rule(grid) != color_frequency_rule(grid):
                color_refuted += 1
                examples.setdefault("color_frequency", {"band": band, "sample_index": sample_index, "input": grid})
            if component_rule(grid) != position_tiebreak_rule(grid):
                position_refuted += 1
                examples.setdefault("position_tiebreak", {"band": band, "sample_index": sample_index, "input": grid})

    canonical_frequency_hits = sum(
        color_frequency_rule(pair["input"]) == pair["output"] for pair in pairs
    )
    canonical_position_hits = sum(
        position_tiebreak_rule(pair["input"]) == pair["output"] for pair in pairs
    )
    return {
        "schema": "area-sorted-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_pairs": len(pairs),
        "canonical_shortcut_fit": {
            "color_frequency_aggregate": f"{canonical_frequency_hits}/{len(pairs)}",
            "position_tiebreak": f"{canonical_position_hits}/{len(pairs)}",
        },
        "handcrafted_counterexample": _witness_record(
            old_grid, color_frequency_rule, authoritative[0]
        ),
        "generated_witnesses": {
            "disconnected_same_color": _witness_record(
                repeated_grid, color_frequency_rule, authoritative[1]
            ),
            "equal_area_color_tiebreak": _witness_record(
                tie_grid, position_tiebreak_rule, authoritative[2]
            ),
        },
        "census": {
            "samples_per_band": samples_per_band,
            "generated": generated,
            "self_check_failures": invalid,
            "profile_counts": dict(sorted(profile_counts.items())),
            "color_frequency_refuted": color_refuted,
            "position_tiebreak_refuted": position_refuted,
            "first_examples": examples,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=100)
    parser.add_argument("--no-authority", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = build_report(
        samples_per_band=args.samples_per_band,
        include_authority=not args.no_authority,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(payload, end="")
    else:
        if args.out.exists():
            raise FileExistsError(f"refusing to overwrite {args.out}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
