"""Portable behavioral tests for the three-panel C4 rotation generator.

The expected answers below use cropped binary arrays and matrix transposition,
independently of the generator's coordinate/orbit implementation. Canonical
labels come only from reviewer_support authoring data. Authoritative generated
labels remain the responsibility of the public Racket-backed checks.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
from itertools import permutations
from pathlib import Path
import random
import re
import sys

import pytest

try:
    from reviewer_support import canonical_pairs, find_root
except ModuleNotFoundError as error:
    if error.name != "reviewer_support":
        raise
    # The same file also runs in the selected source home. Locate its own
    # public helper, without relying on cwd, fixed ancestor depth, or a sibling.
    for ancestor in Path(__file__).resolve().parents:
        helper_dir = ancestor / "shared" / "runtime"
        if (helper_dir / "reviewer_support.py").is_file():
            sys.path.insert(0, str(helper_dir))
            break
    else:
        raise
    from reviewer_support import canonical_pairs, find_root

TASK_ID = "5c126cb64bf7"
ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path for path in (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
        ROOT / "generators" / TASK_ID / "generator.py",
    )
    if path.is_file()
)
SPEC = importlib.util.spec_from_file_location(
    "_rotation_generator_under_test", GENERATOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)

BANDS = (None, "easy", "medium", "hard")
STARTS = (0, 6, 12)
PARTITIONS = {
    "all_distinct": 3,
    "all_same": 1,
    "pair_01": 2,
    "pair_02": 2,
    "pair_12": 2,
}
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def _crop(binary):
    occupied_rows = [r for r, row in enumerate(binary) if any(row)]
    assert occupied_rows, "The independent oracle requires a nonempty panel."
    occupied_cols = [
        c for c in range(len(binary[0]))
        if any(row[c] for row in binary)
    ]
    top, bottom = occupied_rows[0], occupied_rows[-1]
    left, right = occupied_cols[0], occupied_cols[-1]
    return tuple(
        tuple(int(bool(value)) for value in row[left:right + 1])
        for row in binary[top:bottom + 1]
    )


def _panel(grid, start):
    return tuple(
        tuple(int(value != 0) for value in row[start:start + 5])
        for row in grid
    )


def _turn(binary):
    # Rotate a rectangular array clockwise. This deliberately does not use a
    # coordinate transformation, normalization helper, or generator function.
    return tuple(tuple(row) for row in zip(*binary[::-1]))


def _rotations(binary):
    result = [binary]
    for _ in range(3):
        result.append(_turn(result[-1]))
    return tuple(result)


def _oracle(grid):
    shapes = tuple(_crop(_panel(grid, start)) for start in STARTS)
    return [
        [
            8 if i == j else (2 if shapes[j] in _rotations(shapes[i]) else 0)
            for j in range(3)
        ]
        for i in range(3)
    ]


def _partition(output):
    edges = [(i, j) for i in range(3) for j in range(i + 1, 3)
             if output[i][j] == 2]
    if not edges:
        return "all_distinct"
    if len(edges) == 3:
        return "all_same"
    assert len(edges) == 1, "Rotation equivalence must be transitive."
    i, j = edges[0]
    return f"pair_{i}{j}"


def _components(binary):
    height, width = len(binary), len(binary[0])
    visited = [[False] * width for _ in range(height)]
    result = []
    for row in range(height):
        for col in range(width):
            if not binary[row][col] or visited[row][col]:
                continue
            component = [[0] * width for _ in range(height)]
            queue = [(row, col)]
            visited[row][col] = True
            while queue:
                r, c = queue.pop()
                component[r][c] = 1
                for nr, nc in ((r - 1, c), (r + 1, c),
                               (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and binary[nr][nc] and not visited[nr][nc]):
                        visited[nr][nc] = True
                        queue.append((nr, nc))
            result.append(_crop(component))
    return result


def _cell_count(binary):
    return sum(sum(row) for row in binary)


def _observed(grid):
    partition = _partition(_oracle(grid))
    components = [len(_components(_panel(grid, start))) for start in STARTS]
    texture = ("connected" if all(count == 1 for count in components)
               else "scattered" if all(count > 1 for count in components)
               else "mixed")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_classes": PARTITIONS[partition],
        "partition": partition,
        "palette_size": len({value for row in grid for value in row} - {0}),
        "texture": texture,
    }


def _assert_valid_grid(grid):
    assert isinstance(grid, list) and 5 <= len(grid) <= 9
    assert all(isinstance(row, list) and len(row) == 17 for row in grid)
    assert all(type(value) is int and 0 <= value <= 9
               for row in grid for value in row)
    assert all(row[5] == row[11] == 0 for row in grid)
    for start in STARTS:
        cells = [value for row in grid for value in row[start:start + 5]
                 if value != 0]
        assert 3 <= len(cells) <= 7
        assert len(set(cells)) == 1
    assert gen.self_check(deepcopy(grid)) == []


def _assert_accepts(result):
    assert result is True or isinstance(result, (list, tuple)) and not result


def _assert_rejects(result):
    assert result is False or (
        isinstance(result, (list, tuple)) and result
        and all(isinstance(reason, str) and reason for reason in result)
    )


def _render(patterns, *, height=5, colors=(2, 4, 7), offsets=None):
    if offsets is None:
        offsets = ((1, 1), (0, 1), (1, 3))
    grid = [[0] * 17 for _ in range(height)]
    for start, pattern, color, (top, left) in zip(
            STARTS, patterns, colors, offsets):
        assert top + len(pattern) <= height and left + len(pattern[0]) <= 5
        for row, values in enumerate(pattern):
            for col, value in enumerate(values):
                if value:
                    grid[top + row][start + left + col] = color
    return grid


L_SHAPE = ((1, 0), (1, 0), (1, 1))


def _example_grid():
    return _render((
        L_SHAPE,
        _turn(L_SHAPE),
        tuple(tuple(reversed(row)) for row in L_SHAPE),
    ))


def _features(grid):
    shapes = [_crop(_panel(grid, start)) for start in STARTS]
    components = [
        sorted(_components(shape), key=_cell_count, reverse=True)
        for shape in shapes
    ]
    result = set()
    for i in range(3):
        for j in range(i + 1, 3):
            turns = {n for n, shape in enumerate(_rotations(shapes[i]))
                     if shape == shapes[j]}
            if turns:
                if 0 not in turns and turns & {1, 3}:
                    result.add("quarter_turn")
                if turns == {2}:
                    result.add("half_turn")
                continue
            if _cell_count(shapes[i]) == _cell_count(shapes[j]):
                result.add("same_count_negative")
            reflected = tuple(tuple(reversed(row)) for row in shapes[i])
            if shapes[j] in _rotations(reflected):
                result.add("reflection_negative")
            first, second = components[i], components[j]
            if (len(first) > 1 and len(second) > 1
                    and _cell_count(first[0]) > 1
                    and _cell_count(second[0]) > 1
                    and all(_cell_count(piece) == 1 for piece in first[1:])
                    and all(_cell_count(piece) == 1 for piece in second[1:])
                    and second[0] in _rotations(first[0])):
                result.add("satellite_negative")
    return result


def _competitors():
    result = {}
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS",
                      "CANONICAL_SHORTCUTS"):
        declaration = getattr(gen, namespace, {})
        assert isinstance(declaration, dict), namespace
        for name, solve in declaration.items():
            assert isinstance(name, str) and name and callable(solve)
            result[f"{namespace}:{name}"] = solve
    return result


def test_declared_identity_axes_and_lesson_contract():
    assert gen.GENERATOR_ID == gen.TASK_ID == TASK_ID
    assert isinstance(gen.VERSION, str)
    version = re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)",
        gen.VERSION,
    )
    assert version is not None
    assert any(int(component) > 0 for component in version.groups())
    assert gen.RULE_HASH == "338c27e34ee3"
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 5
    assert type(gen.EXAMPLES_NEEDED) is int and gen.EXAMPLES_NEEDED == 9
    assert type(gen.LESSON_SCHEDULE_PERIOD) is int
    assert gen.LESSON_SCHEDULE_PERIOD == gen.EXAMPLES_NEEDED + 1 == 10
    assert set(gen.AXES) == {
        "grid_h", "grid_w", "n_classes", "partition", "palette_size", "texture"
    }
    fixed_width = gen.AXES["grid_w"]
    assert (fixed_width.get("probe") == "diagnostic"
            or fixed_width.get("exact") is False
            or fixed_width.get("diagnostic") is True)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.observe_overrides)
    assert callable(gen.lesson_identifiable)
    assert callable(gen.schedule_profile)


@pytest.mark.parametrize(
    "pair", CANONICAL,
    ids=lambda pair: (
        f"variant{pair['variant']}-{pair['split']}-{pair['pair_index']}"
    ),
)
def test_canonical_labels_match_array_oracle_and_all_inputs_are_accepted(pair):
    original = deepcopy(pair["input"])
    assert _oracle(pair["input"]) == pair["output"]
    _assert_valid_grid(pair["input"])
    _assert_accepts(gen.strict_canonical_like(pair["input"]))
    observed = gen.observe_overrides(pair["input"])
    expected = _observed(pair["input"])
    for name in ("grid_h", "grid_w", "n_classes", "partition", "palette_size"):
        assert observed[name] == expected[name]
    assert pair["input"] == original


def test_canonical_palette_reuse_and_mixed_connectivity_remain_supported():
    assert CANONICAL
    assert any(_observed(pair["input"])["texture"] == "mixed"
               for pair in CANONICAL)
    for pair in CANONICAL:
        grid = [[1 if value else 0 for value in row]
                for row in pair["input"]]
        _assert_valid_grid(grid)
        _assert_accepts(gen.strict_canonical_like(grid))
        assert _oracle(grid) == pair["output"]
        assert gen.observe_overrides(grid)["palette_size"] == 1


@pytest.mark.parametrize("turns", range(4))
def test_handmade_chiral_pair_uses_all_c4_rotations_and_excludes_reflection(turns):
    mirror = tuple(tuple(reversed(row)) for row in L_SHAPE)
    grid = _render((L_SHAPE, _rotations(L_SHAPE)[turns], mirror))
    expected = [[8, 2, 0], [2, 8, 0], [0, 0, 8]]
    assert _oracle(grid) == expected
    _assert_valid_grid(grid)
    _assert_accepts(gen.strict_canonical_like(grid))
    observed = gen.observe_overrides(grid)
    assert observed["partition"] == "pair_01"
    assert observed["n_classes"] == 2


@pytest.mark.parametrize("order", tuple(permutations(range(3))))
def test_panel_permutation_moves_the_relation_matrix_and_observed_pair(order):
    grid = _example_grid()
    expected = _oracle(grid)
    reordered = [
        [value for i, panel_index in enumerate(order)
         for value in (
             row[STARTS[panel_index]:STARTS[panel_index] + 5]
             + ([0] if i < 2 else [])
         )]
        for row in grid
    ]
    permuted_output = [[expected[i][j] for j in order] for i in order]
    assert _oracle(reordered) == permuted_output
    assert gen.observe_overrides(reordered)["partition"] == _partition(permuted_output)


@pytest.mark.parametrize("height", (6, 7, 8, 9))
def test_translation_and_tall_valid_inputs_preserve_cropped_shape_comparison(height):
    mirror = tuple(tuple(reversed(row)) for row in L_SHAPE)
    grid = _render(
        (L_SHAPE, _turn(L_SHAPE), mirror), height=height, colors=(1, 1, 1),
        offsets=((height - 3, 3), (0, 0), (height - 3, 0)),
    )
    _assert_valid_grid(grid)
    assert _oracle(grid) == [[8, 2, 0], [2, 8, 0], [0, 0, 8]]
    assert gen.observe_overrides(grid)["grid_h"] == height
    _assert_rejects(gen.strict_canonical_like(grid))


BAD_CASES = (
    "none", "scalar", "string", "empty", "empty_rows", "non_row", "ragged",
    "height_4", "height_10", "width_16", "width_18", "negative_color",
    "color_10", "boolean_color", "float_color", "string_color",
    "separator_5", "separator_11", "empty_left", "empty_middle", "empty_right",
    "two_cells", "eight_cells", "multicolor_panel",
)


def _bad_grid(case):
    grid = _example_grid()
    if case == "none":
        return None
    if case == "scalar":
        return 7
    if case == "string":
        return "grid"
    if case == "empty":
        return []
    if case == "empty_rows":
        return [[] for _ in range(5)]
    if case == "non_row":
        grid[1] = None
    elif case == "ragged":
        grid[1].pop()
    elif case == "height_4":
        grid.pop()
    elif case == "height_10":
        grid.extend([[0] * 17 for _ in range(5)])
    elif case == "width_16":
        grid = [row[:-1] for row in grid]
    elif case == "width_18":
        grid = [row + [0] for row in grid]
    elif case in {
        "negative_color", "color_10", "boolean_color", "float_color", "string_color"
    }:
        grid[4][4] = {
            "negative_color": -1, "color_10": 10, "boolean_color": True,
            "float_color": 1.0, "string_color": "1",
        }[case]
    elif case in ("separator_5", "separator_11"):
        grid[0][int(case.split("_")[1])] = 2
    elif case.startswith("empty_"):
        start = {"empty_left": 0, "empty_middle": 6, "empty_right": 12}[case]
        for row in grid:
            row[start:start + 5] = [0] * 5
    elif case in ("two_cells", "eight_cells"):
        for row in grid:
            row[:5] = [0] * 5
        count = 2 if case == "two_cells" else 8
        for i in range(count):
            grid[i // 5][i % 5] = 2
    elif case == "multicolor_panel":
        grid[0][7] = 9
    else:
        raise AssertionError(case)
    return grid


@pytest.mark.parametrize("case", BAD_CASES)
def test_malformed_or_out_of_manifold_inputs_return_reasons_without_raising(case):
    invalid = _bad_grid(case)
    original = deepcopy(invalid)
    messages = gen.self_check(invalid)
    assert isinstance(messages, list) and messages
    assert all(isinstance(message, str) and message for message in messages)
    _assert_rejects(gen.strict_canonical_like(invalid))
    assert invalid == original


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("height", (5, 7, 9))
@pytest.mark.parametrize("palette_size", (1, 2, 3))
@pytest.mark.parametrize(
    "partition,texture",
    [(partition, texture) for partition, classes in PARTITIONS.items()
     for texture in ("connected", "scattered", "mixed")
     if texture != "mixed" or classes >= 2],
)
def test_exact_controls_interact_correctly_at_height_and_palette_boundaries(
        band, height, partition, palette_size, texture):
    requested = {
        "grid_h": height, "grid_w": 17, "n_classes": PARTITIONS[partition],
        "partition": partition, "palette_size": palette_size, "texture": texture,
    }
    grid = gen.generate(103, 19, difficulty=band, **requested)
    _assert_valid_grid(grid)
    expected = _observed(grid)
    observed = gen.observe_overrides(deepcopy(grid))
    for name, value in requested.items():
        assert expected[name] == value, (name, value, expected)
        assert observed[name] == expected[name], (name, expected, observed)
    if height == 5:
        _assert_accepts(gen.strict_canonical_like(grid))
    else:
        _assert_rejects(gen.strict_canonical_like(grid))


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("n_classes", (1, 2, 3))
def test_n_classes_alone_selects_a_compatible_rendered_partition(band, n_classes):
    for seed, index in ((0, 0), (31, 7), (89, 16)):
        grid = gen.generate(seed, index, difficulty=band, n_classes=n_classes)
        _assert_valid_grid(grid)
        assert _observed(grid)["n_classes"] == n_classes
        assert gen.observe_overrides(grid)["n_classes"] == n_classes


@pytest.mark.parametrize(
    "partition,n_classes",
    [(partition, count) for partition, actual in PARTITIONS.items()
     for count in (1, 2, 3) if count != actual],
)
def test_conflicting_class_count_and_partition_have_structured_errors(
        partition, n_classes):
    with pytest.raises(ValueError) as caught:
        gen.generate(7, 4, n_classes=n_classes, partition=partition,
                     grid_h=9, palette_size=1, texture="scattered")
    assert set(caught.value.incompatible_axes) == {"n_classes", "partition"}


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "class_control", ({"n_classes": 1}, {"partition": "all_same"}),
    ids=("n_classes", "partition"),
)
def test_mixed_texture_cannot_form_one_rotation_class(band, class_control):
    with pytest.raises(ValueError) as caught:
        gen.generate(7, 4, difficulty=band, grid_h=9, palette_size=1,
                     texture="mixed", **class_control)
    incompatible_axes = set(caught.value.incompatible_axes)
    assert {"texture", *class_control} <= incompatible_axes


INVALID_OVERRIDES = (
    ("grid_h", 4), ("grid_h", 10), ("grid_h", True), ("grid_h", 5.5),
    ("grid_h", "5"),
    ("grid_w", 16), ("grid_w", 18), ("grid_w", 17.0), ("grid_w", True),
    ("n_classes", 0), ("n_classes", 4), ("n_classes", False),
    ("n_classes", "2"),
    ("palette_size", 0), ("palette_size", 4), ("palette_size", True),
    ("palette_size", 2.5),
    ("partition", "pair_10"), ("partition", ""), ("partition", 2),
    ("texture", "default"), ("texture", "empty_panel"),
    ("texture", "all_identical"), ("texture", "no_pairs"),
)


@pytest.mark.parametrize("axis,value", INVALID_OVERRIDES)
def test_invalid_axis_values_cannot_be_silently_coerced_or_ignored(axis, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 9, **{axis: value})


@pytest.mark.parametrize(
    "axis,value",
    (
        ("palette_kind", "warm"), ("panel_cell_count", 4),
        ("position_bias", "center"), ("n_distinct_colors", 2),
        ("density", "panels"), ("__override_contract_unknown_axis__", 1),
    ),
)
def test_removed_or_unknown_knobs_fail_explicitly(axis, value):
    with pytest.raises((TypeError, ValueError)) as caught:
        gen.generate(17, 9, **{axis: value})
    message = str(caught.value).lower()
    assert axis.lower() in message
    assert "unknown" in message or "unexpected" in message or "unsupported" in message


@pytest.mark.parametrize("band", BANDS)
def test_seed_index_determinism_is_independent_of_call_order_and_global_random(band):
    for seed, index in ((0, 0), (17, 11), (123456789, 109)):
        before = random.getstate()
        first = gen.generate(seed, index, difficulty=band)
        assert random.getstate() == before
        expected = deepcopy(first)
        gen.generate(seed + 9, index + 27, difficulty=band)
        second = gen.generate(seed, index, difficulty=band)
        assert first == second
        first[0][0] = 99
        assert second == expected
        assert gen.generate(seed, index, difficulty=band) == expected


def test_difficulty_changes_observed_shape_complexity_not_just_color_labels():
    def signature(grid):
        shapes = [_crop(_panel(grid, start)) for start in STARTS]
        return (
            len(grid),
            tuple(sorted(
                (_cell_count(shape), len(shape) * len(shape[0]),
                 len(_components(shape))) for shape in shapes
            )),
        )
    profiles = {
        band: Counter(
            signature(gen.generate(seed, index, difficulty=band))
            for seed in (0, 11, 67)
            for index in range(2 * gen.LESSON_SCHEDULE_PERIOD)
        )
        for band in ("easy", "hard")
    }
    assert profiles["easy"] != profiles["hard"]


@pytest.mark.parametrize("band", BANDS)
def test_defaults_keep_canonical_height_favored_while_inputs_remain_valid(band):
    heights = Counter()
    for seed in (0, 11, 67, 103):
        for index in range(2 * gen.LESSON_SCHEDULE_PERIOD):
            grid = gen.generate(seed, index, difficulty=band)
            _assert_valid_grid(grid)
            heights[len(grid)] += 1
            if len(grid) == 5:
                _assert_accepts(gen.strict_canonical_like(grid))
    assert heights[5] >= 0.6 * sum(heights.values())
    assert sum(count for height, count in heights.items() if height > 5) > 0


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", (0, 31))
def test_schedule_profiles_repeat_for_the_declared_actual_period(band, seed):
    period = gen.LESSON_SCHEDULE_PERIOD
    declared = set(gen.SCHEDULE_PROFILES)
    seen = set()
    for index in range(period):
        profile = gen.schedule_profile(seed, index, difficulty=band)
        hash(profile)
        seen.add(profile)
        for later in (index + period, index + 3 * period):
            assert gen.schedule_profile(seed, later, difficulty=band) == profile
    assert seen == declared


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", (0, 31))
def test_every_cyclic_window_has_pixel_level_repeated_semantic_contrasts(band, seed):
    period = gen.LESSON_SCHEDULE_PERIOD
    stream = [
        gen.generate(seed, index, difficulty=band)
        for index in range(3 * period)
    ]
    for start in range(2 * period):
        window = stream[start:start + period]
        partitions = Counter(_partition(_oracle(grid)) for grid in window)
        assert partitions["all_same"] >= 2
        assert partitions["all_distinct"] >= 2
        assert sum(partitions[name] for name in ("pair_01", "pair_02", "pair_12")) >= 4
        assert sum(partitions.values()) == 10
        features = Counter(feature for grid in window for feature in _features(grid))
        for feature in ("quarter_turn", "half_turn", "same_count_negative",
                        "reflection_negative", "satellite_negative"):
            assert features[feature] >= 2, (band, seed, start, feature, features)


def test_default_pair_locations_cover_all_three_edges_across_seeds_and_periods():
    seen = set()
    for seed in (0, 11, 67):
        for index in range(3 * gen.LESSON_SCHEDULE_PERIOD):
            partition = _partition(_oracle(gen.generate(seed, index)))
            if partition.startswith("pair_"):
                seen.add(partition)
    assert seen == {"pair_01", "pair_02", "pair_12"}


def test_witness_declarations_are_callable_and_every_refutation_claim_is_true():
    witnesses = gen.SEMANTIC_WITNESSES
    rivals = gen.SEMANTIC_RIVALS
    mapping = gen.WITNESS_RIVALS
    branches = set(getattr(gen, "BRANCH_WITNESSES", ()))
    assert isinstance(witnesses, dict) and witnesses
    assert isinstance(rivals, dict) and rivals
    assert isinstance(mapping, dict) and mapping
    assert branches <= set(witnesses)
    assert set(mapping) <= set(witnesses)
    assert set(witnesses) - branches <= set(mapping)
    fired = Counter()
    for name, predicate in witnesses.items():
        assert isinstance(name, str) and name and callable(predicate)
    for witness, names in mapping.items():
        names = [names] if isinstance(names, str) else list(names)
        assert names and set(names) <= set(rivals), witness
    for band in BANDS:
        # Include the one- and two-color seed families as well as the
        # three-color families when checking coverage over generated support.
        for seed in (0, 31, 3, 4):
            for index in range(2 * gen.LESSON_SCHEDULE_PERIOD):
                grid = gen.generate(seed, index, difficulty=band)
                expected = _oracle(grid)
                for name, predicate in witnesses.items():
                    input_copy = deepcopy(grid)
                    result = predicate(input_copy)
                    assert type(result) is bool, name
                    assert input_copy == grid, name
                    if not result:
                        continue
                    fired[name] += 1
                    if name in mapping:
                        names = mapping[name]
                        names = [names] if isinstance(names, str) else list(names)
                        assert any(
                            rivals[rival](deepcopy(grid)) != expected
                            for rival in names
                        ), (name, band, seed, index)
    assert set(fired) == set(witnesses)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", (0, 31))
def test_actual_period_lessons_have_no_rival_ambiguity_after_any_holdout(band, seed):
    period = gen.LESSON_SCHEDULE_PERIOD
    competitors = _competitors()
    assert competitors
    pairs = [
        {"input": grid, "output": _oracle(grid)}
        for index in range(3 * period)
        for grid in [gen.generate(seed, index, difficulty=band)]
    ]
    predictions = {
        name: [solve(deepcopy(pair["input"])) for pair in pairs]
        for name, solve in competitors.items()
    }
    for start in range(2 * period):
        lesson = pairs[start:start + period]
        for held_out in range(period):
            demos = lesson[:held_out] + lesson[held_out + 1:]
            query = lesson[held_out]
            # A rival agreeing on the entire episode is survived_all.
            # Ambiguity requires fitting every demonstration and changing
            # the held-out query answer.
            for name, outputs in predictions.items():
                fits_demos = all(
                    outputs[start + i] == pair["output"]
                    for i, pair in enumerate(lesson) if i != held_out
                )
                if fits_demos:
                    assert outputs[start + held_out] == query["output"], (
                        band, seed, start, held_out, name
                    )
            original = deepcopy((demos, query))
            assert gen.lesson_identifiable(demos, query) == [], (
                band, seed, start, held_out
            )
            assert (demos, query) == original


def test_lesson_hook_rejects_a_demonstrably_ambiguous_lesson():
    pairs = [
        {"input": grid, "output": _oracle(grid)}
        for index in range(4 * gen.LESSON_SCHEDULE_PERIOD)
        for grid in [gen.generate(103, index, difficulty="medium")]
    ]
    candidate = None
    for name, solve in _competitors().items():
        fitting = [pair for pair in pairs
                   if solve(deepcopy(pair["input"])) == pair["output"]]
        refuting = [pair for pair in pairs
                    if solve(deepcopy(pair["input"])) != pair["output"]]
        if fitting and refuting:
            candidate = (name, fitting, refuting[0])
            break
    assert candidate is not None
    name, fitting, query = candidate
    demos = [deepcopy(fitting[index % len(fitting)])
             for index in range(gen.EXAMPLES_NEEDED)]
    reasons = gen.lesson_identifiable(demos, deepcopy(query))
    assert isinstance(reasons, list) and reasons, name
    assert all(isinstance(reason, str) and reason for reason in reasons)

