#!/usr/bin/env python3
"""Bounded, source-hash-bound audit probes for the two assigned read-only targets."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import pathlib
import sys
from collections import Counter
from typing import Any

PACKET_ROOT = pathlib.Path(__file__).resolve().parents[2]
REPO = PACKET_ROOT / "repo"
sys.path[:0] = [str(REPO / "shared" / "runtime"), str(REPO / "src")]


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def grid_hash(grid: Any) -> str:
    blob = json.dumps(grid, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def probe_legacy() -> dict[str, Any]:
    task_id = "1118c9143cae"
    module, path = load(task_id)

    def call(**overrides: Any) -> dict[str, Any]:
        try:
            grid = module.generate(73, 11, difficulty="easy", **overrides)
            nonzero = [value for row in grid for value in row if value != 0]
            return {
                "status": "returned",
                "shape": [len(grid), len(grid[0])],
                "nonzero_count": len(nonzero),
                "distinct_nonzero": sorted(set(nonzero)),
                "grid_sha256": grid_hash(grid),
                "self_check": module.self_check(grid, difficulty="easy"),
                "grid": grid,
            }
        except Exception as exc:  # audit records exact public behavior
            return {"status": "raised", "exception": type(exc).__name__, "message": str(exc)}

    palette = {name: call(palette_kind=name) for name in module.PALETTE_KINDS}
    texture = {name: call(texture=name) for name in module.HELPFUL_TEXTURES}
    center = call(texture="cell_at_center")
    unknown = call(typo_axis="accepted-by-baseline")
    dimensions = {
        "easy_grid_h_4": call(grid_h=4),
        "easy_grid_h_16": call(grid_h=16),
        "easy_grid_w_4": call(grid_w=4),
        "easy_grid_w_18": call(grid_w=18),
    }
    return {
        "task_id": task_id,
        "generator_sha256": sha256(path),
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
        "probe_seed": 73,
        "probe_sample_index": 11,
        "probe_difficulty": "easy",
        "findings": {
            "unknown_override": unknown,
            "advertised_dimension_boundaries": dimensions,
            "palette_kind_grid_hashes": {k: v.get("grid_sha256") for k, v in palette.items()},
            "helpful_texture_grid_hashes": {k: v.get("grid_sha256") for k, v in texture.items()},
            "cell_at_center": center,
        },
        "interpretation": {
            "unknown_override_rejected": unknown["status"] == "raised",
            "all_palette_kinds_observable": len({v.get("grid_sha256") for v in palette.values()}) == len(palette),
            "all_helpful_textures_observable": len({v.get("grid_sha256") for v in texture.values()}) == len(texture),
            "cell_at_center_rejected_by_self_check": bool(center.get("self_check")),
            "all_advertised_easy_boundaries_constructible": all(v["status"] == "returned" for v in dimensions.values()),
        },
    }


def probe_modern() -> dict[str, Any]:
    task_id = "53ffc8bc9584"
    module, path = load(task_id)
    override_failures: list[dict[str, Any]] = []
    override_cases = 0
    for band in ("easy", "medium", "hard"):
        values = itertools.product(range(7, 12), range(7, 12), (2, 3), module.SCENE_FAMILIES)
        for sample_index, (height, width, targets, family) in enumerate(values):
            override_cases += 1
            expected = {
                "grid_h": height,
                "grid_w": width,
                "n_targets": targets,
                "scene_family": family,
            }
            try:
                grid = module.generate(191, sample_index, difficulty=band, **expected)
                errors = module.self_check(grid, difficulty=band)
                observed = module.observe_overrides(grid)
                if errors or observed != expected:
                    override_failures.append(
                        {"difficulty": band, "expected": expected, "observed": observed, "errors": errors}
                    )
            except Exception as exc:
                override_failures.append(
                    {"difficulty": band, "expected": expected, "exception": f"{type(exc).__name__}: {exc}"}
                )

    lesson_failures: list[dict[str, Any]] = []
    survivor_counts: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    lesson_count = 0
    seed = 31337
    for band in ("easy", "medium", "hard"):
        for start in range(100):
            lesson_count += 1
            demos = []
            for sample_index in range(start, start + module.EXAMPLES_NEEDED):
                grid = module.generate(seed, sample_index, difficulty=band)
                unique_inputs.add(grid_hash(grid))
                demos.append({"input": grid, "output": module.rule_mirror(grid)})
            query_grid = module.generate(seed, start + module.EXAMPLES_NEEDED, difficulty=band)
            unique_inputs.add(grid_hash(query_grid))
            query = {"input": query_grid, "output": module.rule_mirror(query_grid)}
            reasons = module.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append({"difficulty": band, "start": start, "reasons": reasons})
            for name, rival in module.LESSON_COMPETITORS.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    survivor_counts[name] += 1

    invalid_overrides = {}
    for kwargs in (
        {"typo_axis": 1},
        {"grid_h": True},
        {"grid_h": 6},
        {"grid_w": 12},
        {"n_targets": 4},
        {"scene_family": "not-a-family"},
    ):
        key = json.dumps(kwargs, sort_keys=True)
        try:
            module.generate(0, 0, difficulty="easy", **kwargs)
            invalid_overrides[key] = "accepted"
        except Exception as exc:
            invalid_overrides[key] = f"{type(exc).__name__}: {exc}"

    return {
        "task_id": task_id,
        "generator_sha256": sha256(path),
        "declared_rule_hash": module.RULE_HASH,
        "override_cartesian": {
            "cases": override_cases,
            "difficulties": ["easy", "medium", "hard"],
            "domain": {"grid_h": "7..11", "grid_w": "7..11", "n_targets": [2, 3], "scene_family": list(module.SCENE_FAMILIES)},
            "failure_count": len(override_failures),
            "failures": override_failures[:20],
        },
        "lesson_probe": {
            "seed": seed,
            "starts_per_difficulty": 100,
            "lesson_count": lesson_count,
            "examples_per_lesson": module.EXAMPLES_NEEDED,
            "unique_inputs_including_queries": len(unique_inputs),
            "failure_count": len(lesson_failures),
            "failures": lesson_failures[:20],
            "competitor_survivor_counts": dict(survivor_counts),
            "competitors": sorted(module.LESSON_COMPETITORS),
        },
        "invalid_override_results": invalid_overrides,
    }


def main() -> None:
    result = {
        "schema": "arcpuzzles-readonly-audit-probe-v1",
        "command": ["python3", "checks/audit/audit_contract_probe.py"],
        "cwd": "packet_root",
        "targets": [probe_legacy(), probe_modern()],
    }
    output = PACKET_ROOT / "checks" / "audit" / "audit_contract_probe.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(output.relative_to(PACKET_ROOT)),
        "legacy_interpretation": result["targets"][0]["interpretation"],
        "modern_override_failures": result["targets"][1]["override_cartesian"]["failure_count"],
        "modern_lesson_failures": result["targets"][1]["lesson_probe"]["failure_count"],
        "modern_unique_inputs": result["targets"][1]["lesson_probe"]["unique_inputs_including_queries"],
    }, indent=2))


if __name__ == "__main__":
    main()
