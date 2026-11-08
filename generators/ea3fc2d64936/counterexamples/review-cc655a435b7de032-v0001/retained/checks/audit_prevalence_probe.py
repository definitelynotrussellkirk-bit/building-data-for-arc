#!/usr/bin/env python3
"""Quantify the two assigned audit findings without modifying their generators."""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_prevalence_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_row(task_id: str):
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def normalized_masks(grid, force_origin=False):
    masks = []
    for cells in nonzero_components(grid):
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        mask = {(r - r0, c - c0) for r, c in cells}
        if force_origin:
            mask.add((0, 0))
        masks.append(mask)
    return masks


def overlay_output(grid, force_origin=False):
    masks = normalized_masks(grid, force_origin=force_origin)
    h = max(max(r for r, _ in mask) + 1 for mask in masks)
    w = max(max(c for _, c in mask) + 1 for mask in masks)
    counts = [[0] * w for _ in range(h)]
    for mask in masks:
        for r, c in mask:
            counts[r][c] += 1
    return [[0 if n == 0 else 2 if n == 1 else 3 if n == 2 else 4 if n == 3 else 6 for n in row] for row in counts]


def manhattan_rival(grid):
    start = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    goal = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
    direct = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                via = abs(start[0] - r) + abs(start[1] - c) + abs(goal[0] - r) + abs(goal[1] - c)
                if via == direct:
                    out[r][c] = 8
    return out


def probe_ea3():
    task_id = "ea3fc2d64936"
    module, source_hash = load_generator(task_id)
    row = canonical_row(task_id)
    pairs = list(row["train"]) + list(row["test"] if isinstance(row["test"], list) else [row["test"]])
    canonical_records = []
    for index, pair in enumerate(pairs):
        errors = module.self_check(pair["input"])
        originless = sum((0, 0) not in mask for mask in normalized_masks(pair["input"]))
        canonical_records.append({"index": index, "validator_errors": errors, "originless_components": originless})

    bands = ["easy", "medium", "hard"]
    seeds = range(50)
    sample_indices = range(3)
    generated = 0
    generated_validator_failures = 0
    all_masks_have_origin = 0
    forced_origin_rival_matches = 0
    unique_inputs = set()
    for band in bands:
        for seed in seeds:
            for sample_index in sample_indices:
                grid = module.generate(seed, sample_index, difficulty=band)
                generated += 1
                if module.self_check(grid):
                    generated_validator_failures += 1
                if all((0, 0) in mask for mask in normalized_masks(grid)):
                    all_masks_have_origin += 1
                if overlay_output(grid) == overlay_output(grid, force_origin=True):
                    forced_origin_rival_matches += 1
                unique_inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())

    collision_cases = {}
    controls = {
        "palette_kind": ("warm", "cool"),
        "palette_size": (3, 8),
        "n_distinct_colors": (3, 8),
        "texture": ("warm", "cool"),
    }
    for axis, values in controls.items():
        left = module.generate(2026, 7, difficulty="medium", **{axis: values[0]})
        right = module.generate(2026, 7, difficulty="medium", **{axis: values[1]})
        collision_cases[axis] = {"values": list(values), "identical_input": left == right}
    try:
        typo = module.generate(2026, 7, difficulty="medium", typo_axis="accepted")
        baseline = module.generate(2026, 7, difficulty="medium")
        unknown = {"accepted": True, "identical_to_baseline": typo == baseline}
    except Exception as exc:
        unknown = {"accepted": False, "exception": type(exc).__name__, "message": str(exc)}

    return {
        "task_id": task_id,
        "generator_sha256": source_hash,
        "canonical_sample": {
            "denominator": len(canonical_records),
            "validator_failures": sum(bool(record["validator_errors"]) for record in canonical_records),
            "pairs_with_originless_components": sum(record["originless_components"] > 0 for record in canonical_records),
            "records": canonical_records,
        },
        "generated_sample": {
            "bands": bands,
            "seed_start": 0,
            "seed_stop_exclusive": 50,
            "sample_indices": list(sample_indices),
            "denominator": generated,
            "unique_inputs": len(unique_inputs),
            "validator_failures": generated_validator_failures,
            "all_masks_have_origin": all_masks_have_origin,
            "forced_origin_rival_matches": forced_origin_rival_matches,
        },
        "override_collision_probe": {
            "seed": 2026,
            "sample_index": 7,
            "difficulty": "medium",
            "cases": collision_cases,
            "unknown_override": unknown,
        },
    }


def probe_50e():
    task_id = "50e0af791608"
    module, source_hash = load_generator(task_id)
    seed_start, seed_stop = 0, 1000
    starts = [0, 1, 2]
    sample_indices = list(range(6))
    profile_counts = Counter()
    total_draws = 0
    validator_failures = 0
    unique_inputs = set()
    windows = 0
    demo_fit_windows = 0
    shortcut_failures = []

    for seed in range(seed_start, seed_stop):
        records = {}
        for sample_index in sample_indices:
            grid = module.generate(seed, sample_index, difficulty="medium")
            actual = module.rule_mirror(grid)
            rival = manhattan_rival(grid)
            profile = module.observe_overrides(grid).get("scene_profile")
            profile_counts[profile] += 1
            total_draws += 1
            validator_failures += bool(module.self_check(grid))
            unique_inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            records[sample_index] = {"match": rival == actual, "profile": profile}
        for start in starts:
            windows += 1
            demo_matches = all(records[index]["match"] for index in range(start, start + 3))
            if demo_matches:
                demo_fit_windows += 1
            query_match = records[start + 3]["match"]
            if demo_matches and not query_match:
                shortcut_failures.append(
                    {
                        "seed": seed,
                        "start": start,
                        "demo_profiles": [records[index]["profile"] for index in range(start, start + 3)],
                        "query_profile": records[start + 3]["profile"],
                    }
                )

    return {
        "task_id": task_id,
        "generator_sha256": source_hash,
        "sample": {
            "difficulty": "medium",
            "seed_start": seed_start,
            "seed_stop_exclusive": seed_stop,
            "lesson_starts": starts,
            "sample_indices": sample_indices,
            "draw_records": total_draws,
            "unique_inputs": len(unique_inputs),
            "validator_failures": validator_failures,
            "lesson_windows": windows,
        },
        "profile_counts": dict(sorted(profile_counts.items())),
        "wall_ignorant_manhattan_rival": {
            "windows_fitting_all_three_demos": demo_fit_windows,
            "windows_where_query_refutes_after_three_fitting_demos": len(shortcut_failures),
            "first_20_counterexamples": shortcut_failures[:20],
        },
    }


if __name__ == "__main__":
    result = {
        "schema": "assigned_audit_prevalence/1",
        "ea3fc2d64936": probe_ea3(),
        "50e0af791608": probe_50e(),
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "checks" / "audit-prevalence.json").write_text(rendered, encoding="utf-8")
    print(rendered, end="")
