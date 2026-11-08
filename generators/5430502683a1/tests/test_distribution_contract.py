"""Portable black-box regressions for the longest endpoint-span contract.

The geometric oracle reads only occupied cells. Canonical labels independently
check that oracle; production-label and lesson-census evidence still comes from
the unchanged Racket authority, not from this test implementation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import importlib.util
from itertools import product
from math import gcd
from pathlib import Path
import sys

import pytest


def _add_local_runtime_to_path():
    for ancestor in Path(__file__).resolve().parents:
        for candidate in (ancestor, ancestor / "shared" / "runtime"):
            if (candidate / "reviewer_support.py").is_file():
                sys.path.insert(0, str(candidate))
                return
    raise ImportError("No reviewer_support runtime in this test's own tree")


_add_local_runtime_to_path()
from reviewer_support import canonical_pairs, find_root


TASK_ID = "5430502683a1"
ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ) if path.is_file()
)
_spec = importlib.util.spec_from_file_location("endpoint_span_contract_generator", GENERATOR_PATH)
generator = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = generator
_spec.loader.exec_module(generator)

DIFFICULTIES = (None, "easy", "medium", "hard")
DOMAINS = {"grid_h": range(8, 17), "grid_w": range(9, 19), "pair_count": range(2, 5)}
BASE_OVERRIDES = {"grid_h": 10, "grid_w": 11, "pair_count": 3}
CANONICAL_PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
REQUIRED_RIVALS = (
    "longest_euclidean", "longest_manhattan", "prefer_diagonal",
    "lowest_color", "highest_color", "first_in_scan", "last_in_scan",
)


def _input(height, width, pairs):
    grid = [[0] * width for _ in range(height)]
    for color, endpoints in pairs.items():
        for row, column in endpoints:
            assert grid[row][column] == 0, "test endpoints overlap"
            grid[row][column] = color
    return grid


def _oracle(grid):
    """Use lattice-point counts, without importing generator span helpers."""
    assert isinstance(grid, list) and 1 <= len(grid) <= 30
    assert all(isinstance(row, list) and row for row in grid)
    height, width = len(grid), len(grid[0])
    assert 1 <= width <= 30
    assert all(len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    assert any(value == 0 for row in grid for value in row), "background 0 must be present"

    cells = defaultdict(list)
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color:
                cells[color].append((row, column))
    assert 2 <= len(cells) <= 4
    assert all(len(endpoints) == 2 for endpoints in cells.values())

    pairs = {}
    for color, ((ar, ac), (br, bc)) in cells.items():
        dr, dc = br - ar, bc - ac
        assert dr == 0 or dc == 0 or abs(dr) == abs(dc), "unaligned endpoints"
        steps = gcd(abs(dr), abs(dc))
        assert steps > 0
        line = tuple((ar + i * (dr // steps), ac + i * (dc // steps)) for i in range(steps + 1))
        assert line[-1] == (br, bc)
        assert all(0 <= r < height and 0 <= c < width for r, c in line)
        orientation = "horizontal" if dr == 0 else "vertical" if dc == 0 else "diagonal"
        pairs[color] = {
            "line": line, "length": len(line), "orientation": orientation,
            "euclidean_squared": dr * dr + dc * dc,
            "manhattan": abs(dr) + abs(dc),
        }
    longest = max(pair["length"] for pair in pairs.values())
    winners = [color for color, pair in pairs.items() if pair["length"] == longest]
    assert len(winners) == 1, "the longest span must be unique"
    winner = winners[0]
    colors = sorted(pairs)
    role = "low" if winner == colors[0] else "high" if winner == colors[-1] else "interior"
    return {"grid_h": height, "grid_w": width, "pair_count": len(pairs),
            "pairs": pairs, "winner": winner, "role": role}


def _paint(observed, color):
    output = [[0] * observed["grid_w"] for _ in range(observed["grid_h"])]
    for row, column in observed["pairs"][color]["line"]:
        output[row][column] = 8
    return output


def _assert_generated_contract(grid):
    observed = _oracle(grid)
    assert observed["grid_h"] in DOMAINS["grid_h"]
    assert observed["grid_w"] in DOMAINS["grid_w"]
    assert observed["pair_count"] in DOMAINS["pair_count"]
    assert generator.self_check(grid) == []
    return observed


def _axes(observed):
    return {axis: observed[axis] for axis in DOMAINS}


def test_public_schema_matches_the_supported_exact_controls():
    assert set(generator.AXES) == set(DOMAINS)
    for axis, values in DOMAINS.items():
        assert generator.AXES[axis]["type"] == "int"
        assert generator.AXES[axis]["valid"] == f"{min(values)}..{max(values)}"
    assert generator.VERSION != "3.1.1", "a changed distribution needs a new version"
    assert generator.EXAMPLES_NEEDED == 7


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("axis,value", [(axis, value) for axis, values in DOMAINS.items() for value in values])
def test_each_exact_axis_value_works_in_every_band_and_orientation(difficulty, axis, value):
    overrides = {**BASE_OVERRIDES, axis: value}
    for sample_index in (0, 1):
        grid = generator.generate(73, sample_index, difficulty=difficulty, **overrides)
        assert _axes(_assert_generated_contract(grid)) == overrides


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("height,width,pair_count", list(product((8, 16), (9, 18), (2, 4))))
def test_joint_exact_axis_boundaries_work_through_a_complete_cycle(difficulty, height, width, pair_count):
    overrides = {"grid_h": height, "grid_w": width, "pair_count": pair_count}
    for sample_index in range(8):
        grid = generator.generate(771, sample_index, difficulty=difficulty, **overrides)
        assert _axes(_assert_generated_contract(grid)) == overrides


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_default_support_retains_canonical_shapes_and_geometric_variety(difficulty):
    profiles, counts, orientations, lengths, colors = set(), set(), set(), set(), set()
    for seed, sample_index in product(range(32), range(8)):
        grid = generator.generate(seed, sample_index, difficulty=difficulty)
        observed = _assert_generated_contract(grid)
        profiles.add((observed["grid_h"], observed["grid_w"], observed["pair_count"]))
        counts.add(observed["pair_count"])
        winner = observed["pairs"][observed["winner"]]
        orientations.add(winner["orientation"])
        lengths.add(winner["length"])
        colors.add(observed["winner"])
    assert {(10, 10, 3), (9, 11, 3)} <= profiles
    assert counts == {2, 3, 4}
    assert orientations == {"horizontal", "vertical", "diagonal"}
    assert len(lengths) >= 3
    assert 8 in colors, "the output color must also sometimes be a winning input color"
    assert len(profiles) >= 8, "canonical-shaped examples must coexist with broader canvases"


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("start", range(8))
@pytest.mark.parametrize("pair_count", (None, 2, 3, 4), ids=("default_pairs", "two_pairs", "three_pairs", "four_pairs"))
def test_eight_draw_windows_keep_geometric_counterexamples_after_any_holdout(difficulty, start, pair_count):
    for seed in (0, 29, 773):
        overrides = {} if pair_count is None else {"pair_count": pair_count}
        observed = [_assert_generated_contract(generator.generate(seed, start + offset, difficulty=difficulty, **overrides))
                    for offset in range(8)]
        if pair_count is not None:
            assert all(item["pair_count"] == pair_count for item in observed)
        axis_winners, metric_witnesses = [], []
        for item in observed:
            winner = item["pairs"][item["winner"]]
            is_axis = winner["orientation"] != "diagonal"
            axis_winners.append(is_axis)
            metric_witnesses.append(is_axis and any(
                    rival["orientation"] == "diagonal"
                    and rival["length"] < winner["length"]
                    and rival["euclidean_squared"] > winner["euclidean_squared"]
                    and rival["manhattan"] > winner["manhattan"]
                    for rival in item["pairs"].values()
                ))
        assert 4 <= sum(axis_winners) <= 6
        assert sum(metric_witnesses) >= 4, "both repeated gap profiles must refute geometric distance"
        roles = Counter(item["role"] for item in observed)
        has_interior_rank = all(item["pair_count"] >= 3 for item in observed)
        if has_interior_rank:
            assert roles == {"low": 2, "interior": 4, "high": 2}
        else:
            # Two colors have only the low and high ranks. Both need repeated
            # support, so neither rank disappears when one pair is held out.
            assert roles["low"] >= 2 and roles["high"] >= 2
        winners = Counter(item["winner"] for item in observed)
        assert set(winners) == set(observed[0]["pairs"])
        assert min(winners.values()) >= 2, "every input color must win more than once"
        for held_out in range(8):
            remaining = [item for index, item in enumerate(observed) if index != held_out]
            expected_roles = {"low", "interior", "high"} if has_interior_rank else {"low", "high"}
            assert expected_roles <= {item["role"] for item in remaining}
            assert sum(metric for index, metric in enumerate(metric_witnesses) if index != held_out) >= 3
            assert sum(not axis for index, axis in enumerate(axis_winners) if index != held_out) >= 1


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_generation_is_deterministic_and_none_means_no_override(difficulty):
    for sample_index in (0, 1, 5):
        expected = generator.generate(29, sample_index, difficulty=difficulty)
        generator.generate(900, sample_index + 7, difficulty=difficulty, **BASE_OVERRIDES)
        assert generator.generate(29, sample_index, difficulty=difficulty) == expected
        for override in ({axis: None for axis in DOMAINS}, *({axis: None} for axis in DOMAINS)):
            assert generator.generate(29, sample_index, difficulty=difficulty, **override) == expected
        assert generator.generate(29, sample_index, difficulty=difficulty, **BASE_OVERRIDES) == generator.generate(
            29, sample_index, difficulty=difficulty, **dict(reversed(list(BASE_OVERRIDES.items())))
        )


@pytest.mark.parametrize("axis", tuple(DOMAINS))
@pytest.mark.parametrize("kind", ("true", "false", "float", "fraction", "string", "list", "dict"))
def test_exact_integer_axes_reject_coercion(axis, kind):
    value = BASE_OVERRIDES[axis]
    invalid = {"true": True, "false": False, "float": float(value), "fraction": value + 0.25,
               "string": str(value), "list": [value], "dict": {"value": value}}[kind]
    with pytest.raises(ValueError):
        generator.generate(29, 1, **{axis: invalid})


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("axis,value", [(axis, value) for axis, values in DOMAINS.items()
                                         for value in (min(values) - 1, max(values) + 1)])
def test_out_of_domain_exact_values_fail_explicitly(difficulty, axis, value):
    with pytest.raises(ValueError):
        generator.generate(29, 1, difficulty=difficulty, **{axis: value})


@pytest.mark.parametrize("axis,value", (
    ("unknown_axis", 3), ("grid_height", 10), ("paircount", 3),
    ("palette_kind", "warm"), ("anchor_corner", True), ("asymmetry_force", True),
    ("palette_size", 3), ("n_distinct_colors", 3),
    ("texture", "no_pairs"), ("texture", "single_pair"), ("texture", "full_grid"),
    ("unknown_axis", None), ("texture", None),
))
def test_unknown_and_removed_override_names_fail_explicitly(axis, value):
    with pytest.raises(ValueError):
        generator.generate(29, 1, **{axis: value})


def _metric_counterexample():
    # Horizontal span: 7 cells, Euclidean distance 6. Diagonal span: 6 cells,
    # Euclidean distance sqrt(50), Manhattan distance 10. Color 4 is interior.
    return _input(8, 10, {4: ((0, 0), (0, 6)), 2: ((1, 1), (6, 6)), 7: ((2, 9), (4, 9))})


def _valid_boundary_inputs():
    return [
        ("one_row", _input(1, 5, {8: ((0, 0), (0, 4)), 2: ((0, 1), (0, 2))})),
        ("one_column", _input(5, 1, {8: ((0, 0), (4, 0)), 2: ((1, 0), (2, 0))})),
        ("full_width_nonsquare", _input(8, 18, {8: ((7, 0), (7, 17)), 2: ((0, 0), (5, 5))})),
        ("full_height_nonsquare", _input(16, 9, {8: ((0, 8), (15, 8)), 2: ((1, 0), (5, 4))})),
        ("arc_maximum_diagonal", _input(30, 30, {
            8: ((0, 29), (29, 0)), 6: ((0, 0), (5, 0)), 2: ((28, 1), (28, 5)),
        })),
        ("metric_counterexample", _metric_counterexample()),
    ]


@pytest.mark.parametrize("name,grid", _valid_boundary_inputs(), ids=lambda value: value if isinstance(value, str) else None)
def test_validator_accepts_lawful_nonsquare_full_span_and_arc_boundary_inputs(name, grid):
    observed = _oracle(grid)
    before = deepcopy(grid)
    assert generator.self_check(grid) == [], name
    assert generator.observe_overrides(grid) == _axes(observed), name
    assert grid == before, "validation and observation must not mutate inputs"


def _malformed_inputs():
    cases = [
        ("none", None), ("empty", []), ("empty_rows", [[], []]),
        ("non_grid_integer", 1), ("non_grid_string", "not a grid"),
        ("blank", [[0] * 10 for _ in range(8)]),
        ("full_grid", [[2] * 10 for _ in range(8)]),
        ("no_zero_background", [[1, 2, 2, 1]]),
        ("single_pair", _input(8, 10, {4: ((0, 0), (0, 6))})),
        ("five_pairs", _input(10, 10, {color: ((color, 0), (color, 9 if color == 1 else 2))
                                       for color in range(1, 6)})),
        ("nonaligned_winner", _input(8, 10, {4: ((0, 0), (6, 4)), 2: ((1, 1), (1, 3))})),
        ("nonaligned_loser", _input(8, 10, {4: ((0, 0), (0, 6)), 2: ((2, 8), (4, 9))})),
        ("tied_longest_spans", _input(8, 10, {4: ((0, 0), (0, 6)), 2: ((1, 1), (7, 7))})),
    ]
    for name, replacement in (("ragged", [0] * 9), ("empty_row", []),
                               ("non_row", None), ("string_row", "0000000000")):
        grid = _metric_counterexample()
        grid[-1] = replacement
        cases.append((name, grid))
    for name, value in (("bool", False), ("float", 0.0), ("string", "0"),
                        ("none", None), ("negative_color", -1), ("color_above_nine", 10),
                        ("unhashable_color", {})):
        grid = _metric_counterexample()
        grid[7][9] = value
        cases.append((name, grid))
    for name, color in (("extra_singleton", 9), ("third_endpoint", 4)):
        grid = _metric_counterexample()
        grid[7][9] = color
        cases.append((name, grid))
    grid = _metric_counterexample() + [[0] * 10 for _ in range(23)]
    cases.append(("height_above_arc_limit", grid))
    grid = [row + [0] * 21 for row in _metric_counterexample()]
    cases.append(("width_above_arc_limit", grid))
    return cases


@pytest.mark.parametrize("name,grid", _malformed_inputs(), ids=lambda value: value if isinstance(value, str) else None)
def test_self_check_rejects_malformed_inputs_without_crashing(name, grid):
    before = deepcopy(grid)
    errors = generator.self_check(grid)
    assert isinstance(errors, list) and errors, name
    assert all(isinstance(error, str) and error for error in errors), name
    assert grid == before


@pytest.mark.parametrize("pair", CANONICAL_PAIRS,
                         ids=[f"variant-{pair['variant']}-{pair['split']}-{pair['pair_index']}" for pair in CANONICAL_PAIRS])
def test_independent_geometric_oracle_matches_every_labeled_canonical_pair(pair):
    observed = _oracle(pair["input"])
    assert _paint(observed, observed["winner"]) == pair["output"]
    assert generator.self_check(pair["input"]) == []


def test_declared_rivals_are_callable_and_canonical_shortcuts_fit_all_labels():
    for attribute in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        rivals = getattr(generator, attribute)
        assert isinstance(rivals, dict)
        assert set(REQUIRED_RIVALS) <= set(rivals)
        assert all(isinstance(name, str) and callable(solve) for name, solve in rivals.items())
    shortcuts = generator.CANONICAL_SHORTCUTS
    assert {"longest_euclidean", "longest_manhattan", "prefer_diagonal"} <= set(shortcuts)
    for name, solve in shortcuts.items():
        for pair in CANONICAL_PAIRS:
            assert solve(deepcopy(pair["input"])) == pair["output"], (name, pair["split"], pair["pair_index"])


@pytest.mark.parametrize("name,expected_color", (
    ("longest_euclidean", 2), ("longest_manhattan", 2), ("prefer_diagonal", 2),
    ("lowest_color", 2), ("highest_color", 7),
))
def test_declared_rivals_follow_their_named_geometry_on_an_explicit_counterexample(name, expected_color):
    grid = _metric_counterexample()
    observed = _oracle(grid)
    assert observed["winner"] == 4
    expected = _paint(observed, expected_color)
    assert expected != _paint(observed, observed["winner"])
    for attribute in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        assert getattr(generator, attribute)[name](deepcopy(grid)) == expected


@pytest.mark.parametrize("name,grid,first,last", (
    ("winner_first", _metric_counterexample(), 4, 7),
    ("winner_last", _input(8, 10, {
        4: ((7, 0), (7, 6)), 2: ((1, 1), (6, 6)), 7: ((2, 9), (4, 9)),
    }), 2, 4),
    ("winner_middle", _input(8, 10, {
        4: ((2, 0), (2, 5)), 2: ((3, 1), (7, 5)), 7: ((0, 8), (0, 9)),
    }), 7, 2),
), ids=lambda value: value if isinstance(value, str) else None)
def test_scan_rivals_follow_row_major_first_appearance_instead_of_numeric_color_rank(name, grid, first, last):
    observed = _oracle(grid)
    assert observed["winner"] == 4
    for attribute in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        rivals = getattr(generator, attribute)
        assert rivals["first_in_scan"](deepcopy(grid)) == _paint(observed, first), name
        assert rivals["last_in_scan"](deepcopy(grid)) == _paint(observed, last), name
