#!/usr/bin/env python3
"""Reproducible source-bound census for the two assigned audit targets."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path[:0] = [str(REPO / "shared" / "runtime"), str(REPO / "src")]

BANDS = ("easy", "medium", "hard")
SAMPLES_PER_BAND = 400
CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_canonical(task_id: str) -> dict[str, Any]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def component_count(cells: set[tuple[int, int]]) -> int:
    unseen = set(cells)
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in CARD:
                nb = (r + dr, c + dc)
                if nb in unseen:
                    unseen.remove(nb)
                    stack.append(nb)
    return count


def color_components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
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
                for dr, dc in CARD:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def crop_flip(cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    cell_set = set(cells)
    r0 = min(r for r, _ in cell_set)
    r1 = max(r for r, _ in cell_set)
    c0 = min(c for _, c in cell_set)
    c1 = max(c for _, c in cell_set)
    return [
        [color if (r, c) in cell_set else 0 for c in range(c1, c0 - 1, -1)]
        for r in range(r0, r1 + 1)
    ]


def largest_component_rule(grid: list[list[int]]) -> list[list[int]]:
    components = color_components(grid)
    if not components:
        return [[0]]
    color, cells = min(
        components,
        key=lambda item: (
            -len(item[1]),
            min(r for r, _ in item[1]),
            min(c for _, c in item[1]),
        ),
    )
    return crop_flip(cells, color)


def global_color_count_rival(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return [[0]]
    color = min(counts, key=lambda value: (-counts[value], value))
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    return crop_flip(cells, color)


def audit_boolean_gallery() -> dict[str, Any]:
    task_id = "1b46e014e17c"
    gen = load_generator(task_id)
    canonical = load_canonical(task_id)
    by_band: dict[str, Any] = {}
    all_connected = 0
    total_templates = 0
    generated_inputs = 0
    for band_index, band in enumerate(BANDS):
        band_inputs = 0
        band_templates = 0
        band_connected = 0
        for index in range(SAMPLES_PER_BAND):
            seed = 1_460_000 + band_index * 100_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            analysis = gen._analyze(grid)
            assert not analysis["errors"], analysis["errors"]
            band_inputs += 1
            for frame in analysis["frames"]:
                band_templates += 1
                if component_count(set(frame["support"])) == 1:
                    band_connected += 1
        generated_inputs += band_inputs
        total_templates += band_templates
        all_connected += band_connected
        by_band[band] = {
            "seed_start": 1_460_000 + band_index * 100_000,
            "sample_index_range": [0, SAMPLES_PER_BAND - 1],
            "inputs": band_inputs,
            "templates": band_templates,
            "connected_templates": band_connected,
        }

    canonical_pairs = list(canonical["train"]) + list(canonical["test"])
    canonical_connected = 0
    canonical_rule_match = 0
    for pair in canonical_pairs:
        analysis = gen._analyze(pair["input"])
        assert not analysis["errors"], analysis["errors"]
        if all(component_count(set(frame["support"])) == 1 for frame in analysis["frames"]):
            canonical_connected += 1
        if gen.rule_mirror(pair["input"]) == pair["output"]:
            canonical_rule_match += 1

    counter_input = json.loads((ROOT / "checks/audit/1b46e014e17c/input.json").read_text())
    rival_output = json.loads((ROOT / "checks/audit/1b46e014e17c/rival_output.json").read_text())
    racket = json.loads((ROOT / "checks/audit/1b46e014e17c/racket.json").read_text())
    actual = racket["results"][0]["output"]
    analysis = gen._analyze(counter_input)
    return {
        "task_id": task_id,
        "generator_sha256": sha256(REPO / "generators" / task_id / "generator.py"),
        "rule_hash": racket["executed_rule_hash"],
        "sample_policy": {
            "bands": list(BANDS),
            "samples_per_band": SAMPLES_PER_BAND,
            "seed_formula": "1460000 + band_index*100000 + sample_index",
        },
        "generated_census": {
            "inputs": generated_inputs,
            "templates": total_templates,
            "connected_templates": all_connected,
            "by_band": by_band,
        },
        "canonical_census": {
            "pairs": len(canonical_pairs),
            "pairs_with_both_templates_connected": canonical_connected,
            "python_mirror_matches_outputs": canonical_rule_match,
        },
        "counterexample": {
            "validator_errors": gen.self_check(counter_input),
            "documented_domain": True,
            "left_template_components": component_count(set(analysis["frames"][0]["support"])),
            "right_template_components": component_count(set(analysis["frames"][1]["support"])),
            "actual_racket_output": actual,
            "largest_component_only_rival_output": rival_output,
            "disagrees": actual != rival_output,
            "input_sha256": racket["results"][0]["input_sha256"],
            "output_sha256": racket["results"][0]["output_sha256"],
        },
    }


def audit_largest_object() -> dict[str, Any]:
    task_id = "2d585b947291"
    gen = load_generator(task_id)
    canonical = load_canonical(task_id)
    by_band: dict[str, Any] = {}
    total_inputs = 0
    one_component_per_color = 0
    rival_matches = 0
    for band_index, band in enumerate(BANDS):
        band_inputs = 0
        band_one = 0
        band_match = 0
        for index in range(SAMPLES_PER_BAND):
            seed = 2_585_000 + band_index * 100_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            components = color_components(grid)
            colors = {value for row in grid for value in row if value != 0}
            comp_colors = Counter(color for color, _ in components)
            if all(comp_colors[color] == 1 for color in colors):
                band_one += 1
            if largest_component_rule(grid) == global_color_count_rival(grid):
                band_match += 1
            band_inputs += 1
        total_inputs += band_inputs
        one_component_per_color += band_one
        rival_matches += band_match
        by_band[band] = {
            "seed_start": 2_585_000 + band_index * 100_000,
            "sample_index_range": [0, SAMPLES_PER_BAND - 1],
            "inputs": band_inputs,
            "one_component_per_color": band_one,
            "global_color_count_rival_matches": band_match,
        }

    canonical_pairs = list(canonical["train"]) + list(canonical["test"])
    canonical_rival_match = sum(
        global_color_count_rival(pair["input"]) == pair["output"]
        for pair in canonical_pairs
    )
    canonical_rule_match = sum(
        largest_component_rule(pair["input"]) == pair["output"]
        for pair in canonical_pairs
    )

    counter_input = json.loads((ROOT / "checks/audit/2d585b947291/input.json").read_text())
    rival_output = json.loads((ROOT / "checks/audit/2d585b947291/rival_output.json").read_text())
    racket = json.loads((ROOT / "checks/audit/2d585b947291/racket.json").read_text())
    actual = racket["results"][0]["output"]
    components = color_components(counter_input)
    color_component_counts = Counter(color for color, _ in components)
    return {
        "task_id": task_id,
        "generator_sha256": sha256(REPO / "generators" / task_id / "generator.py"),
        "rule_hash": racket["executed_rule_hash"],
        "sample_policy": {
            "bands": list(BANDS),
            "samples_per_band": SAMPLES_PER_BAND,
            "seed_formula": "2585000 + band_index*100000 + sample_index",
        },
        "generated_census": {
            "inputs": total_inputs,
            "one_component_per_color": one_component_per_color,
            "global_color_count_rival_matches": rival_matches,
            "by_band": by_band,
        },
        "canonical_census": {
            "pairs": len(canonical_pairs),
            "independent_largest_component_rule_matches_outputs": canonical_rule_match,
            "global_color_count_rival_matches_outputs": canonical_rival_match,
        },
        "counterexample": {
            "validator_errors": gen.self_check(counter_input),
            "documented_ordinary_domain": False,
            "validator_domain": True,
            "reason_outside_ordinary_domain": "color 2 is split across two objects, while ordinary generation assigns a distinct color to each object",
            "component_counts_by_color": dict(sorted(color_component_counts.items())),
            "actual_racket_output": actual,
            "global_color_count_rival_output": rival_output,
            "disagrees": actual != rival_output,
            "input_sha256": racket["results"][0]["input_sha256"],
            "output_sha256": racket["results"][0]["output_sha256"],
        },
    }


def main() -> None:
    result = {
        "schema": "arcpuzzles-assigned-audit-analysis-v1",
        "command": ["python3", "checks/audit/analyze.py"],
        "cwd": str(ROOT),
        "findings": [audit_boolean_gallery(), audit_largest_object()],
    }
    out = ROOT / "checks" / "audit" / "analysis.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        finding["task_id"]: {
            "generator_sha256": finding["generator_sha256"],
            "generated_census": finding["generated_census"],
            "canonical_census": finding["canonical_census"],
            "counterexample_disagrees": finding["counterexample"]["disagrees"],
        }
        for finding in result["findings"]
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
