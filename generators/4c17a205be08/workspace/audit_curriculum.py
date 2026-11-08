#!/usr/bin/env python3
"""Deterministic semantic/curriculum audit for generator 4c17a205be08.

This is intentionally independent of the repository check orchestrator so a
future reviewer can quickly answer three questions from the checked-out task:

1. Which declared rival rules fit every canonical pair?
2. Which generated branches refute those rivals, with an exact witness?
3. Does every scheduled five-demonstration lesson satisfy lesson_identifiable?

The selected Racket program remains authoritative.  This tool uses the
Python rule mirror only for fast diagnostics; use the battery's rule_smoke and
semantic_gate (or a protected Racket probe) for authority-backed verification.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "4c17a205be08"


def _load_generator():
    try:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError:
        here = Path(__file__).resolve()
        repo = here.parents[3]
        runtime = repo / "shared" / "runtime"
        if runtime.is_dir() and str(runtime) not in sys.path:
            sys.path.insert(0, str(runtime))
        path = here.parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"generator_{TASK_ID}_for_audit", path
        )
        if not spec or not spec.loader:
            raise RuntimeError(f"cannot load generator from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def _canonical_path() -> Path:
    here = Path(__file__).resolve()
    candidates = (
        here.parents[3] / "shared" / "data" / "canonical" / "puzzles.jsonl",
        here.parents[4] / "data" / "canonical" / "puzzles.jsonl",
        here.parents[5] / "data" / "canonical" / "puzzles.jsonl",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("canonical puzzles.jsonl not found")


def _normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [[int(value) for value in row] for row in grid]


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    for line in _canonical_path().read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        test = row.get("test", [])
        tests = [test] if isinstance(test, dict) else list(test)
        pairs = list(row.get("train", [])) + tests
        return [
            {
                "input": _normalize_grid(pair["input"]),
                "output": _normalize_grid(pair["output"]),
            }
            for pair in pairs
        ]
    raise KeyError(f"canonical task {TASK_ID} not found")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_witness(*, seed: int, sample_index: int, difficulty: str, grid, authoritative, rival, observed):
    return {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "observed": observed,
        "input": grid,
        "authoritative_output": authoritative,
        "rival_output": rival,
    }


def build_report(*, seed: int = 20261002, samples: int = 24) -> dict[str, Any]:
    if samples < 1:
        raise ValueError("samples must be positive")

    gen = _load_generator()
    pairs = _canonical_pairs()
    generator_path = Path(gen.__file__).resolve()

    canonical_shortcuts: dict[str, Any] = {}
    for name, rival in sorted(gen.CANONICAL_SHORTCUTS.items()):
        matched = sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        canonical_shortcuts[name] = {
            "matched_pairs": matched,
            "total_pairs": len(pairs),
            "fits_all": matched == len(pairs),
        }

    transform_counts: Counter[str] = Counter()
    palette_counts: Counter[int] = Counter()
    component_counts: Counter[int] = Counter()
    invalid: list[dict[str, Any]] = []
    shortcut_state = {
        name: {
            "disagreement_count": 0,
            "disagreement_transforms": set(),
            "first_witness": None,
        }
        for name in gen.CANONICAL_SHORTCUTS
    }

    difficulty = "medium"
    for sample_index in range(samples):
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        findings = list(gen._teaching_reasons(grid) or [])
        if findings:
            invalid.append({"sample_index": sample_index, "findings": findings})
            continue

        observed = gen.observe_overrides(grid)
        transform = observed["transform"]
        authoritative = gen.rule_mirror(grid)
        transform_counts[transform] += 1
        palette_counts[len({value for row in grid for value in row})] += 1
        component_counts[gen._nonbackground_components(grid)] += 1

        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            rival_output = rival(grid)
            if rival_output == authoritative:
                continue
            state = shortcut_state[name]
            state["disagreement_count"] += 1
            state["disagreement_transforms"].add(transform)
            if state["first_witness"] is None:
                state["first_witness"] = _first_witness(
                    seed=seed,
                    sample_index=sample_index,
                    difficulty=difficulty,
                    grid=grid,
                    authoritative=authoritative,
                    rival=rival_output,
                    observed=observed,
                )

    shortcut_refutations = {}
    for name, state in sorted(shortcut_state.items()):
        shortcut_refutations[name] = {
            "disagreement_count": state["disagreement_count"],
            "disagreement_transforms": sorted(state["disagreement_transforms"]),
            "first_witness": state["first_witness"],
        }

    window_failures = []
    window_checked = 0
    for window_difficulty in ("easy", "medium", "hard"):
        for start in range(len(gen.ALL_TRANSFORMS)):
            window_checked += 1
            window_seed = seed + start
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(
                    window_seed,
                    sample_index,
                    difficulty=window_difficulty,
                )
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_index = start + gen.EXAMPLES_NEEDED
            query_grid = gen.generate(
                window_seed,
                query_index,
                difficulty=window_difficulty,
            )
            findings = list(gen.lesson_identifiable(
                demos,
                {"input": query_grid, "output": gen.rule_mirror(query_grid)},
            ) or [])
            if findings:
                window_failures.append({
                    "difficulty": window_difficulty,
                    "seed": window_seed,
                    "start": start,
                    "findings": findings,
                })

    return {
        "schema": "4c17a205be08_curriculum_audit/1",
        "task_id": TASK_ID,
        "generator_sha256": _sha256(generator_path),
        "rule_hash_declared": getattr(gen, "RULE_HASH", None),
        "seed": seed,
        "canonical": {
            "path": str(_canonical_path()),
            "pair_count": len(pairs),
            "shortcuts": canonical_shortcuts,
        },
        "generated": {
            "difficulty": difficulty,
            "sample_index_range": [0, samples - 1],
            "sample_count": samples,
            "invalid_count": len(invalid),
            "invalid": invalid,
            "transform_counts": dict(sorted(transform_counts.items())),
            "palette_size_counts": {
                str(key): value for key, value in sorted(palette_counts.items())
            },
            "nonbackground_component_counts": {
                str(key): value for key, value in sorted(component_counts.items())
            },
            "shortcut_refutations": shortcut_refutations,
        },
        "lesson_windows": {
            "examples_needed": gen.EXAMPLES_NEEDED,
            "checked": window_checked,
            "identifiable": window_checked - len(window_failures),
            "failures": window_failures,
        },
        "authority_note": (
            "Python mirror diagnostic only; protected-Racket battery evidence "
            "is required for authority-backed claims."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261002)
    parser.add_argument("--samples", type=int, default=24)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = build_report(seed=args.seed, samples=args.samples)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
