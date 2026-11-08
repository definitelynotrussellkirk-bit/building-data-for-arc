#!/usr/bin/env python3
"""Independent structural fuzzing for the shipped reviewed generator.

This executes ``solve/source/generator.py`` under a tiny deterministic stand-in
for the repository's generation context.  It is deliberately *not* a substitute
for the retained production-runtime battery: it stress-tests structure that must
hold regardless of keyed-RNG implementation—validation, exact axes, component
invariants, shortcut separation, determinism, and lesson scheduling.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys
import time
import types
from typing import Any

BANDS = (None, "easy", "medium", "hard")
MAX_ISSUES = 50


class _Context:
    def __init__(
        self,
        *,
        seed: int,
        sample_index: int,
        version: str,
        task_id: str,
        difficulty: str | None,
        overrides: dict[str, Any],
    ) -> None:
        self.seed = seed
        self.sample_index = sample_index
        self.version = version
        self.task_id = task_id
        self.difficulty = difficulty
        self.overrides = dict(overrides)

    def _key(self, name: str) -> int:
        payload = (
            f"{self.task_id}\0{self.version}\0{self.seed}\0{self.sample_index}"
            f"\0{self.difficulty}\0{name}"
        ).encode()
        return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")

    def draw_rng(self, name: str) -> random.Random:
        return random.Random(self._key(name))

    def draw_choice(self, name: str, choices):
        values = tuple(choices)
        if not values:
            raise ValueError(f"empty choice domain for {name}")
        if self.overrides.get(name) is not None:
            value = self.overrides[name]
            if value not in values:
                raise ValueError(f"{name} override {value!r} outside {values!r}")
            return value
        return values[self._key(name) % len(values)]

    def draw_int_strict(self, name: str, low: int, high: int) -> int:
        if self.overrides.get(name) is not None:
            value = self.overrides[name]
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} override {value!r} outside {low}..{high}")
            return value
        return low + self._key(name) % (high - low + 1)


def _install_stub_runtime() -> dict[str, types.ModuleType | None]:
    saved = {name: sys.modules.get(name) for name in (
        "puzzle_generators",
        "puzzle_generators.base",
        "puzzle_generators.helpers",
        "puzzle_generators.helpers.grid",
    )}
    package = types.ModuleType("puzzle_generators")
    package.__path__ = []
    base = types.ModuleType("puzzle_generators.base")
    helpers = types.ModuleType("puzzle_generators.helpers")
    helpers.__path__ = []
    grid = types.ModuleType("puzzle_generators.helpers.grid")

    def gen_ctx(**kwargs):
        return _Context(**kwargs)

    def full_grid(height: int, width: int, value: int):
        return [[value for _ in range(width)] for _ in range(height)]

    base.gen_ctx = gen_ctx
    grid.full_grid = full_grid
    package.base = base
    package.helpers = helpers
    helpers.grid = grid
    sys.modules.update({
        "puzzle_generators": package,
        "puzzle_generators.base": base,
        "puzzle_generators.helpers": helpers,
        "puzzle_generators.helpers.grid": grid,
    })
    return saved


def _restore_modules(saved: dict[str, types.ModuleType | None]) -> None:
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


def _load_generator(path: Path):
    saved = _install_stub_runtime()
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        name = f"reviewed_generator_{digest}_{time.time_ns()}"
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(name, None)
        return module
    finally:
        _restore_modules(saved)


def _frozen(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def run_fuzz(
    generator_path: str | Path,
    *,
    default_seed_count: int,
    default_index_count: int,
    override_seed_count: int,
    schedule_seed_count: int,
) -> dict[str, Any]:
    path = Path(generator_path)
    started = time.monotonic()
    issues: list[dict[str, Any]] = []

    def add(kind: str, **details: Any) -> None:
        if len(issues) < MAX_ISSUES:
            issues.append({"kind": kind, **details})

    for name, value in (
        ("default_seed_count", default_seed_count),
        ("default_index_count", default_index_count),
        ("override_seed_count", override_seed_count),
        ("schedule_seed_count", schedule_seed_count),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    if not path.is_file():
        raise FileNotFoundError(path)

    generator = _load_generator(path)
    required = (
        "TARGET_SHAPES", "LESSON_SCHEDULE_PERIOD", "LESSON_COMPETITORS",
        "generate", "self_check", "observe_overrides", "_winner", "_shape_name",
        "_intended_output", "_rival_largest_cell_count", "_rival_widest_component",
        "_rival_leftmost_component", "_rival_rightmost_component",
        "_rival_first_nonrectangular", "_rival_same_color_components",
    )
    for name in required:
        if not hasattr(generator, name):
            add("missing_required_symbol", symbol=name)
    if issues:
        return {
            "schema": "arcpuzzles-generator-structural-fuzz-v1",
            "generator": str(path),
            "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "issues": issues,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }

    default_cases = 0
    unique_default_inputs: set[tuple[tuple[int, ...], ...]] = set()
    for seed in range(default_seed_count):
        for sample_index in range(default_index_count):
            for band in BANDS:
                try:
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    again = generator.generate(seed, sample_index, difficulty=band)
                    default_cases += 1
                    if grid != again:
                        add("nondeterministic_default", seed=seed, sample_index=sample_index, band=band)
                    errors = generator.self_check(grid)
                    if errors:
                        add("self_check_failed", seed=seed, sample_index=sample_index, band=band, errors=errors)
                        continue
                    observed = generator.observe_overrides(grid)
                    expected_observed = {
                        "grid_h": len(grid),
                        "grid_w": len(grid[0]),
                        "target_shape": generator._shape_name(generator._winner(grid)),
                    }
                    if observed != expected_observed:
                        add(
                            "observe_mismatch", seed=seed, sample_index=sample_index,
                            band=band, observed=observed, expected=expected_observed,
                        )
                    answer = generator._intended_output(grid)
                    for rival_name, rival in (
                        ("largest_cell_count", generator._rival_largest_cell_count),
                        ("widest_component", generator._rival_widest_component),
                        ("leftmost_component", generator._rival_leftmost_component),
                        ("first_nonrectangular", generator._rival_first_nonrectangular),
                    ):
                        if rival(grid) == answer:
                            add(
                                "default_rival_survived", rival=rival_name, seed=seed,
                                sample_index=sample_index, band=band,
                            )
                    color_split_differs = generator._rival_same_color_components(grid) != answer
                    if color_split_differs != (sample_index % 2 == 0):
                        add(
                            "color_split_schedule_mismatch", seed=seed,
                            sample_index=sample_index, band=band,
                            differs=color_split_differs,
                        )
                    rightmost_differs = generator._rival_rightmost_component(grid) != answer
                    if rightmost_differs != (sample_index % 2 == 0):
                        add(
                            "rightmost_layout_schedule_mismatch", seed=seed,
                            sample_index=sample_index, band=band,
                            differs=rightmost_differs,
                        )
                    unique_default_inputs.add(_frozen(grid))
                except Exception as exc:  # one malformed case should not hide the rest of the report
                    add(
                        "default_exception", seed=seed, sample_index=sample_index,
                        band=band, exception=f"{type(exc).__name__}: {exc}",
                    )
                if len(issues) >= MAX_ISSUES:
                    break
            if len(issues) >= MAX_ISSUES:
                break
        if len(issues) >= MAX_ISSUES:
            break

    legal_override_cases = 0
    if len(issues) < MAX_ISSUES:
        for seed, band, height, width, shape, sample_index in itertools.product(
            range(override_seed_count),
            BANDS,
            range(8, 12),
            range(10, 14),
            tuple(generator.TARGET_SHAPES),
            (0, 1),
        ):
            requested = {"grid_h": height, "grid_w": width, "target_shape": shape}
            try:
                grid = generator.generate(seed, sample_index, difficulty=band, **requested)
                legal_override_cases += 1
                errors = generator.self_check(grid)
                if errors:
                    add(
                        "override_self_check_failed", seed=seed, sample_index=sample_index,
                        band=band, requested=requested, errors=errors,
                    )
                observed = generator.observe_overrides(grid)
                if observed != requested:
                    add(
                        "override_not_exact", seed=seed, sample_index=sample_index,
                        band=band, requested=requested, observed=observed,
                    )
                if grid != generator.generate(seed, sample_index, difficulty=band, **requested):
                    add(
                        "nondeterministic_override", seed=seed, sample_index=sample_index,
                        band=band, requested=requested,
                    )
            except Exception as exc:
                add(
                    "legal_override_exception", seed=seed, sample_index=sample_index,
                    band=band, requested=requested,
                    exception=f"{type(exc).__name__}: {exc}",
                )
            if len(issues) >= MAX_ISSUES:
                break

    lesson_query_cases = 0
    if len(issues) < MAX_ISSUES:
        for seed, band, start in itertools.product(
            range(schedule_seed_count),
            BANDS,
            range(generator.LESSON_SCHEDULE_PERIOD),
        ):
            try:
                grids = [generator.generate(seed, start + offset, difficulty=band) for offset in range(5)]
                answers = [generator._intended_output(grid) for grid in grids]
                rival_outputs = {
                    name: [rival(grid) for grid in grids]
                    for name, rival in generator.LESSON_COMPETITORS.items()
                }
                for query_index in range(5):
                    demo_indexes = [index for index in range(5) if index != query_index]
                    for name, outputs in rival_outputs.items():
                        if all(outputs[index] == answers[index] for index in demo_indexes):
                            add(
                                "lesson_competitor_survived", competitor=name, seed=seed,
                                band=band, start=start, query_index=query_index,
                            )
                    lesson_query_cases += 1
            except Exception as exc:
                add(
                    "lesson_exception", seed=seed, band=band, start=start,
                    exception=f"{type(exc).__name__}: {exc}",
                )
            if len(issues) >= MAX_ISSUES:
                break

    invalid_requests = [
        ((True, 0), {}),
        ((1.0, 0), {}),
        (("1", 0), {}),
        ((-1, 0), {}),
        ((0, True), {}),
        ((0, -1), {}),
        ((0, 0), {"difficulty": "expert"}),
        ((0, 0), {"typo_axis": 1}),
        ((0, 0), {"grid_h": True}),
        ((0, 0), {"grid_w": 9.0}),
        ((0, 0), {"target_shape": "triangle"}),
    ]
    invalid_requests_checked = 0
    if len(issues) < MAX_ISSUES:
        for args, kwargs in invalid_requests:
            invalid_requests_checked += 1
            try:
                generator.generate(*args, **kwargs)
            except (TypeError, ValueError):
                pass
            except Exception as exc:
                add(
                    "invalid_request_wrong_exception", args=list(args), kwargs=kwargs,
                    exception=f"{type(exc).__name__}: {exc}",
                )
            else:
                add("invalid_request_accepted", args=list(args), kwargs=kwargs)

    fixtures_checked = 0
    if hasattr(generator, "mutation_fixtures") and len(issues) < MAX_ISSUES:
        try:
            for name, grid in generator.mutation_fixtures():
                fixtures_checked += 1
                if not generator.self_check(grid):
                    add("mutation_fixture_accepted", fixture=name)
        except Exception as exc:
            add("mutation_fixture_exception", exception=f"{type(exc).__name__}: {exc}")

    return {
        "schema": "arcpuzzles-generator-structural-fuzz-v1",
        "scope_note": (
            "Uses a deterministic stand-in generation context; production-runtime and Racket claims "
            "remain bound to the retained evidence bundle."
        ),
        "generator": str(path),
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "default_cases": default_cases,
        "legal_override_cases": legal_override_cases,
        "lesson_query_cases": lesson_query_cases,
        "invalid_requests_checked": invalid_requests_checked,
        "mutation_fixtures_checked": fixtures_checked,
        "unique_default_inputs": len(unique_default_inputs),
        "issues": issues,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generator", type=Path, nargs="?", default=Path("solve/source/generator.py"))
    parser.add_argument("--preset", choices=("quick", "full"), default="quick")
    parser.add_argument("--json-out", type=Path, help="also write the JSON report here")
    args = parser.parse_args(argv)
    counts = {
        "quick": dict(
            default_seed_count=10,
            default_index_count=20,
            override_seed_count=2,
            schedule_seed_count=10,
        ),
        "full": dict(
            default_seed_count=100,
            default_index_count=100,
            override_seed_count=10,
            schedule_seed_count=100,
        ),
    }[args.preset]
    report = run_fuzz(args.generator, **counts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    return 0 if not report["issues"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
