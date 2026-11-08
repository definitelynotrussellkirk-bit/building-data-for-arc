#!/usr/bin/env python3
"""Bounded adversarial probe for the reconciled two-room generator.

Surfaces:
1. sampler boundaries and forced retry exhaustion;
2. API/verifier rejection paths plus semantic-rival separation.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_DIR = Path(__file__).resolve().parents[1]
SOURCE = TASK_DIR / "generator.py"
SPEC = importlib.util.spec_from_file_location("probe_generator_9acebbb8a360", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


class AlwaysMinimumRng:
    """Forces every random placement attempt onto the same rectangle."""

    def __init__(self) -> None:
        self.calls = 0

    def randint(self, low: int, high: int) -> int:
        self.calls += 1
        return low


def _sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _expect_error(exc_type, fn, label: str) -> str:
    try:
        fn()
    except exc_type as exc:
        return f"{label}: {type(exc).__name__}: {exc}"
    raise AssertionError(f"{label}: expected {exc_type.__name__}")


def main() -> None:
    counts = {
        "boundary_draws": 0,
        "default_draws": 0,
        "lesson_checks": 0,
        "rejection_checks": 0,
    }
    shape_hits: set[tuple[int, int]] = set()
    sample_hashes: list[str] = []

    # Exhaust every declared shape in every difficulty band. This also attacks
    # the small 8x10 canvas where random placement is most constrained.
    for difficulty in ("easy", "medium", "hard"):
        for height in range(8, 14):
            for width in range(10, 17):
                for seed in range(10):
                    grid = GEN.generate(
                        seed,
                        height * 100 + width,
                        difficulty=difficulty,
                        grid_h=height,
                        grid_w=width,
                    )
                    assert (len(grid), len(grid[0])) == (height, width)
                    assert GEN.self_check(grid) == []
                    assert GEN.strict_canonical_like(grid) == []
                    truth = GEN.rule_mirror(grid)
                    assert truth != grid
                    assert GEN.SEMANTIC_RIVALS["identity"](grid) != truth
                    assert (
                        GEN.SEMANTIC_RIVALS["single_global_seed_color"](grid)
                        != truth
                    )
                    shape_hits.add((height, width))
                    counts["boundary_draws"] += 1
                    if len(sample_hashes) < 8:
                        sample_hashes.append(_sha(grid))

    # Broad defaults catch accidental collisions and confirm deterministic,
    # fresh-return behavior across the unoverridden schedule.
    for seed in range(100):
        for sample_index in range(10):
            grid = GEN.generate(seed, sample_index)
            assert GEN.self_check(grid) == []
            replay = GEN.generate(seed, sample_index)
            assert replay == grid
            mutated = copy.deepcopy(grid)
            mutated[0][0] = 9 if mutated[0][0] != 9 else 8
            assert GEN.generate(seed, sample_index) == grid
            counts["default_draws"] += 1

    # Force all 12,800 random candidate attempts to collide. The helper must
    # terminate in the deterministic legal fallback instead of silently
    # emitting one room or looping forever.
    stuck = AlwaysMinimumRng()
    fallback = GEN._place_exactly_two_frames(8, 10, stuck)
    assert fallback == [(0, 0, 4, 3), (0, 6, 4, 9)], fallback
    assert stuck.calls >= 12_800

    # Generated lessons must separate both declared competitors.
    for seed in range(30):
        pairs = []
        for sample_index in range(3):
            grid = GEN.generate(10_000 + seed, sample_index)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:2], pairs[2]) == []
        counts["lesson_checks"] += 1

    rejection_messages = []
    cases = [
        (TypeError, lambda: GEN.generate(True, 0), "bool seed"),
        (TypeError, lambda: GEN.generate(1, True), "bool sample_index"),
        (TypeError, lambda: GEN.generate(1, -1), "negative sample_index"),
        (ValueError, lambda: GEN.generate(1, 0, difficulty="extreme"), "difficulty"),
        (ValueError, lambda: GEN.generate(1, 0, n_frames=2), "singleton n_frames"),
        (ValueError, lambda: GEN.generate(1, 0, palette_kind="warm"), "stale axis"),
        (TypeError, lambda: GEN.generate(1, 0, grid_h=True), "bool grid_h"),
        (
            ValueError,
            lambda: GEN.generate(1, 0, texture="no_frames", grid_h=9),
            "mixed degenerate/ordinary overrides",
        ),
    ]
    for exc_type, fn, label in cases:
        rejection_messages.append(_expect_error(exc_type, fn, label))
        counts["rejection_checks"] += 1

    for texture in GEN.DEGENERATE_TEXTURES:
        assert GEN.self_check(GEN.generate(1, 0, texture=texture)), texture

    report = {
        "task_id": GEN.GENERATOR_ID,
        "version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "counts": counts,
        "shape_count": len(shape_hits),
        "shape_range": [min(shape_hits), max(shape_hits)],
        "forced_retry_calls": stuck.calls,
        "forced_fallback": fallback,
        "sample_hashes": sample_hashes,
        "rejections": rejection_messages,
        "status": "pass",
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
