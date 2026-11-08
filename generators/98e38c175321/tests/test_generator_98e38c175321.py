"""Regression tests for the isolated-red diagonal-X generator repair."""
from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT / "puzzle_generators" / "per_puzzle" / "98e38c175321" / "generator.py"
)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_98e38c175321",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "98e38c175321":
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise AssertionError("canonical task 98e38c175321 is missing")


def _python_transform(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    seen = set()
    seeds = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 2
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if len(component) == 1:
                seeds.append(component[0])
    for sr, sc in seeds:
        for dr, dc in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            r, c = sr + dr, sc + dc
            if 0 <= r < h and 0 <= c < w and grid[r][c] in (0, 2):
                out[r][c] = 3
    return out


def test_all_canonical_inputs_pass_and_define_the_pinned_signatures():
    generator = _load_generator()
    pairs = _canonical_pairs()
    signatures = {
        generator.canonical_profile_signature(pair["input"])
        for pair in pairs
    }
    assert signatures == generator._CANONICAL_SIGNATURES
    assert all(generator.self_check(pair["input"]) == [] for pair in pairs)


def test_every_profile_mode_and_color_override_is_exact():
    generator = _load_generator()
    for profile in generator.LAYOUT_PROFILES:
        for mode in generator.PLACEMENT_MODES:
            for color in generator.NONRED_COLORS:
                grid = generator.generate(
                    731,
                    19,
                    difficulty="hard",
                    layout_profile=profile,
                    placement_mode=mode,
                    nonred_color=color,
                )
                assert generator.self_check(grid) == []
                assert generator.observe_overrides(grid) == {
                    "layout_profile": profile,
                    "placement_mode": mode,
                    "nonred_color": color,
                }
                output = _python_transform(grid)
                assert output != grid
                assert all(
                    output[r][c] == value
                    for r, row in enumerate(grid)
                    for c, value in enumerate(row)
                    if value not in (0, 2)
                )


def test_each_band_reaches_every_complete_profile_in_200_draws():
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        counts = {profile: 0 for profile in generator.LAYOUT_PROFILES}
        for seed in range(200):
            grid = generator.generate(seed, seed * 29 + 7, difficulty=band)
            assert generator.self_check(grid, difficulty=band) == []
            counts[generator.observe_overrides(grid)["layout_profile"]] += 1
        assert all(count > 0 for count in counts.values()), (band, counts)


def test_recombined_profile_is_rejected_by_strict_linked_signature():
    generator = _load_generator()
    grid = generator.generate(
        11,
        3,
        layout_profile="p0",
        placement_mode="interior",
        nonred_color=6,
    )
    changed = [row[:] for row in grid]
    for r, row in enumerate(changed):
        for c, value in enumerate(row):
            if value == 0:
                changed[r][c] = 2
                break
        else:
            continue
        break
    assert generator.canonical_profile_signature(changed) not in generator._CANONICAL_SIGNATURES
    assert generator.self_check(changed)


def test_deterministic_fresh_returns_and_global_rng_purity():
    generator = _load_generator()
    random.seed(8675309)
    before = random.getstate()
    first = generator.generate(123, 17, difficulty="medium")
    after = random.getstate()
    second = generator.generate(123, 17, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == generator.generate(123, 17, difficulty="medium")
