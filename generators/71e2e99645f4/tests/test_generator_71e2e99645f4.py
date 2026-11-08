"""Focused regressions for the reviewed 71e2e99645f4 generator."""
from __future__ import annotations

import copy
import importlib.util
import os
from itertools import combinations
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "71e2e99645f4"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))

PATTERN_HOLES = {
    "no_hole": frozenset(),
    "center_hole": frozenset({(1, 1), (1, 2), (2, 1), (2, 2)}),
    "bottom_hole": frozenset({(2, 1), (2, 2), (3, 1), (3, 2)}),
    "edge_hole": frozenset({(1, 0), (1, 3), (2, 0), (2, 3)}),
}


def _section_holes(grid, section_index: int) -> frozenset[tuple[int, int]]:
    start = section_index * 5
    return frozenset(
        (row, col)
        for row in range(4)
        for col in range(4)
        if grid[row][start + col] == 0
    )


def _lesson(seed: int, start: int, difficulty: str = "medium"):
    grids = [GEN.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
    return [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]


def test_rule_pin_and_canonical_pairs_match_the_authority() -> None:
    assert GEN.RULE_HASH == "d38a7d9b0fc4"
    assert len(PAIRS) == 5
    catalog = Catalog(find_root(__file__))
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original

        result = catalog.apply(TASK_ID, [pair["input"]])
        assert result["rule_hash_matches_catalog"] is True
        assert result["executed_rule_hash"] == GEN.RULE_HASH
        assert result["results"][0]["error"] is None
        assert result["results"][0]["output"] == pair["output"]


def test_exact_overrides_round_trip_in_every_band() -> None:
    requested_patterns = ["edge_hole", "bottom_hole", "center_hole"]
    for band in (None, "easy", "medium", "hard"):
        grid = GEN.generate(
            1701,
            23,
            difficulty=band,
            fill_color=7,
            hole_patterns=requested_patterns,
        )
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.observe_overrides(grid) == {
            "fill_color": 7,
            "hole_patterns": requested_patterns,
        }
        assert [_section_holes(grid, index) for index in range(3)] == [
            PATTERN_HOLES[name] for name in requested_patterns
        ]
        assert grid == GEN.generate(
            1701,
            23,
            difficulty=band,
            fill_color=7,
            hole_patterns=requested_patterns,
        )


def test_edge_hole_is_the_canonical_four_cell_middle_edge_pattern() -> None:
    grid = GEN.generate(
        9,
        4,
        fill_color=6,
        hole_patterns=["edge_hole", "no_hole", "center_hole"],
    )
    assert _section_holes(grid, 0) == PATTERN_HOLES["edge_hole"]
    assert grid[0][0] == grid[0][3] == grid[3][0] == grid[3][3] == 6
    assert GEN.rule_mirror(grid)[0] == [3, 3, 3]


def test_unknown_and_invalid_controls_fail_closed() -> None:
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(0, 0, typo_axis=3)

    for invalid in (True, 7.0, "7", 0, 10):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, fill_color=invalid)

    invalid_pattern_lists = (
        "edge_hole",
        ("edge_hole", "no_hole", "center_hole"),
        [],
        ["edge_hole", "no_hole"],
        ["edge_hole", "no_hole", "center_hole", "bottom_hole"],
        ["edge_hole", "no_hole", 3],
        ["edge_hole", "no_hole", "diagonal_hole"],
    )
    for invalid in invalid_pattern_lists:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, hole_patterns=invalid)

    for invalid_seed in (True, 1.5, "1"):
        with pytest.raises(TypeError, match="seed"):
            GEN.generate(invalid_seed, 0)
    for invalid_index in (True, -1, 1.5, "1"):
        with pytest.raises((TypeError, ValueError), match="sample_index"):
            GEN.generate(0, invalid_index)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[1]],
        [[0], [0, 1]],
        [[True] * 14 for _ in range(4)],
        [[10] * 14 for _ in range(4)],
    ],
)
def test_self_check_rejects_malformed_and_minimal_impostor_grids(grid) -> None:
    assert GEN.self_check(grid, meta={"texture": "no_holes"})


def test_self_check_rejects_invalid_dividers_fill_and_old_edge_geometry() -> None:
    good = GEN.generate(
        22,
        5,
        fill_color=4,
        hole_patterns=["edge_hole", "no_hole", "bottom_hole"],
    )

    bad_divider = copy.deepcopy(good)
    bad_divider[0][4] = 4
    assert GEN.self_check(bad_divider)

    mixed_fill = copy.deepcopy(good)
    mixed_fill[0][0] = 7
    assert GEN.self_check(mixed_fill)

    old_edge = copy.deepcopy(good)
    for row in (0, 3):
        old_edge[row][0] = 0
        old_edge[row][3] = 0
    assert GEN.self_check(old_edge)


def test_default_schedule_is_deterministic_lawful_and_covers_all_classes() -> None:
    all_patterns: set[str] = set()
    for band in (None, "easy", "medium", "hard"):
        band_signatures = []
        for index in range(12):
            grid = GEN.generate(2400, index, difficulty=band)
            assert grid == GEN.generate(2400, index, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            observed = GEN.observe_overrides(grid)
            assert "no_hole" in observed["hole_patterns"]
            assert len(set(observed["hole_patterns"])) == 3
            all_patterns.update(observed["hole_patterns"])
            band_signatures.append(tuple(observed["hole_patterns"]))
        assert len(set(band_signatures)) >= 3
    assert all_patterns == set(PATTERN_HOLES)

    same_draw = {
        tuple(GEN.observe_overrides(GEN.generate(421, 8, difficulty=band))["hole_patterns"])
        for band in ("easy", "medium", "hard")
    }
    assert len(same_draw) >= 2


def test_default_curriculum_windows_refute_every_declared_rival() -> None:
    assert set(GEN.LESSON_COMPETITORS) == {
        "full_edge_columns",
        "four_zeros_means_center",
        "canonical_position_lookup",
    }
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = _lesson(8123 + start, start, band)
            assert GEN.lesson_identifiable(lesson[:3], lesson[3]) == []
            for demo_indices in combinations(range(4), 3):
                query_index = next(index for index in range(4) if index not in demo_indices)
                demos = [lesson[index] for index in demo_indices]
                assert GEN.lesson_identifiable(demos, lesson[query_index]) == []


def test_semantic_witnesses_fire_and_rivals_disagree_on_their_targets() -> None:
    expected = {
        "canonical_edge_geometry",
        "vertical_position_matters",
        "position_generalization",
    }
    fired: set[str] = set()
    for index in range(6):
        grid = GEN.generate(19001, index, difficulty="medium")
        output = GEN.rule_mirror(grid)
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                fired.add(name)
        for name, rival in GEN.LESSON_COMPETITORS.items():
            if name == "full_edge_columns" and "edge_hole" in GEN.observe_overrides(grid)["hole_patterns"]:
                assert rival(grid) != output
            if name == "four_zeros_means_center" and "bottom_hole" in GEN.observe_overrides(grid)["hole_patterns"]:
                assert rival(grid) != output
    assert fired == expected


def test_default_paths_record_both_exact_axes(monkeypatch) -> None:
    captured = {}
    real_gen_ctx = GEN.gen_ctx

    def tracking_gen_ctx(**kwargs):
        ctx = real_gen_ctx(**kwargs)
        captured["ctx"] = ctx
        return ctx

    monkeypatch.setattr(GEN, "gen_ctx", tracking_gen_ctx)
    grid = GEN.generate(23311, 5, difficulty="medium")
    draws = captured["ctx"].recorded_draws()
    observed = GEN.observe_overrides(grid)
    assert set(GEN.AXES) == {"fill_color", "hole_patterns"}
    assert draws["fill_color"] == observed["fill_color"]
    assert draws["hole_patterns"] == observed["hole_patterns"]
