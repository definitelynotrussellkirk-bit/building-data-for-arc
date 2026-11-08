from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = TASK_DIR.parents[1]
RUNTIME_DIR = REPO_DIR / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME_DIR))

SPEC = importlib.util.spec_from_file_location("review_e9905db3a38d_generator", TASK_DIR / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

BANDS = ("easy", "medium", "hard")


def _canonical_record() -> dict:
    path = REPO_DIR / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("task_id") == "e9905db3a38d":
            return record
    raise AssertionError("canonical task e9905db3a38d not found")


def _active_code_block(grid: list[list[int]]) -> tuple[int, int, list[list[int]]]:
    code = grid[-2:]
    active = [col for col in range(len(grid[0])) if any(code[row][col] for row in range(2))]
    assert active
    start, end = min(active), max(active)
    return start, end, [row[start : end + 1] for row in code]


def _norm(points: set[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return frozenset((row - min_row, col - min_col) for row, col in points)


def _shape(grid: list[list[int]], color: int) -> frozenset[tuple[int, int]]:
    points = {
        (row, col)
        for row, line in enumerate(grid[:-2])
        for col, value in enumerate(line)
        if value == color
    }
    assert points
    return _norm(points)


def _rotate_cw(shape: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    height = max(row for row, _ in shape) + 1
    return _norm({(col, height - 1 - row) for row, col in shape})


def test_metadata_pins_rule_and_declares_only_real_axes() -> None:
    assert getattr(GEN, "RULE_HASH", None) == "7b04fc79d5f0"
    assert set(GEN.AXES) == {"tile_size", "n_codecols"}
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()


def test_override_contract_accepts_full_domain_and_rejects_unknown_keys() -> None:
    assert callable(getattr(GEN, "observe_overrides", None))
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, difficulty="easy", typo_axis=3)

    for band in BANDS:
        for tile_size in range(2, 5):
            for n_codecols in range(2, 5):
                grid = GEN.generate(
                    991,
                    tile_size * 10 + n_codecols,
                    difficulty=band,
                    tile_size=tile_size,
                    n_codecols=n_codecols,
                )
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid) == {
                    "tile_size": tile_size,
                    "n_codecols": n_codecols,
                }


def test_generated_distribution_exposes_semantics_without_position_shortcuts() -> None:
    fixed_code_1 = 0
    fixed_code_4 = 0
    layouts: set[tuple[tuple[int, ...], ...]] = set()

    for band_index, band in enumerate(BANDS):
        for sample_index in range(24):
            grid = GEN.generate(1400 + band_index, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            tile_size = observed["tile_size"]
            n_codecols = observed["n_codecols"]

            output_h = 2 * tile_size + 1
            output_w = n_codecols * tile_size + (n_codecols - 1)
            assert len(grid) > output_h
            assert len(grid[0]) > output_w

            shape_1 = _shape(grid, 1)
            shape_2 = _shape(grid, 2)
            assert shape_1 != shape_2
            assert _rotate_cw(shape_1) != shape_1
            assert _rotate_cw(shape_2) != shape_2

            start, end, code = _active_code_block(grid)
            assert end - start + 1 == n_codecols
            assert all(any(code[row][col] for row in range(2)) for col in range(n_codecols))
            assert {value for row in code for value in row if value} == {1, 2, 3, 4}
            layouts.add(tuple(tuple(row) for row in code))
            fixed_code_1 += grid[-2][start] == 1
            fixed_code_4 += grid[-1][end] == 4

    assert len(layouts) >= 24
    assert fixed_code_1 < 36
    assert fixed_code_4 < 36


def test_schedule_has_canonical_linked_support_in_every_band() -> None:
    assert callable(getattr(GEN, "strict_canonical_like", None))
    assert callable(getattr(GEN, "schedule_profile", None))
    assert tuple(GEN.SCHEDULE_PROFILES) == ("canonical", "compact", "wide", "large")

    for band in BANDS:
        profiles = [GEN.schedule_profile(123, index, band) for index in range(16)]
        assert set(profiles) == set(GEN.SCHEDULE_PROFILES)
        strict = 0
        for index in range(24):
            grid = GEN.generate(123, index, difficulty=band)
            strict += not GEN.strict_canonical_like(grid)
        assert strict >= 6


def test_rule_mirror_matches_every_canonical_example() -> None:
    assert callable(getattr(GEN, "rule_mirror", None))
    record = _canonical_record()
    for pair in record["train"] + record["test"]:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_semantic_contract_refutes_rotation_and_template_swap_rivals() -> None:
    assert callable(getattr(GEN, "lesson_identifiable", None))
    assert set(GEN.SEMANTIC_RIVALS) == {
        "ignore_rotation",
        "swap_template_families",
        "fixed_corner_decode",
    }
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "rotated_codes_are_observable",
        "template_families_are_observable",
        "code_positions_are_not_fixed",
    }
    assert GEN.WITNESS_RIVALS["code_positions_are_not_fixed"] == ["fixed_corner_decode"]

    for band in BANDS:
        demos = []
        fixed_corner_refutations = 0
        for index in range(GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(808, index, difficulty=band)
            answer = GEN.rule_mirror(grid)
            demos.append({"input": grid, "output": answer})
            assert GEN.SEMANTIC_RIVALS["ignore_rotation"](grid) != answer
            assert GEN.SEMANTIC_RIVALS["swap_template_families"](grid) != answer
            fixed_corner_refutations += (
                GEN.SEMANTIC_RIVALS["fixed_corner_decode"](grid) != answer
            )
        assert fixed_corner_refutations >= 1
        query_grid = GEN.generate(808, GEN.EXAMPLES_NEEDED, difficulty=band)
        assert GEN.lesson_identifiable(demos, {"input": query_grid}) == []
