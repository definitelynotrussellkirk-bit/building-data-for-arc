"""Public-generator audit probes for the two assigned audit targets."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repo"
OUT = Path(__file__).resolve().parent


def load(task_id: str):
    path = ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module, path


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            comp = []
            while stack:
                rr, cc = stack.pop()
                if (rr, cc) in seen or grid[rr][cc] == 0:
                    continue
                seen.add((rr, cc))
                comp.append((rr, cc))
                for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr, nc = rr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w:
                        stack.append((nr,nc))
            result.append(comp)
    return result


def probe_873():
    task = "87388eaff4ce"
    gen, path = load(task)
    total = 1000
    ties = 0
    counts = Counter()
    dropped = 0
    validation_errors = 0
    for index in range(total):
        band = ("easy", "medium", "hard")[index % 3]
        grid = gen.generate(873_000 + index, index, difficulty=band)
        validation_errors += bool(gen.self_check(grid, difficulty=band))
        comps = components(grid)
        heights = []
        for comp in comps:
            rows = [r for r, _ in comp]
            heights.append(max(rows)-min(rows)+1)
        if len(set(heights)) != len(heights):
            ties += 1
        counts[len(comps)] += 1
        requested_min = 2 if band != "hard" else 3
        if len(comps) < requested_min:
            dropped += 1
    return {
        "task_id": task,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sample": {"seed_formula": "873000 + sample_index", "indices": [0, total-1], "difficulty_cycle": ["easy","medium","hard"]},
        "normal_samples": total,
        "samples_with_equal_bbox_heights": ties,
        "component_count_histogram": dict(sorted(counts.items())),
        "samples_below_documented_minimum_objects": dropped,
        "self_check_failures": validation_errors,
        "finding": "normal sampler draws distinct heights, so the authority's equal-height color tie-break has zero support",
    }


def section_zeros(grid, section):
    start = section*5
    return {(r, c) for r in range(4) for c in range(4) if grid[r][start+c] == 0}


def pattern_name(zeros):
    center = {(r,c) for r in (1,2) for c in (1,2)}
    bottom = {(r,c) for r in (2,3) for c in (1,2)}
    generated_edge = {(r,c) for r in range(4) for c in (0,3)}
    canonical_edge = {(r,c) for r in (1,2) for c in (0,3)}
    if not zeros: return "no_hole"
    if zeros == center: return "center_hole"
    if zeros == bottom: return "bottom_hole"
    if zeros == generated_edge: return "generated_full_edge_hole"
    if zeros == canonical_edge: return "canonical_middle_edge_hole"
    return "other"


def probe_71():
    task = "71e2e99645f4"
    gen, path = load(task)
    total = 1000
    patterns = Counter()
    validation_errors = 0
    for index in range(total):
        band = ("easy", "medium", "hard")[index % 3]
        grid = gen.generate(710_000 + index, index, difficulty=band)
        validation_errors += bool(gen.self_check(grid, difficulty=band))
        for section in range(3):
            patterns[pattern_name(section_zeros(grid, section))] += 1
    same_seed = 123
    same_index = 7
    center_override = gen.generate(same_seed, same_index, hole_patterns="center_hole")
    bottom_override = gen.generate(same_seed, same_index, hole_patterns="bottom_hole")
    return {
        "task_id": task,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sample": {"seed_formula": "710000 + sample_index", "indices": [0, total-1], "difficulty_cycle": ["easy","medium","hard"]},
        "normal_samples": total,
        "sections_examined": total*3,
        "section_pattern_histogram": dict(sorted(patterns.items())),
        "canonical_middle_edge_hole_count": patterns["canonical_middle_edge_hole"],
        "generated_full_edge_hole_count": patterns["generated_full_edge_hole"],
        "self_check_failures": validation_errors,
        "ignored_override_probe": {
            "seed": same_seed,
            "sample_index": same_index,
            "first": {"hole_patterns": "center_hole"},
            "second": {"hole_patterns": "bottom_hole"},
            "byte_identical": center_override == bottom_override,
            "grid_sha256": hashlib.sha256(json.dumps(center_override,separators=(",",":")).encode()).hexdigest(),
        },
        "finding": "normal edge sections always zero all eight edge-column cells; canonical edge sections zero only four middle-row edge cells",
    }


if __name__ == "__main__":
    reports = {"87388eaff4ce": probe_873(), "71e2e99645f4": probe_71()}
    for task, report in reports.items():
        path = OUT / task / "distribution_probe.json"
        path.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps(reports, indent=2, sort_keys=True))
