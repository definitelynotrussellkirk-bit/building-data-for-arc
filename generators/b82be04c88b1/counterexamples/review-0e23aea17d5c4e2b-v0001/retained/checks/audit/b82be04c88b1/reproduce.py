from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "b82be04c88b1"
HERE = Path(__file__).resolve().parent
ROOT = find_root(Path(__file__).resolve().parents[3] / "repo")
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_hash(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blue_components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    }
    out = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        out.append(component)
    return out


def main() -> None:
    generator = load_generator()
    total = 0
    disconnected = 0
    first = None
    by_band = {}
    for difficulty in ("easy", "medium", "hard"):
        band_total = 0
        band_disconnected = 0
        for seed in range(200):
            for sample_index in range(4):
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                components = blue_components(grid)
                total += 1
                band_total += 1
                if len(components) != 1:
                    disconnected += 1
                    band_disconnected += 1
                    if first is None:
                        first = {
                            "difficulty": difficulty,
                            "seed": seed,
                            "sample_index": sample_index,
                            "grid": grid,
                            "component_sizes": sorted((len(c) for c in components), reverse=True),
                            "validator_errors": generator.self_check(grid),
                        }
        by_band[difficulty] = {
            "total": band_total,
            "disconnected": band_disconnected,
        }

    assert first is not None
    assert not first["validator_errors"]
    (HERE / "input.json").write_text(json.dumps(first["grid"], indent=2) + "\n")

    seed = 123
    sample_index = 7
    difficulty = "medium"
    baseline = generator.generate(seed, sample_index, difficulty=difficulty)
    override_cases = []
    for overrides in (
        {"grid_h": 8},
        {"grid_w": 16},
        {"blob_n": 14},
        {"n_missing": 4},
        {"__audit_unknown_axis__": 1},
    ):
        observed = generator.generate(seed, sample_index, difficulty=difficulty, **overrides)
        override_cases.append(
            {
                "overrides": overrides,
                "byte_identical_to_baseline": observed == baseline,
                "observed_h": len(observed),
                "observed_w": len(observed[0]),
                "observed_sha256": grid_hash(observed),
            }
        )

    report = {
        "schema": "arcpuzzles-audit-reproduction-v1",
        "task_id": TASK_ID,
        "classification": "emitted_domain_and_validator_contract_defect",
        "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": sha256_file(GENERATOR_PATH),
        "command": "PYTHONPATH=src:shared/runtime python3 ../checks/audit/b82be04c88b1/reproduce.py",
        "cwd": str(ROOT),
        "sample": {
            "difficulties": ["easy", "medium", "hard"],
            "seed_range": [0, 199],
            "sample_index_range": [0, 3],
            "total": total,
            "disconnected": disconnected,
            "by_band": by_band,
        },
        "first_counterexample": {
            "difficulty": first["difficulty"],
            "seed": first["seed"],
            "sample_index": first["sample_index"],
            "component_sizes": first["component_sizes"],
            "passes_target_validator": not bool(first["validator_errors"]),
            "target_validator_errors": first["validator_errors"],
            "input_path": "checks/audit/b82be04c88b1/input.json",
        },
        "validator_blind_spots": {
            "single_blue_errors": generator.self_check([[1]]),
            "empty_scene_errors": generator.self_check([[0]]),
        },
        "ignored_override_probe": {
            "difficulty": difficulty,
            "seed": seed,
            "sample_index": sample_index,
            "baseline_sha256": grid_hash(baseline),
            "cases": override_cases,
        },
        "target_edited": False,
    }
    (HERE / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
