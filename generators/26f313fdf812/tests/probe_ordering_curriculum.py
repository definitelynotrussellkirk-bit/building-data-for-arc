#!/usr/bin/env python3
"""Source-bound probe for bbox-top-left versus row-scan ordering coverage."""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_26f313fdf812_order_probe", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _components_in_scan_order(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                current_row, current_col = current
                for row_delta, col_delta in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (current_row + row_delta, current_col + col_delta)
                    neighbor_row, neighbor_col = neighbor
                    if not (0 <= neighbor_row < height and 0 <= neighbor_col < width):
                        continue
                    if neighbor in seen or grid[neighbor_row][neighbor_col] != color:
                        continue
                    seen.add(neighbor)
                    queue.append(neighbor)
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            components.append(
                {
                    "color": color,
                    "size": len(cells),
                    "first_cell": min(cells),
                    "bbox_top_left": [min(rows), min(cols)],
                }
            )
    return components


def _matrix(values: list[int]) -> list[list[int]]:
    return [
        [1 if left == right else (2 if left > right else 3) for right in values]
        for left in values
    ]


def _scan_rival(grid: list[list[int]]) -> list[list[int]]:
    return _matrix([item["size"] for item in _components_in_scan_order(grid)])


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run(samples_per_profile: int) -> dict[str, Any]:
    generator = _load_generator()
    source_sha256 = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    profiles = [
        name
        for name, spec in generator._PROFILE_BY_NAME.items()
        if spec["same_row"]
    ]

    profile_results: dict[str, Any] = {}
    for profile in profiles:
        unique_inputs: set[str] = set()
        self_check_failures: list[dict[str, Any]] = []
        strict_failures: list[dict[str, Any]] = []
        rival_agreements: list[dict[str, Any]] = []
        first_witness: dict[str, Any] | None = None
        for offset in range(samples_per_profile):
            seed = 20261011 + offset
            sample_index = 7 * offset + 3
            grid = generator.generate(
                seed,
                sample_index,
                difficulty="medium",
                scene_profile=profile,
            )
            input_sha256 = _grid_sha256(grid)
            unique_inputs.add(input_sha256)
            self_errors = generator.self_check(grid)
            strict_errors = generator.strict_canonical_like(grid)
            official = generator.rule_mirror(grid)
            rival = _scan_rival(grid)
            if self_errors:
                self_check_failures.append(
                    {"seed": seed, "sample_index": sample_index, "errors": self_errors}
                )
            if strict_errors:
                strict_failures.append(
                    {"seed": seed, "sample_index": sample_index, "errors": strict_errors}
                )
            if official == rival:
                rival_agreements.append(
                    {"seed": seed, "sample_index": sample_index, "input_sha256": input_sha256}
                )
            elif first_witness is None:
                scan_components = _components_in_scan_order(grid)
                bbox_components = sorted(
                    scan_components,
                    key=lambda item: tuple(item["bbox_top_left"]),
                )
                first_witness = {
                    "seed": seed,
                    "sample_index": sample_index,
                    "input_sha256": input_sha256,
                    "input": grid,
                    "bbox_order": [
                        {
                            "color": item["color"],
                            "size": item["size"],
                            "bbox_top_left": item["bbox_top_left"],
                            "first_cell": list(item["first_cell"]),
                        }
                        for item in bbox_components
                    ],
                    "scan_order": [
                        {
                            "color": item["color"],
                            "size": item["size"],
                            "bbox_top_left": item["bbox_top_left"],
                            "first_cell": list(item["first_cell"]),
                        }
                        for item in scan_components
                    ],
                    "official_output": official,
                    "scan_rival_output": rival,
                }
        profile_results[profile] = {
            "samples": samples_per_profile,
            "unique_inputs": len(unique_inputs),
            "self_check_failures": self_check_failures,
            "strict_failures": strict_failures,
            "scan_rival_agreements": rival_agreements,
            "first_witness": first_witness,
        }

    production_windows: list[dict[str, Any]] = []
    rotated_windows: list[dict[str, Any]] = []
    for band, schedule in generator._PROFILES_BY_BAND.items():
        for start in range(len(schedule)):
            pairs = []
            profiles = []
            for offset in range(generator.EXAMPLES_NEEDED + 1):
                grid = generator.generate(41000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
                profiles.append(
                    generator.schedule_profile(41000 + start, start + offset, band)
                )

            for query_index, query in enumerate(pairs):
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                errors = generator.lesson_identifiable(demos, query)
                surviving_query_rivals = []
                for name, rival in generator.LESSON_COMPETITORS.items():
                    if rival(query["input"]) == query["output"]:
                        continue
                    if all(rival(pair["input"]) == pair["output"] for pair in demos):
                        surviving_query_rivals.append(name)
                row = {
                    "band": band,
                    "start": start,
                    "query_index": query_index,
                    "profiles": profiles,
                    "query_profile": profiles[query_index],
                    "errors": errors,
                    "surviving_query_rivals": surviving_query_rivals,
                }
                rotated_windows.append(row)
                if query_index == len(pairs) - 1:
                    production_windows.append(row)

    def _window_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        failures = [
            item
            for item in rows
            if item["errors"] or item["surviving_query_rivals"]
        ]
        return {
            "demonstrations_per_window": generator.EXAMPLES_NEEDED,
            "total": len(rows),
            "passed": len(rows) - len(failures),
            "failures": failures,
            "rows": rows,
        }

    return {
        "schema": "arcpuzzles-ordering-curriculum-probe-v2",
        "task_id": generator.TASK_ID,
        "version": generator.VERSION,
        "generator_sha256": source_sha256,
        "rule_hash": generator.RULE_HASH,
        "samples_per_profile": samples_per_profile,
        "profile_results": profile_results,
        "production_windows": _window_summary(production_windows),
        "rotated_windows": _window_summary(rotated_windows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples-per-profile", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.samples_per_profile < 1:
        parser.error("--samples-per-profile must be positive")
    report = run(args.samples_per_profile)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    failures = sum(
        len(row["self_check_failures"])
        + len(row["strict_failures"])
        + len(row["scan_rival_agreements"])
        for row in report["profile_results"].values()
    )
    failures += len(report["production_windows"]["failures"])
    failures += len(report["rotated_windows"]["failures"])
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": report["generator_sha256"],
        "profiles": len(report["profile_results"]),
        "profile_samples": len(report["profile_results"]) * args.samples_per_profile,
        "production_windows": report["production_windows"]["total"],
        "rotated_windows": report["rotated_windows"]["total"],
        "failures": failures,
    }, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
