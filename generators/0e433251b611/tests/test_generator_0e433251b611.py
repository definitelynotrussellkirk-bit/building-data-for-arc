"""Focused regression tests for the seeded-chamber flood generator."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "puzzle_generators/per_puzzle/0e433251b611/generator.py"
CANONICAL_PATH = ROOT / "data/canonical/puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_0e433251b611", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decode(rows: list[str]) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


def _canonical_pairs():
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != "0e433251b611":
            continue
        pairs = row["train"] + [row["test"]]
        return [(_decode(pair["input"]), _decode(pair["output"])) for pair in pairs]
    raise AssertionError("canonical task row not found")


def _ambiguous_two_seed_grid() -> list[list[int]]:
    grid = [[9] * 7 for _ in range(7)]
    for row in range(1, 6):
        for col in range(1, 6):
            grid[row][col] = 0
    grid[2][2] = 3
    grid[4][4] = 6
    return grid


def test_rule_hash_and_canonical_parity():
    gen = _load_generator()
    assert gen.RULE_HASH == "d0a24e887acb"
    for input_grid, expected in _canonical_pairs():
        assert gen.self_check(input_grid) == []
        assert gen.rule_mirror(input_grid) == expected


def test_every_declared_override_is_observable():
    gen = _load_generator()
    for layout in gen.LAYOUT_PROFILES:
        for seed_pattern in gen.SEED_PATTERNS:
            for color_relation in gen.COLOR_RELATIONS:
                for size_relation in gen.SIZE_RELATIONS:
                    requested = {
                        "layout_profile": layout,
                        "seed_pattern": seed_pattern,
                        "color_relation": color_relation,
                        "size_relation": size_relation,
                    }
                    grid = gen.generate(1234, 17, difficulty="hard", **requested)
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == requested


def test_unknown_override_is_rejected():
    gen = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="row_3")


def test_self_check_rejects_multiple_seeds_in_one_chamber():
    gen = _load_generator()
    errors = gen.self_check(_ambiguous_two_seed_grid())
    assert any("at most one" in error for error in errors)


def test_self_check_rejects_partial_wall_texture():
    gen = _load_generator()
    grid = gen.generate(17, 0)
    grid[2][2] = 9
    errors = gen.self_check(grid)
    assert any("complete divider" in error for error in errors)


def test_generated_lessons_refute_canonical_shortcuts():
    gen = _load_generator()
    grids = [gen.generate(91, sample_index) for sample_index in range(4)]
    official = [gen.rule_mirror(grid) for grid in grids]
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert any(rival(grid) != answer for grid, answer in zip(grids, official)), name
