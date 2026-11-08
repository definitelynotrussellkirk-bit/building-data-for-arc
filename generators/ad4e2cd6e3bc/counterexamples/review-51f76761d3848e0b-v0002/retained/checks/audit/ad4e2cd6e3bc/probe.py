"""Bounded findings-only probe. Writes only this task's audit directory."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "ad4e2cd6e3bc"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
SOURCE = REPO / "generators" / TASK / "generator.py"


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def local_neighbor_rival(grid):
    """Fill black cells with an orthogonal passable neighbor; ignore seed location."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 and any(
                0 <= nr < h and 0 <= nc < w and grid[nr][nc] in (0, 2)
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            ):
                out[r][c] = 8
    return out


def main():
    spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    canonical = next(
        row for row in map(json.loads, (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
        if row.get("task_id") == TASK
    )
    rule = canonical["program_solution"]
    cases = []
    for profile in mod.SCENE_PROFILES:
        grid = mod.generate(17, 23, difficulty="medium", scene_profile=profile)
        analysis = mod._analysis(grid)
        cases.append({
            "case_id": profile,
            "origin": "unmodified generated sample",
            "seed": 17,
            "sample_index": 23,
            "difficulty": "medium",
            "overrides": {"scene_profile": profile},
            "input": grid,
            "validator_result": mod.self_check(grid),
            "observed_overrides": mod.observe_overrides(grid),
            "seed_region_size": len(analysis["seed_region"]),
            "unreachable_component_sizes": sorted(map(len, analysis["unreachable_components"])),
            "rival_output": local_neighbor_rival(grid),
        })
    frontier = [[int(c) for c in row] for row in (
        "55555555", "55550055", "55555555", "52000005",
        "50000005", "50000005", "55555555",
    )]
    analysis = mod._analysis(frontier)
    cases.append({
        "case_id": "two_cell_unreachable_frontier",
        "origin": "constructed validator-domain frontier; not a generated sample",
        "seed": None,
        "sample_index": None,
        "difficulty": None,
        "overrides": None,
        "input": frontier,
        "validator_result": mod.self_check(frontier),
        "observed_overrides": mod.observe_overrides(frontier),
        "seed_region_size": len(analysis["seed_region"]),
        "unreachable_component_sizes": sorted(map(len, analysis["unreachable_components"])),
        "rival_output": local_neighbor_rival(frontier),
    })
    write("input.json", {"inputs": [case["input"] for case in cases]})
    write("cases.json", cases)
    write("provenance.json", {
        "task_id": TASK,
        "generator_path": str(SOURCE),
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "generator_version": mod.VERSION,
        "canonical_path": str(REPO / "shared/data/canonical/puzzles.jsonl"),
        "rule_sha256_exact": hashlib.sha256(rule.encode()).hexdigest(),
        "rule_sha256_normalized": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
        "generator_rule_hash": mod.RULE_HASH,
        "canonical_program": rule,
        "canonical_pair_count": len(canonical["train"] + canonical["test"]),
        "source_unchanged_by_probe": True,
    })
    print(json.dumps({"generated_cases": len(cases)-1, "frontiers": 1,
                      "validator_failures": sum(bool(case["validator_result"]) for case in cases)}))


if __name__ == "__main__":
    main()
