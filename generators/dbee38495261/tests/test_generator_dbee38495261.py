"""Focused regression and semantic tests for ordered waypoint maze routing."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "dbee38495261"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.dbee38495261.generator"
)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _expected(grid):
    return gen.rule_mirror(copy.deepcopy(grid))


def test_canonical_pairs_are_accepted_and_match_rule_mirror() -> None:
    pairs = _pairs()
    assert len(pairs) == 4
    assert gen.RULE_HASH == "f1fa88aeec11"
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _expected(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "axes",
    [
        {"grid_h": 7, "grid_w": 9, "n_mids": 1},
        {"grid_h": 8, "grid_w": 10, "n_mids": 4},
        {"grid_h": 14, "grid_w": 16, "n_mids": 2},
    ],
)
def test_exact_override_boundaries_are_realized(band, axes) -> None:
    grid = gen.generate(91, 17, difficulty=band, **axes)
    assert gen.self_check(grid, meta={"overrides": axes}) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == axes
    assert 1 in {value for row in grid for value in row}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "expert"},
        {"typo_axis": 1},
        {"grid_h": 6},
        {"grid_h": 15},
        {"grid_w": 8},
        {"grid_w": 17},
        {"n_mids": 0},
        {"n_mids": 5},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"n_mids": "2"},
    ],
)
def test_invalid_calls_fail_loudly(kwargs) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, **kwargs)


def test_distribution_teaches_walls_and_waypoint_order_in_every_band() -> None:
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        seen_shapes = set()
        seen_mid_counts = set()
        seen_canonical_shape = False
        killed_reverse = False
        killed_row_major = False
        for sample_index in range(32):
            seed = 12_345 + 1000 * band_index
            grid = gen.generate(seed, sample_index, difficulty=band)
            assert grid == gen.generate(seed, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            observed = gen.observe_overrides(grid)
            seen_shapes.add((observed["grid_h"], observed["grid_w"]))
            seen_mid_counts.add(observed["n_mids"])
            seen_canonical_shape |= (observed["grid_h"], observed["grid_w"]) in {
                (7, 9), (8, 9), (8, 10)
            }
            expected = _expected(grid)
            assert gen.SEMANTIC_RIVALS["ignore walls"](copy.deepcopy(grid)) != expected
            assert (
                gen.SEMANTIC_RIVALS["connect only start to end"](
                    copy.deepcopy(grid)
                )
                != expected
            )
            killed_reverse |= (
                gen.SEMANTIC_RIVALS["visit mids in reverse numeric order"](
                    copy.deepcopy(grid)
                )
                != expected
            )
            killed_row_major |= (
                gen.SEMANTIC_RIVALS["visit mids in row-major order"](
                    copy.deepcopy(grid)
                )
                != expected
            )
        assert seen_canonical_shape, band
        assert len(seen_shapes) >= 4, band
        assert seen_mid_counts == {1, 2, 3, 4}, band
        assert killed_reverse, band
        assert killed_row_major, band


def test_declared_witnesses_and_rivals_are_executable_counterexamples() -> None:
    for n_mids in (1, 2, 3, 4):
        grid = gen.generate(
            71,
            n_mids,
            difficulty="hard",
            grid_h=11,
            grid_w=13,
            n_mids=n_mids,
        )
        expected = _expected(grid)
        assert gen.SEMANTIC_WITNESSES["wall detour"](grid)
        assert gen.SEMANTIC_WITNESSES["waypoint required"](grid)
        for witness, rivals in gen.WITNESS_RIVALS.items():
            if gen.SEMANTIC_WITNESSES[witness](grid):
                assert any(gen.SEMANTIC_RIVALS[name](grid) != expected for name in rivals)


def test_four_demo_lessons_refute_every_named_competitor() -> None:
    for band in (None, "easy", "medium", "hard"):
        lesson = []
        for sample_index in range(gen.EXAMPLES_NEEDED + 1):
            source = gen.generate(88_001, sample_index, difficulty=band)
            lesson.append({"input": source, "output": _expected(source)})
        assert gen.lesson_identifiable(lesson[:-1], lesson[-1]) == []


def test_self_check_rejects_structural_and_semantic_impostors_without_raising() -> None:
    malformed = [None, [], [[]], [[0], [0, 1]], [[False]], [[10]]]
    for grid in malformed:
        errors = gen.self_check(grid)
        assert isinstance(errors, list) and errors

    grid = gen.generate(991, 3, difficulty="hard")
    positions = {
        value: (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in (2, 3, 4, 5, 6, 7)
    }
    no_walls = copy.deepcopy(grid)
    no_walls[:] = [[0 if value == 1 else value for value in row] for row in no_walls]
    assert any("wall" in message for message in gen.self_check(no_walls))

    duplicate_start = copy.deepcopy(grid)
    zero = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
    )
    duplicate_start[zero[0]][zero[1]] = 2
    assert any("color-2" in message for message in gen.self_check(duplicate_start))

    disconnected = copy.deepcopy(grid)
    start = positions[2]
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        row, col = start[0] + dr, start[1] + dc
        if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
            disconnected[row][col] = 1
    assert any("disconnected" in message for message in gen.self_check(disconnected))


def test_global_rng_purity_and_fresh_return_values() -> None:
    random.seed(120_901)
    before = random.getstate()
    first = gen.generate(444, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(444, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 0
    assert first != second


def test_retained_wall_waypoint_counterexample_is_source_bound() -> None:
    root = find_root(__file__)
    evidence_dir = (
        root
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "review-a21b77ad9dc3e664-v0001"
    )
    assets = json.loads((evidence_dir / "audit_assets.json").read_text())
    racket = json.loads((evidence_dir / "racket.json").read_text())
    source = root / "generators" / TASK_ID / "generator.py"

    assert assets["generator_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert assets["rule_hash"] == gen.RULE_HASH
    assert assets["self_check_errors"] == []
    assert gen.self_check(assets["input"]) == []
    expected = gen.rule_mirror(copy.deepcopy(assets["input"]))
    assert expected == assets["python_rule_mirror_output"]
    assert expected == assets["racket_output"] == racket["results"][0]["output"]
    assert assets["all_declared_rivals_disagree"]
    assert set(assets["rival_outputs"]) == set(gen.LESSON_COMPETITORS)
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert rival(copy.deepcopy(assets["input"])) == assets["rival_outputs"][name]
        assert assets["rival_outputs"][name] != expected
