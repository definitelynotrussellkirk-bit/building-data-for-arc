"""Focused semantic and regression tests for generator 99d71aabd753."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "99d71aabd753"
ROOT = find_root(__file__)
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.99d71aabd753.generator"
)
AUTHORITY = canonical_path(ROOT).parents[1] / "base/solutions/training/2753e76c__99d71aabd753.json"


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _manual_gap_impostor() -> list[list[int]]:
    grid = [[0] * 10 for _ in range(10)]
    grid[1][1] = 1
    grid[2][2] = 2  # diagonal contact with color 1
    grid[7][7] = 2
    return grid


def _manual_tie_impostor() -> list[list[int]]:
    grid = [[0] * 10 for _ in range(10)]
    for row, col in ((1, 1), (1, 7)):
        grid[row][col] = 1
    for row, col in ((7, 1), (7, 7)):
        grid[row][col] = 2
    return grid


def _nonrectangle_impostor() -> list[list[int]]:
    grid = GEN.generate(991, 17, difficulty="medium")
    components = GEN._components_by_color(grid)
    component = next(
        component
        for groups in components.values()
        for component in groups
        if len(component) >= 4
    )
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    corner = (min(rows), min(cols))
    if corner not in component:
        corner = next(iter(component))
    broken = copy.deepcopy(grid)
    broken[corner[0]][corner[1]] = 0
    return broken


def test_metadata_and_active_source_sync() -> None:
    row = _canonical_row()
    source = row["program_solution"]
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == _normalized_hash(source) == "a6f4f8240a92"
    assert _normalized_hash(authority["racket_target"]["target_code"]) == _normalized_hash(source)
    # raw_code is explicitly preserved as archival executable source.
    assert authority["racket_target"]["raw_code"] != source


def test_all_canonical_inputs_are_accepted_and_python_mirror_matches() -> None:
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._chart_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_default_semantics_and_branch_support_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        witness_counts = Counter()
        inputs: set[tuple[tuple[int, ...], ...]] = set()
        outputs: set[tuple[tuple[int, ...], ...]] = set()
        for seed in range(80):
            grid = GEN.generate(seed, seed * 17 + 3, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert GEN._ordinary_semantics_hold(grid)
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, GEN._chart_output(grid))))
            witness_counts.update(
                name
                for name, predicate in GEN.SEMANTIC_WITNESSES.items()
                if predicate(grid)
            )
        assert len(inputs) >= 78
        assert len(outputs) >= 45
        assert set(witness_counts) == set(GEN.SEMANTIC_WITNESSES)
        assert witness_counts["cell_count_ranking_conflicts"] == 80
        assert witness_counts["first_seen_order_conflicts"] == 80
        assert witness_counts["mixed_rectangle_areas"] == 80


def _rank_step_chart(grid: list[list[int]]) -> list[list[int]]:
    """Rival that learns rank plus maximum, then assumes lengths step by one."""
    counts = GEN._component_counts(grid)
    colors = sorted(counts, key=counts.get, reverse=True)
    width = max(counts.values())
    return [
        [0] * rank + [color] * (width - rank)
        for rank, color in enumerate(colors)
    ]


def test_every_ordinary_band_breaks_the_rank_step_shortcut() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(60):
            grid = GEN.generate(7000 + seed, seed * 31 + 9, difficulty=band)
            descending = sorted(GEN._component_counts(grid).values(), reverse=True)
            assert any(upper - lower > 1 for upper, lower in zip(descending, descending[1:]))
            assert _rank_step_chart(grid) != GEN._chart_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 10},
        {"grid_h": 22},
        {"grid_w": 10},
        {"grid_w": 22},
    ],
)
def test_dimension_only_overrides_do_not_reenable_rank_step_shortcut(
    overrides: dict[str, int],
) -> None:
    """Unrelated exact axes must not weaken the count teaching invariant."""
    for band in ("easy", "medium", "hard"):
        for offset in range(60):
            grid = GEN.generate(9000 + offset, offset * 37 + 5, difficulty=band, **overrides)
            descending = sorted(GEN._component_counts(grid).values(), reverse=True)
            assert any(upper - lower > 1 for upper, lower in zip(descending, descending[1:]))
            assert _rank_step_chart(grid) != GEN._chart_output(grid)


def test_default_keyed_draws_equal_returned_observables() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(seed, seed + 101, difficulty=band)
            finally:
                set_ctx_observer(None)
            assert captured
            drawn = captured[-1].recorded_draws()
            observed = GEN.observe_overrides(grid)
            assert drawn["grid_h"] == len(grid)
            assert drawn["grid_w"] == len(grid[0])
            assert drawn["n_colors"] == observed["n_colors"]
            assert drawn["max_count"] == observed["max_count"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 10},
        {"grid_h": 22},
        {"grid_w": 10},
        {"grid_w": 22},
        {"n_colors": 2},
        {"n_colors": 5},
        {"max_count": 2},
        {"max_count": 7},
        {"grid_h": 10, "grid_w": 10},
        {"n_colors": 5, "max_count": 7},
        {"grid_h": 10, "grid_w": 10, "n_colors": 5, "max_count": 7},
    ],
)
def test_boundary_overrides_are_exact(overrides: dict[str, int]) -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(4):
            grid = GEN.generate(seed, seed + 7, difficulty=band, **overrides)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            if "grid_h" in overrides:
                assert len(grid) == overrides["grid_h"]
            if "grid_w" in overrides:
                assert len(grid[0]) == overrides["grid_w"]
            for axis in ("n_colors", "max_count"):
                if axis in overrides:
                    assert observed[axis] == overrides[axis]


def test_incompatible_and_unknown_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        GEN.generate(1, 2, n_colors=5, max_count=2)
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, texture="same_shape")


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(20260724)
    state = random.getstate()
    first = GEN.generate(737, 19, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(737, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    second[0][0] = (second[0][0] + 1) % 10
    assert first != second


def test_self_check_rejects_targeted_structural_impostors() -> None:
    valid = GEN.generate(71, 13, difficulty="easy")
    all_background = [[0 for _ in row] for row in valid]
    ragged = copy.deepcopy(valid)
    ragged[0].pop()
    impostors = {
        "all_background": all_background,
        "ragged": ragged,
        "tied_component_counts": _manual_tie_impostor(),
        "nonrectangular_component": _nonrectangle_impostor(),
        "missing_object_gap": _manual_gap_impostor(),
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_is_distribution_invalid_but_oracle_defined() -> None:
    # The replacement feature is an L-shaped component, absent from every
    # remaining object (all remaining components are solid rectangles).
    impostor = _nonrectangle_impostor()
    assert GEN.self_check(impostor)
    output = GEN._chart_output(impostor)
    assert output
    assert all(isinstance(row, list) and row for row in output)


def test_generated_lesson_rebuts_named_shortcuts() -> None:
    grids = [GEN.generate(500 + i, i, difficulty="medium") for i in range(4)]
    pairs = [{"input": grid, "output": GEN._chart_output(grid)} for grid in grids]
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
    for grid in grids:
        official = GEN._chart_output(grid)
        assert GEN._CANDIDATE_RULES["count_cells"](grid) != official
        assert GEN._CANDIDATE_RULES["sort_first_seen"](grid) != official
        assert GEN._CANDIDATE_RULES["left_align"](grid) != official
