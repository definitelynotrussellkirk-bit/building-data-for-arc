#!/usr/bin/env python3
"""Reproduce the bounded adversarial audit for generator 395201c95f9d.

Run from the packet's repo directory through run_with_racket.py so the shared
runtime is on PYTHONPATH.  The script imports the audited generator by file,
checks every declared exact-axis cross-product, every cyclic four-demo schedule
window, and a broad default sample/rival execution census, then writes the
source-bound JSON receipt beside this file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


TASK_ID = "395201c95f9d"
THIS = Path(__file__).resolve()
PACKET_ROOT = THIS.parents[3]
GENERATOR_PATH = PACKET_ROOT / "repo" / "generators" / TASK_ID / "generator.py"
OUTPUT_PATH = THIS.with_name("custom_probe.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_failure(failures: list[dict[str, Any]], kind: str, **details: Any) -> None:
    # Bound the receipt while preserving the first actionable examples.
    if len(failures) < 100:
        failures.append({"kind": kind, **details})


def main() -> int:
    mod = load_generator()
    failures: list[dict[str, Any]] = []

    # Every validator and rival re-analyzes the same visible grid.  Cache that
    # pure analysis by immutable grid bytes so this exhaustive audit remains a
    # practical replay rather than repeating identical D4 work dozens of times.
    original_analysis = mod._analysis
    analysis_cache: dict[tuple[tuple[int, ...], ...], dict[str, Any]] = {}

    def cached_analysis(grid: Any) -> dict[str, Any]:
        key = tuple(tuple(row) for row in grid)
        if key not in analysis_cache:
            analysis_cache[key] = original_analysis(grid)
        return analysis_cache[key]

    mod._analysis = cached_analysis

    generation_cache: dict[tuple[str, int, int], list[list[int]]] = {}

    def default_grid(difficulty: str, seed: int, sample_index: int) -> list[list[int]]:
        key = (difficulty, seed, sample_index)
        if key not in generation_cache:
            generation_cache[key] = mod.generate(seed, sample_index, difficulty=difficulty)
        return generation_cache[key]

    exact_attempted = 0
    exact_completed = 0
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for panel_h in range(4, 9):
            for panel_w in range(4, 8):
                for cell_count in range(4, 7):
                    for match_panel in range(2):
                        for transform_index, transform in enumerate(mod._CODES):
                            exact_attempted += 1
                            seed = 100_000 * band_index + exact_attempted
                            overrides = {
                                "panel_h": panel_h,
                                "panel_w": panel_w,
                                "cell_count": cell_count,
                                "match_panel": match_panel,
                                "transform": transform,
                            }
                            try:
                                grid = mod.generate(
                                    seed,
                                    transform_index,
                                    difficulty=difficulty,
                                    **overrides,
                                )
                                observed = mod.observe_overrides(grid)
                                errors = mod.self_check(
                                    grid,
                                    difficulty=difficulty,
                                    meta={"overrides": overrides},
                                )
                                output = mod.rule_mirror(grid)
                            except Exception as exc:  # audit receipt, not unit-test masking
                                add_failure(
                                    failures,
                                    "exact_override_exception",
                                    difficulty=difficulty,
                                    overrides=overrides,
                                    exception=f"{type(exc).__name__}: {exc}",
                                )
                                continue
                            exact_completed += 1
                            if observed != overrides:
                                add_failure(
                                    failures,
                                    "exact_override_mismatch",
                                    difficulty=difficulty,
                                    overrides=overrides,
                                    observed=observed,
                                )
                            if errors:
                                add_failure(
                                    failures,
                                    "exact_override_self_check",
                                    difficulty=difficulty,
                                    overrides=overrides,
                                    errors=errors,
                                )
                            if output == grid:
                                add_failure(
                                    failures,
                                    "exact_override_identity_output",
                                    difficulty=difficulty,
                                    overrides=overrides,
                                )

    window_attempted = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(20):
            for start in range(16):
                window_attempted += 1
                try:
                    pairs = []
                    for offset in range(5):
                        grid = default_grid(difficulty, seed, start + offset)
                        pairs.append({"input": grid, "output": mod.rule_mirror(grid)})
                    errors = mod.lesson_identifiable(pairs[:4], pairs[4])
                except Exception as exc:
                    add_failure(
                        failures,
                        "lesson_window_exception",
                        difficulty=difficulty,
                        seed=seed,
                        start=start,
                        exception=f"{type(exc).__name__}: {exc}",
                    )
                    continue
                if errors:
                    add_failure(
                        failures,
                        "lesson_window_not_identifiable",
                        difficulty=difficulty,
                        seed=seed,
                        start=start,
                        errors=errors,
                    )

    default_attempted = 0
    self_check_failures = 0
    rival_exceptions = 0
    rivals = dict(mod.LESSON_COMPETITORS)
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(100):
            for sample_index in range(16):
                default_attempted += 1
                try:
                    grid = default_grid(difficulty, seed, sample_index)
                except Exception as exc:
                    self_check_failures += 1
                    add_failure(
                        failures,
                        "default_generation_exception",
                        difficulty=difficulty,
                        seed=seed,
                        sample_index=sample_index,
                        exception=f"{type(exc).__name__}: {exc}",
                    )
                    continue
                errors = mod.self_check(grid, difficulty=difficulty)
                if errors:
                    self_check_failures += 1
                    add_failure(
                        failures,
                        "default_self_check",
                        difficulty=difficulty,
                        seed=seed,
                        sample_index=sample_index,
                        errors=errors,
                    )
                for name, rival in rivals.items():
                    try:
                        rival(grid)
                    except Exception as exc:
                        rival_exceptions += 1
                        add_failure(
                            failures,
                            "rival_exception",
                            rival=name,
                            difficulty=difficulty,
                            seed=seed,
                            sample_index=sample_index,
                            exception=f"{type(exc).__name__}: {exc}",
                        )

    exact_failures = sum(1 for row in failures if row["kind"].startswith("exact_override"))
    window_failures = sum(1 for row in failures if row["kind"].startswith("lesson_window"))
    result = {
        "task_id": TASK_ID,
        "generator_sha256": sha256(GENERATOR_PATH),
        "rule_hash": mod.RULE_HASH,
        "command": [
            "python3",
            "run_with_racket.py",
            "python3",
            "../checks/audit/395201c95f9d/probe.py",
        ],
        "cwd": "packet_root",
        "checks": {
            "exact_override_matrix": {
                "attempted": exact_attempted,
                "completed": exact_completed,
                "failure_count": exact_failures,
            },
            "cyclic_four_demo_windows": {
                "attempted": window_attempted,
                "failure_count": window_failures,
            },
            "default_samples": {
                "attempted": default_attempted,
                "self_check_failures": self_check_failures,
                "rival_exceptions": rival_exceptions,
                "rival_count": len(rivals),
            },
        },
        "failures": failures,
        "status": "no_issue_found" if not failures else "issues_found",
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
