"""Focused input-grammar checks; protected Racket labels are audited separately."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
SOURCE = HOME / "generator.py"


def test_module_exists():
    assert SOURCE.is_file(), "the assigned public family needs a portable generator.py"


@pytest.fixture(scope="module")
def module():
    spec = importlib.util.spec_from_file_location("public_eval_58f5dbd5_generator_tests", SOURCE)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _transform(grid, turn, reflect=False):
    result = [row[::-1] if reflect else row[:] for row in grid]
    for _ in range(turn):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _components(mask, diagonal=False):
    left = {(r, c) for r, row in enumerate(mask) for c, value in enumerate(row) if value}
    result = []
    steps = [(r, c) for r in (-1, 0, 1) for c in (-1, 0, 1)
             if (r or c) and (diagonal or abs(r) + abs(c) == 1)]
    while left:
        stack = [left.pop()]
        group = set(stack)
        while stack:
            r, c = stack.pop()
            for dr, dc in steps:
                point = r + dr, c + dc
                if point in left:
                    left.remove(point)
                    group.add(point)
                    stack.append(point)
        result.append(group)
    return result


def _render_canonical(parsed):
    r0, c0, r1, c1 = parsed["crop"]
    bg = parsed["background"]
    output = [[bg] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for target in parsed["targets"]:
        tr0, tc0, tr1, tc1 = target["bbox"]
        for r in range(tr0, tr1 + 1):
            for c in range(tc0, tc1 + 1):
                output[r - r0][c - c0] = target["color"]
        for r, row in enumerate(target["mask"]):
            for c, occupied in enumerate(row):
                if occupied:
                    output[tr0 + 1 + r - r0][tc0 + 1 + c - c0] = bg
    return output


def test_exact_original_labels_and_input_preservation(module):
    raw = ROOT / "shared/data/raw"
    parent = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["58f5dbd5"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["58f5dbd5"]
    pairs = parent["train"] + [dict(pair, output=gold[i]) for i, pair in enumerate(parent["test"])]
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        parsed = module.analyze(pair["input"])
        assert _render_canonical(parsed) == pair["output"]
        assert pair["input"] == before
        assert module.self_check(pair["input"]) == []


@pytest.mark.parametrize("seed", [0, 9, 17, 43, 2**63 - 1])
def test_ten_profiles_are_distinct_and_grammar_valid(module, seed):
    grids = [module.generate(seed, index) for index in range(10)]
    assert len({_freeze(grid) for grid in grids}) == 10
    counts = [4, 3, 1, 2, 5, 6, 2, 4, 1, 7]
    for index, grid in enumerate(grids):
        assert grid == module.generate(seed, index)
        assert module.self_check(grid) == []
        parsed = module.analyze(grid)
        assert len(parsed["targets"]) == counts[index]
        assert 1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30
        assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
        assert parsed["targets"] == sorted(parsed["targets"], key=lambda item: item["bbox"][:2])
        assert set(parsed) == {"background", "targets", "crop"}
    assert len(grids[9]) == len(grids[9][0]) == 30
    assert len({value for row in grids[9] for value in row}) == 10
    tall_output = _render_canonical(module.analyze(grids[7]))
    assert max(len(tall_output), len(tall_output[0])) >= 20


@pytest.mark.parametrize("seed", [0, 9, 17, 43, 2**63 - 1])
def test_first_two_demonstrations_bind_by_color_and_teach_orientation(module, seed):
    for index in (0, 1):
        parsed = module.analyze(module.generate(seed, index))
        targets = parsed["targets"]
        row_order = tuple(item["color"] for item in targets)
        col_order = tuple(item["color"] for item in sorted(targets, key=lambda item: (item["bbox"][1], item["bbox"][0])))
        template_row = tuple(item["color"] for item in sorted(targets, key=lambda item: item["template_bbox"][:2]))
        template_col = tuple(item["color"] for item in sorted(targets, key=lambda item: (item["template_bbox"][1], item["template_bbox"][0])))
        assert row_order != col_order
        assert template_row not in (row_order, col_order)
        assert template_col not in (row_order, col_order)
        assert row_order not in (tuple(sorted(row_order)), tuple(sorted(row_order, reverse=True)))
        assert len({_freeze(item["mask"]) for item in targets}) == len(targets)
        assert any(len(_components(item["mask"], diagonal=True)) > 1 for item in targets)
        for item in targets:
            mask = item["mask"]
            assert all(type(value) is bool for row in mask for value in row)
            assert _freeze(mask) != _freeze(_transform(mask, 2))
            assert _freeze(mask) != _freeze(_transform(mask, 0, True))
            assert _freeze(mask) != _freeze(_transform(mask, 2, True))
            if len(mask) == len(mask[0]):
                for turn in range(4):
                    for reflect in (False, True):
                        if turn or reflect:
                            assert _freeze(mask) != _freeze(_transform(mask, turn, reflect))


def test_decoy_override_is_exact_observable_and_does_not_change_core(module):
    for seed in (0, 9, 17, 43, 2**63 - 1):
        for index in range(10):
            grids = [module.generate(seed, index, decoy_count=count) for count in range(3)]
            base = module.analyze(grids[0])
            core_colors = {base["background"]} | {item["color"] for item in base["targets"]}
            for count, grid in enumerate(grids):
                assert module.observe_overrides(grid) == {"decoy_count": count}
                assert module.analyze(grid) == base
                without_decoys = [[value if value in core_colors else base["background"] for value in row] for row in grid]
                assert without_decoys == grids[0]


def test_override_is_recorded_by_real_generator_context(module):
    from puzzle_generators.base import set_ctx_observer

    contexts = []
    set_ctx_observer(contexts.append)
    try:
        for value in (0, 2):
            module.generate(17, 0, decoy_count=value)
            assert contexts[-1].axis_value("decoy_count") == value
            assert contexts[-1].overrides_used() == {"decoy_count": value}
    finally:
        set_ctx_observer(None)


@pytest.mark.parametrize("name", ["seed", "sample_index"])
@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, -1, 2**63])
def test_strict_integer_request_validation(module, name, bad):
    values = {"seed": 0, "sample_index": 0, name: bad}
    with pytest.raises((TypeError, ValueError)):
        module.generate(**values)


@pytest.mark.parametrize("bad", [True, False, 0, 0.5, "", "easiest", [], {}])
def test_strict_difficulty_validation(module, bad):
    with pytest.raises((TypeError, ValueError)):
        module.generate(0, difficulty=bad)


@pytest.mark.parametrize("bad", [True, False, 0.0, "0", None, -1, 3, [], {}])
def test_strict_override_validation(module, bad):
    with pytest.raises((TypeError, ValueError)):
        module.generate(0, decoy_count=bad)


def test_unknown_override_and_large_valid_index(module):
    with pytest.raises((TypeError, ValueError)):
        module.generate(0, typo_decoy_count=1)
    assert module.self_check(module.generate(2**63 - 1, 2**63 - 1)) == []
    assert module.generate(17) == module.generate(17, 0)


@pytest.mark.parametrize("bad", [None, (), [], [[]], [[0], [0, 0]], [[True]], [[0.0]], [["0"]], [[-1]], [[10]], [[0] * 31], [[0]] * 31])
def test_analyzer_rejects_malformed_grids(module, bad):
    with pytest.raises((TypeError, ValueError)):
        module.analyze(bad)
    assert module.self_check(bad)


def test_analyzer_checks_border_and_clean_target_crop(module):
    grid = module.generate(17, 8, decoy_count=0)
    broken = copy.deepcopy(grid)
    broken[0][0] = (broken[0][0] + 1) % 10
    with pytest.raises(ValueError):
        module.analyze(broken)
    broken = copy.deepcopy(grid)
    parsed = module.analyze(grid)
    r0, c0, r1, c1 = parsed["targets"][0]["bbox"]
    broken[r0 + 1][c0 + 1] = parsed["background"]
    with pytest.raises(ValueError):
        module.analyze(broken)
    broken = copy.deepcopy(grid)
    cr0, cc0, cr1, cc1 = parsed["crop"]
    candidates = [(r, c) for r in range(cr0, cr1 + 1) for c in range(cc0, cc1 + 1)
                  if 0 < r < len(grid) - 1 and 0 < c < len(grid[0]) - 1 and grid[r][c] == parsed["background"]]
    assert candidates
    r, c = candidates[0]
    unused = next(color for color in range(10) if color not in {value for row in grid for value in row})
    broken[r][c] = unused
    with pytest.raises(ValueError):
        module.analyze(broken)


def test_full_rectangle_template_remains_a_template(module):
    grid = [[0] * 15 for _ in range(9)]
    for r in range(1, 7):
        for c in range(1, 7):
            grid[r][c] = 2
    for r in range(2, 6):
        for c in range(10, 14):
            grid[r][c] = 2
    parsed = module.analyze(grid)
    assert parsed["targets"][0]["bbox"] == [1, 1, 6, 6]
    assert parsed["targets"][0]["mask"] == [[True] * 4 for _ in range(4)]


def test_bounded_sampling_covers_palette_topology_sizes_and_difficulty(module):
    backgrounds = set()
    shapes = set()
    counts = set()
    for seed in range(96):
        for index in range(10):
            grid = module.generate(seed, index, difficulty=(None, "easy", "medium", "hard")[seed % 4])
            assert module.self_check(grid) == []
            parsed = module.analyze(grid)
            backgrounds.add(parsed["background"])
            shapes.add((len(grid), len(grid[0])))
            counts.add(len(parsed["targets"]))
    assert backgrounds == set(range(10))
    assert counts == set(range(1, 8))
    assert len(shapes) >= 20
    assert (30, 30) in shapes


def test_analysis_is_equivariant_under_d4_and_palette_permutation(module):
    grid = module.generate(43, 6)
    canonical = _render_canonical(module.analyze(grid))
    palette = [7, 2, 8, 0, 9, 5, 3, 1, 6, 4]
    for turn in range(4):
        for reflect in (False, True):
            changed = [[palette[value] for value in row] for row in _transform(grid, turn, reflect)]
            expected = [[palette[value] for value in row] for row in _transform(canonical, turn, reflect)]
            assert _render_canonical(module.analyze(changed)) == expected
