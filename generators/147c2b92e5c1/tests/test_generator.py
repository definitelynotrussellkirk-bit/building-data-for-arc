"""Focused regression tests for the holed-object transform curriculum."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys
from typing import Any

import pytest

# Portable bootstrap for both the review packet and staged task-test runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "147c2b92e5c1"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)

Grid = list[list[int]]


def _rectangular(grid: Any) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    )


def _components(grid: Grid) -> list[list[tuple[int, int]]]:
    """4-connected nonzero body components, ignoring the two header rows."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(2, height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                cur_row, cur_col = stack.pop()
                cells.append((cur_row, cur_col))
                for next_row, next_col in (
                    (cur_row - 1, cur_col),
                    (cur_row + 1, cur_col),
                    (cur_row, cur_col - 1),
                    (cur_row, cur_col + 1),
                ):
                    if not (2 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            result.append(sorted(cells))
    return result


def _crop_component(grid: Grid, cells: list[tuple[int, int]]) -> Grid:
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    keep = set(cells)
    return [
        [grid[row][col] if (row, col) in keep else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def _hole_count(shape: Grid) -> int:
    height, width = len(shape), len(shape[0])
    zeros = {(row, col) for row in range(height) for col in range(width) if shape[row][col] == 0}
    seen: set[tuple[int, int]] = set()
    holes = 0
    for start in sorted(zeros):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        touches_edge = False
        while stack:
            row, col = stack.pop()
            touches_edge |= row in (0, height - 1) or col in (0, width - 1)
            for next_row, next_col in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if (next_row, next_col) in zeros and (next_row, next_col) not in seen:
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
        if not touches_edge:
            holes += 1
    return holes


def _target_shape(grid: Grid) -> Grid:
    candidates = [
        _crop_component(grid, cells)
        for cells in _components(grid)
        if _hole_count(_crop_component(grid, cells)) == 1
    ]
    assert len(candidates) == 1
    return candidates[0]


def _transform(shape: Grid, code: int) -> Grid:
    if code == 1:
        return deepcopy(shape)
    if code == 2:
        return [list(row) for row in zip(*shape[::-1])]
    if code == 3:
        return [row[::-1] for row in shape[::-1]]
    if code == 4:
        return [list(row) for row in zip(*shape)][::-1]
    if code == 5:
        return [row[::-1] for row in shape]
    if code == 6:
        return shape[::-1]
    raise ValueError(code)


def _scale2(shape: Grid) -> Grid:
    output: Grid = []
    for row in shape:
        doubled = [value for value in row for _ in range(2)]
        output.extend([list(doubled), list(doubled)])
    return output


def _code(grid: Grid) -> int:
    values = [value for value in grid[0] if value != 0]
    assert len(values) == 1
    return values[0]


def _independent_rule(grid: Grid) -> Grid:
    return _scale2(_transform(_target_shape(grid), _code(grid)))


def _identity_rival(grid: Grid) -> Grid:
    return _scale2(_target_shape(grid))


def _labeled(grid: Grid) -> dict[str, Grid]:
    return {"input": grid, "output": _independent_rule(grid)}


def test_contract_metadata_is_pinned_minimal_and_current():
    assert gen.RULE_HASH == "93c771e66aca"
    assert gen.VERSION == "3.0.0"
    assert gen.EXAMPLES_NEEDED == 4
    assert not hasattr(gen, "LESSON_SCHEDULE_PERIOD")
    assert gen._FULL_CYCLE == 60
    assert gen.MIN_STRICT_FRAC == 1.0
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "transform_code",
        "palette_profile",
        "target_slot",
        "target_rank",
    }
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()


def test_canonical_pairs_are_owned_and_match_independent_oracle():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.strict_canonical_like(original) == []
        assert _independent_rule(original) == pair["output"]
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    (
        {
            "grid_h": 9,
            "grid_w": 11,
            "transform_code": 1,
            "palette_profile": "shared",
            "target_slot": "left",
            "target_rank": "largest",
        },
        {
            "grid_h": 15,
            "grid_w": 16,
            "transform_code": 6,
            "palette_profile": "distinct",
            "target_slot": "right",
            "target_rank": "middle",
        },
    ),
)
def test_every_declared_override_is_exact_observable_and_global(band, requested):
    grid = gen.generate(8128, 17, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == _independent_rule(grid)


def test_transform_code_override_realizes_all_six_authority_branches():
    outputs = []
    for code in range(1, 7):
        grid = gen.generate(
            61,
            7,
            grid_h=9,
            grid_w=11,
            transform_code=code,
            palette_profile="distinct",
            target_slot="left",
            target_rank="largest",
        )
        assert gen.observe_overrides(grid)["transform_code"] == code
        assert gen.rule_mirror(grid) == _independent_rule(grid)
        outputs.append(gen.rule_mirror(grid))
    assert len({repr(output) for output in outputs}) == 6


def test_unknown_retired_badly_typed_and_out_of_range_inputs_fail_loudly():
    bad_overrides = (
        {"typo_axis": 1},
        {"texture": "warm"},
        {"grid_h": True},
        {"grid_w": "13"},
        {"transform_code": 2.0},
        {"palette_profile": 1},
        {"target_slot": "top"},
        {"target_rank": "smallest"},
        {"grid_h": 8},
        {"grid_h": 16},
        {"grid_w": 10},
        {"grid_w": 17},
        {"transform_code": 0},
        {"transform_code": 7},
    )
    for overrides in bad_overrides:
        with pytest.raises((TypeError, ValueError)):
            gen.generate(0, 0, **overrides)
    for seed, sample_index in ((True, 0), (0, True), (1.0, 0), (0, "1"), (0, -1)):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(seed, sample_index)
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


def test_retained_seed60_identity_shortcut_is_constructively_refuted():
    lesson = [gen.generate(60, index, difficulty="easy") for index in range(5)]
    assert [_code(grid) for grid in lesson] == [1, 2, 3, 4, 5]
    assert sum(_identity_rival(grid) != _independent_rule(grid) for grid in lesson) == 4
    assert all(gen.self_check(grid) == [] for grid in lesson)


def test_every_generated_target_exposes_all_six_transforms():
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 17, 99173):
            for sample_index in range(12):
                grid = gen.generate(seed, sample_index, difficulty=band)
                shape = _target_shape(grid)
                signatures = {repr(_transform(shape, code)) for code in range(1, 7)}
                assert len(signatures) == 6


def test_default_curriculum_spans_axes_and_retains_regular_canonical_anchors():
    canonical_profiles = {
        (9, 11, 5),
        (9, 12, 4),
        (9, 12, 5),
        (10, 12, 5),
        (10, 13, 5),
    }
    for band in (None, "easy", "medium", "hard"):
        profiles = []
        for sample_index in range(gen._FULL_CYCLE):
            grid = gen.generate(0, sample_index, difficulty=band)
            assert gen.strict_canonical_like(grid) == []
            profiles.append(
                (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
            )
        assert {height for height, _, _ in profiles} == set(range(9, 16))
        assert {width for _, width, _ in profiles} == set(range(11, 17))
        assert {palette_size for _, _, palette_size in profiles} == {4, 5}
        for start in range(gen._FULL_CYCLE):
            window = [profiles[(start + offset) % gen._FULL_CYCLE] for offset in range(20)]
            assert canonical_profiles.issubset(set(window))


def test_four_demo_windows_refute_declared_semantic_rivals_for_every_query_rotation():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 60):
            for start in range(gen._FULL_CYCLE):
                lesson = [
                    _labeled(gen.generate(seed, start + offset, difficulty=band))
                    for offset in range(5)
                ]
                for query_index in range(5):
                    query = lesson[query_index]
                    demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                    assert gen.lesson_identifiable(demos, query) == []
                    for rival in gen.LESSON_COMPETITORS.values():
                        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
                        assert not (survives and rival(query["input"]) != query["output"])


def test_semantic_contracts_are_pure_and_witnessed():
    grid = gen.generate(73, 11, difficulty="hard")
    original = deepcopy(grid)
    intended = gen.rule_mirror(grid)
    assert gen.SEMANTIC_RIVALS
    assert gen.CANONICAL_SHORTCUTS == gen.SEMANTIC_RIVALS
    assert gen.LESSON_COMPETITORS == gen.SEMANTIC_RIVALS
    for rival in gen.SEMANTIC_RIVALS.values():
        result = rival(grid)
        assert _rectangular(result)
        assert grid == original
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        if witness(grid):
            assert any(
                gen.SEMANTIC_RIVALS[rival](grid) != intended
                for rival in gen.WITNESS_RIVALS[witness_name]
            )


def test_self_check_rejects_destructive_mutations_and_minimal_impostors():
    grid = gen.generate(71, 2, difficulty="medium")
    assert gen.self_check(grid) == []

    no_code = deepcopy(grid)
    no_code[0] = [0] * len(no_code[0])

    occupied_separator = deepcopy(grid)
    occupied_separator[1][0] = 3

    opened_hole = deepcopy(grid)
    target = next(
        cells
        for cells in _components(grid)
        if _hole_count(_crop_component(grid, cells)) == 1
    )
    top = min(row for row, _ in target)
    left = min(col for _, col in target)
    shape = _crop_component(grid, target)
    hole = next(
        (row, col)
        for row in range(1, len(shape) - 1)
        for col in range(1, len(shape[0]) - 1)
        if shape[row][col] == 0
    )
    # Remove one orthogonally adjacent target cell, opening the enclosed hole.
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = hole[0] + dr, hole[1] + dc
        if shape[rr][cc] != 0:
            opened_hole[top + rr][left + cc] = 0
            break

    extra_component = deepcopy(grid)
    extra_component[-1][-1] = 9

    impostors = [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 11 for _ in range(9)],
        [[0] * 11 for _ in range(9)],
        no_code,
        occupied_separator,
        opened_hole,
        extra_component,
    ]
    assert all(gen.self_check(candidate) for candidate in impostors)
