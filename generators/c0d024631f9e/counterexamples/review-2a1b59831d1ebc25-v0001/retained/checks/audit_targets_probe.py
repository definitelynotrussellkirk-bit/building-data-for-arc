#!/usr/bin/env python3
"""Reproduce the two adversarial audit findings drawn for this review packet."""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
TARGETS = ("cd8b5598bb80", "c0d024631f9e")


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical(task_id: str) -> dict:
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(task_id)


def normalize(grid):
    return [[int(v) for v in row] for row in grid] if grid and isinstance(grid[0], str) else grid


def components(grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(cells)
    return found


def orientation(cells: list[tuple[int, int]]) -> str:
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    if len(rows) == 1:
        return "horizontal"
    if len(cols) == 1:
        return "vertical"
    return "other"


def audit_segments() -> dict:
    module, path = load_generator("cd8b5598bb80")
    bands = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        mixed = wrong_size = non_cyan_distractor = 0
        component_sizes: collections.Counter[int] = collections.Counter()
        for index in range(100):
            grid = module.generate(41000 + band_index * 1000 + index, index, difficulty=band)
            comps = components(grid, 8)
            kinds = {orientation(comp) for comp in comps}
            mixed += len(kinds) > 1
            wrong_size += any(len(comp) != 4 for comp in comps)
            non_cyan_distractor += any(value not in (0, 8) for row in grid for value in row)
            component_sizes.update(len(comp) for comp in comps)
        bands[band] = {
            "draws": 100,
            "mixed_orientation_grids": mixed,
            "grids_with_non_length4_cyan_component": wrong_size,
            "grids_with_non_cyan_distractor": non_cyan_distractor,
            "component_size_histogram": dict(sorted(component_sizes.items())),
        }

    malformed = [[0] * 8 for _ in range(8)]
    for col in range(2, 5):
        malformed[2][col] = 8

    row = canonical("cd8b5598bb80")
    pairs = list(row["train"]) + (row["test"] if isinstance(row["test"], list) else [row["test"]])
    canonical_profiles = []
    for index, pair in enumerate(pairs):
        grid = normalize(pair["input"])
        comps = components(grid, 8)
        canonical_profiles.append(
            {
                "pair_index": index,
                "cyan_components": [
                    {"size": len(comp), "orientation": orientation(comp)} for comp in comps
                ],
                "non_0_8_colors": sorted({v for line in grid for v in line if v not in (0, 8)}),
            }
        )
    return {
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sampled_bands": bands,
        "length3_counterexample_self_check_findings": module.self_check(malformed),
        "canonical_profiles": canonical_profiles,
        "finding": (
            "Default data contains only isolated length-4 cyan segments, one orientation per grid, "
            "and no distractor colors; canonical pairs include mixed target orientations, non-target "
            "cyan components, and other colors. self_check accepts a length-3 cyan component."
        ),
    }


def audit_rank3() -> dict:
    module, path = load_generator("c0d024631f9e")
    identical = []
    for index in range(20):
        seed = 52000 + index
        random_pick = module.generate(seed, index, difficulty="medium", third_color_pick="random")
        specific_pick = module.generate(seed, index, difficulty="medium", third_color_pick="specific")
        identical.append(random_pick == specific_pick)

    placement_results = {}
    for pattern in ("random", "clustered", "striped", "quadrants", "banded"):
        accepted = 0
        errors: collections.Counter[str] = collections.Counter()
        for index in range(20):
            try:
                grid = module.generate(
                    53000 + index,
                    index,
                    difficulty="medium",
                    placement_pattern=pattern,
                )
                findings = module.self_check(grid)
                if findings:
                    errors[f"self_check: {findings[0]}"] += 1
                else:
                    accepted += 1
            except Exception as exc:
                errors[f"{type(exc).__name__}: {exc}"] += 1
        placement_results[pattern] = {
            "attempts": 20,
            "accepted": accepted,
            "errors": dict(errors),
        }
    return {
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "third_color_pick_identical_draws": sum(identical),
        "third_color_pick_draws": len(identical),
        "placement_pattern_results": placement_results,
        "finding": (
            "third_color_pick is a dead advertised axis, and four of five advertised placement_pattern "
            "values are rejected because generate eagerly calls draw_choice with only ['random']."
        ),
    }


def main() -> int:
    payload = {
        "schema": "arc-adversarial-audit-probe-v1",
        "targets": {
            "cd8b5598bb80": audit_segments(),
            "c0d024631f9e": audit_rank3(),
        },
    }
    output = ROOT / "checks/audit_targets_probe.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({task: data["finding"] for task, data in payload["targets"].items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
