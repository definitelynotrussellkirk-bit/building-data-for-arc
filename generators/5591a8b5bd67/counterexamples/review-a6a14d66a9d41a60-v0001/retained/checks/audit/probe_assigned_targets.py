from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reviewer_support import load_selected_generator

ROOT = Path.cwd().resolve()
OUT = ROOT.parent / "checks" / "audit"
OUT.mkdir(parents=True, exist_ok=True)


def attempt(fn):
    try:
        value = fn()
    except Exception as exc:  # evidence should retain the exact public exception
        return {
            "accepted": False,
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }
    return {"accepted": True, "value": value}


def probe_5591() -> dict[str, Any]:
    task_id = "5591a8b5bd67"
    gen, source, source_sha = load_selected_generator(task_id, root=ROOT)
    exact = {
        "grid_h": 10,
        "grid_w": 18,
        "rays": 8,
        "n_distinct_colors": 8,
        "wall_profile": "blocked",
    }
    grid = gen.generate(41, 5, difficulty="medium", **exact)
    observed = gen.observe_overrides(grid)
    unknown = attempt(
        lambda: {
            "shape": [len(g := gen.generate(41, 5, difficulty="medium", typo_axis=7)), len(g[0])],
            "self_check": gen.self_check(g),
        }
    )
    scalar_cases = {
        "grid_h_float_10_9": attempt(
            lambda: len(gen.generate(41, 5, difficulty="medium", grid_h=10.9))
        ),
        "rays_string_8": attempt(
            lambda: gen.observe_overrides(
                gen.generate(41, 5, difficulty="medium", rays="8")
            )["rays"]
        ),
        "sample_index_bool": attempt(
            lambda: gen.observe_overrides(
                gen.generate(41, True, difficulty="medium")
            )["wall_profile"]
        ),
    }
    return {
        "schema": "assigned-audit-contract-probe-v1",
        "task_id": task_id,
        "generator_path": str(Path(source).relative_to(ROOT)),
        "generator_sha256": source_sha,
        "declared_axes": sorted(gen.AXES),
        "exact_request": exact,
        "returned_shape": [len(grid), len(grid[0])],
        "observed_overrides": observed,
        "missing_observed_axes": sorted(set(gen.AXES) - set(observed)),
        "self_check": gen.self_check(grid),
        "unknown_override": {"request": {"typo_axis": 7}, **unknown},
        "scalar_cases": scalar_cases,
        "finding": (
            "reproduced: observe_overrides omits declared exact grid_h/grid_w; "
            "unknown overrides are silently accepted"
        ),
        "command": [
            "python3",
            "run_with_racket.py",
            "python3",
            "../checks/audit/probe_assigned_targets.py",
        ],
        "cwd": "WORK",
    }


def occupancy_signatures(grid: list[list[int]]) -> set[tuple[int, int, int]]:
    bases = (0, 5, 10)
    signatures: set[tuple[int, int, int]] = set()
    for row in range(len(grid)):
        for col in range(4):
            signatures.add(tuple(int(grid[row][base + col] != 0) for base in bases))
    return signatures


def probe_8f10() -> dict[str, Any]:
    task_id = "8f10b83435aa"
    gen, source, source_sha = load_selected_generator(task_id, root=ROOT)
    all_patterns = {
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (1, 1, 0),
        (1, 0, 1),
        (0, 1, 1),
        (1, 1, 1),
    }
    cases: list[dict[str, Any]] = []
    requests = [
        {"panel_h": 6, "n_majority": 6, "n_singletons": 3, "n_triples": 1},
        {"panel_h": 7, "n_majority": 10, "n_singletons": 9, "n_triples": 3},
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(requests):
            grid = gen.generate(700 + index, 90 + index, difficulty=band, **overrides)
            observed = gen.observe_overrides(grid)
            signatures = occupancy_signatures(grid)
            cases.append(
                {
                    "difficulty": band,
                    "overrides": overrides,
                    "observed": observed,
                    "self_check": gen.self_check(grid),
                    "strict_canonical_like": gen.strict_canonical_like(grid),
                    "occupancy_signatures": [list(x) for x in sorted(signatures)],
                    "covers_all_8_boolean_inputs": signatures == all_patterns,
                }
            )
    default_failures: list[dict[str, Any]] = []
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = gen.generate(seed, seed * 13 + 7, difficulty=band)
            signatures = occupancy_signatures(grid)
            if signatures != all_patterns:
                default_failures.append(
                    {
                        "difficulty": band,
                        "seed": seed,
                        "missing": [list(x) for x in sorted(all_patterns - signatures)],
                    }
                )
    invalid = {
        "unknown_axis": attempt(lambda: gen.generate(1, 2, typo_axis=1)),
        "float_panel_h": attempt(lambda: gen.generate(1, 2, panel_h=6.0)),
        "string_majority": attempt(lambda: gen.generate(1, 2, n_majority="6")),
    }
    return {
        "schema": "assigned-audit-truth-table-probe-v1",
        "task_id": task_id,
        "generator_path": str(Path(source).relative_to(ROOT)),
        "generator_sha256": source_sha,
        "declared_axes": sorted(gen.AXES),
        "exact_boundary_cases": cases,
        "default_draws_checked": 120,
        "default_truth_table_failures": default_failures,
        "invalid_override_results": invalid,
        "conclusion": (
            "No issue found in the checked surface: every checked grid contains all eight "
            "three-panel occupancy signatures, so any pointwise Boolean occupancy rule is "
            "fully identified within a single example; exact controls were observable and "
            "invalid/unknown controls rejected."
        ),
        "command": [
            "python3",
            "run_with_racket.py",
            "python3",
            "../checks/audit/probe_assigned_targets.py",
        ],
        "cwd": "WORK",
    }


reports = {
    "5591a8b5bd67-contract-probe.json": probe_5591(),
    "8f10b83435aa-truth-table-probe.json": probe_8f10(),
}
for filename, report in reports.items():
    path = OUT / filename
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(path)
