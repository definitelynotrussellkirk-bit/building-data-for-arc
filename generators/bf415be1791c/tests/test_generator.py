"""Focused, portable regressions for bf415be1791c.

The oracles and measurements below are intentionally independent of generator
metadata. Racket remains the output authority; the Python mirror is checked
against every labeled canonical pair and a generated sample.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "bf415be1791c"
TASK_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    f"review_{TASK_ID}", TASK_DIR / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

PROBE_SPEC = importlib.util.spec_from_file_location(
    f"review_{TASK_ID}_shortcut_probe", TASK_DIR / "workspace" / "probe_shortcuts.py"
)
assert PROBE_SPEC and PROBE_SPEC.loader
SHORTCUT_PROBE = importlib.util.module_from_spec(PROBE_SPEC)
PROBE_SPEC.loader.exec_module(SHORTCUT_PROBE)

BANDS = (None, "easy", "medium", "hard")
AXES = {
    "grid_h",
    "grid_w",
    "divider_col",
    "n_magenta",
    "n_components",
    "n_distractor_cells",
    "n_distractor_colors",
}
RIVALS = {
    "largest_magenta_component_only",
    "components_of_size_at_least_two",
    "components_of_size_at_least_three",
    "components_of_size_at_least_four",
    "components_of_size_at_most_six",
    "reflect_every_colored_left_cell",
    "move_magenta_instead_of_copying",
}


def _divider(grid):
    height = len(grid)
    width = len(grid[0])
    columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    assert len(columns) == 1
    return columns[0]


def _components(grid, color=6):
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = [start]
        component = {start}
        for row, col in queue:
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = row + drow, col + dcol
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return sorted(result, key=lambda cells: (min(cells), len(cells)))


def independent_rule(grid):
    divider = _divider(grid)
    output = [list(row) for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 6:
                continue
            mirror_col = 2 * divider - col
            if 0 <= mirror_col < len(values) and output[row][mirror_col] == 0:
                output[row][mirror_col] = 8
    return output


def independent_observed(grid):
    distractors = [
        value
        for row in grid
        for value in row
        if value not in (0, 5, 6, 8)
    ]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "divider_col": _divider(grid),
        "n_magenta": sum(value == 6 for row in grid for value in row),
        "n_components": len(_components(grid)),
        "n_distractor_cells": len(distractors),
        "n_distractor_colors": len(set(distractors)),
    }


def largest_component_only(grid):
    divider = _divider(grid)
    output = [list(row) for row in grid]
    components = _components(grid)
    selected = sorted(components, key=lambda cells: (-len(cells), min(cells)))[0]
    for row, col in selected:
        mirror_col = 2 * divider - col
        if 0 <= mirror_col < len(grid[0]) and output[row][mirror_col] == 0:
            output[row][mirror_col] = 8
    return output


def components_of_size_at_least(grid, minimum_size):
    """Independent canonical-fitting component-size shortcut."""
    divider = _divider(grid)
    output = [list(row) for row in grid]
    for component in _components(grid):
        if len(component) < minimum_size:
            continue
        for row, col in component:
            mirror_col = 2 * divider - col
            if 0 <= mirror_col < len(grid[0]) and output[row][mirror_col] == 0:
                output[row][mirror_col] = 8
    return output


def components_of_size_at_most(grid, maximum_size):
    """Independent upper-size component shortcut."""
    divider = _divider(grid)
    output = [list(row) for row in grid]
    for component in _components(grid):
        if len(component) > maximum_size:
            continue
        for row, col in component:
            mirror_col = 2 * divider - col
            if 0 <= mirror_col < len(grid[0]) and output[row][mirror_col] == 0:
                output[row][mirror_col] = 8
    return output


def accepts(result):
    return result is True or result == []


def canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def test_rule_pin_and_public_contract():
    assert GEN.RULE_HASH == "7d82bc36a98b"
    assert GEN.VERSION == "2.2.0"
    assert set(GEN.AXES) == AXES
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 8
    assert tuple(GEN.SCHEDULE_PROFILES) == tuple(range(8))


def test_all_canonical_pairs_are_accepted_and_match_independent_rule():
    pairs = canonical()
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == [], pair
        assert accepts(GEN.strict_canonical_like(pair["input"])), pair
        assert independent_rule(pair["input"]) == pair["output"], pair
        assert GEN.rule_mirror(pair["input"]) == pair["output"], pair


EXACT_CASES = (
    {
        "grid_h": 9,
        "grid_w": 12,
        "divider_col": 5,
        "n_magenta": 4,
        "n_components": 1,
        "n_distractor_cells": 4,
        "n_distractor_colors": 2,
    },
    {
        "grid_h": 9,
        "grid_w": 12,
        "divider_col": 8,
        "n_magenta": 10,
        "n_components": 3,
        "n_distractor_cells": 10,
        "n_distractor_colors": 4,
    },
    {
        "grid_h": 13,
        "grid_w": 16,
        "divider_col": 8,
        "n_magenta": 10,
        "n_components": 3,
        "n_distractor_cells": 10,
        "n_distractor_colors": 4,
    },
)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("options", EXACT_CASES)
def test_full_range_exact_controls_are_constructive_and_observable(band, options):
    grid = GEN.generate(391, 8, difficulty=band, **options)
    assert independent_observed(grid) == options
    assert GEN.observe_overrides(grid) == options
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": options}) == []
    assert accepts(GEN.strict_canonical_like(grid))
    assert GEN.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 8),
        ("grid_h", 14),
        ("grid_w", 11),
        ("grid_w", 17),
        ("divider_col", 4),
        ("divider_col", 9),
        ("n_magenta", 3),
        ("n_magenta", 11),
        ("n_components", 0),
        ("n_components", 4),
        ("n_distractor_cells", 3),
        ("n_distractor_cells", 11),
        ("n_distractor_colors", 1),
        ("n_distractor_colors", 5),
        ("grid_h", True),
        ("grid_w", 12.5),
        ("n_magenta", "6"),
        ("n_components", False),
        ("palette_kind", "warm"),
        ("texture", "no_divider"),
        ("palette_size", 2),
        ("position_bias", "magenta_left_with_5_div"),
        ("n_distinct_colors", 2),
        ("density", "sparse"),
        ("unknown_axis", 1),
    ],
)
def test_invalid_or_retired_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{key: value})


def test_none_overrides_keep_default_draw_convention():
    kwargs = {name: None for name in AXES}
    assert GEN.generate(22, 1, **kwargs) == GEN.generate(22, 1)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 12 for _ in range(9)],
        [[0] * 12 for _ in range(9)],
        [[10] + [0] * 11 for _ in range(9)],
        ["000000000000"] * 9,
    ],
)
def test_malformed_self_check_is_diagnostic_not_exception(grid):
    result = GEN.self_check(grid)
    assert isinstance(result, list) and result


def test_self_check_rejects_rule_domain_near_misses():
    grid = GEN.generate(812, 2)
    assert GEN.self_check(grid) == []

    right_magenta = deepcopy(grid)
    divider = _divider(right_magenta)
    source = min(_components(right_magenta)[0])
    right_magenta[source[0]][source[1]] = 0
    right_magenta[source[0]][divider + 1] = 6
    assert GEN.self_check(right_magenta)

    occupied_target = deepcopy(grid)
    row, col = min(_components(occupied_target)[0])
    occupied_target[row][2 * divider - col] = 2
    assert GEN.self_check(occupied_target)

    cyan_input = deepcopy(grid)
    cyan_input[0][0] = 8
    assert GEN.self_check(cyan_input)

    broken_divider = deepcopy(grid)
    broken_divider[0][divider] = 0
    assert GEN.self_check(broken_divider)


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    expected = {
        "largest_magenta_component_only",
        "components_of_size_at_least_two",
        "components_of_size_at_least_three",
        "components_of_size_at_least_four",
        "components_of_size_at_most_six",
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == expected
    assert RIVALS <= set(GEN.SEMANTIC_RIVALS)
    for pair in canonical():
        assert largest_component_only(pair["input"]) == pair["output"]
        assert components_of_size_at_least(pair["input"], 2) == pair["output"]
        assert components_of_size_at_least(pair["input"], 3) == pair["output"]
        assert components_of_size_at_least(pair["input"], 4) == pair["output"]
        assert components_of_size_at_most(pair["input"], 6) == pair["output"]
        assert all(
            shortcut(pair["input"]) == pair["output"]
            for shortcut in GEN.CANONICAL_SHORTCUTS.values()
        )


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_default_schedule_covers_all_profiles_and_teaching_witnesses(band):
    grids = [GEN.generate(1207, index, difficulty=band) for index in range(16)]
    observed = [independent_observed(grid) for grid in grids]
    assert {
        GEN.schedule_profile(1207, index, difficulty=band) for index in range(8)
    } == set(range(8))
    assert {item["grid_h"] for item in observed} >= {9, 10, 13}
    assert {item["grid_w"] for item in observed} >= {12, 15, 16}
    assert {item["divider_col"] for item in observed} == {5, 6, 7, 8}
    assert {item["n_magenta"] for item in observed} >= {4, 5, 6, 8, 10}
    assert {item["n_components"] for item in observed} == {1, 2, 3}
    assert {item["n_distractor_cells"] for item in observed} >= {4, 5, 8, 10}
    assert {item["n_distractor_colors"] for item in observed} == {2, 3, 4}
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) == len(grids)
    assert all(GEN.self_check(grid, difficulty=band) == [] for grid in grids)
    assert all(accepts(GEN.strict_canonical_like(grid)) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["multiple_magenta_components"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["singleton_magenta_component"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["two_cell_magenta_component"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["oversized_magenta_component"](grid) for grid in grids)
    assert all(GEN.SEMANTIC_WITNESSES["left_distractor_has_empty_mirror"](grid) for grid in grids)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("start", range(8))
def test_every_four_pair_window_retains_small_component_witness_after_holdout(
    band, start
):
    grids = [
        GEN.generate(2609 + start, start + offset, difficulty=band)
        for offset in range(4)
    ]
    component_sizes = [sorted(map(len, _components(grid))) for grid in grids]
    singleton_witnesses = sum(1 in sizes for sizes in component_sizes)
    two_cell_witnesses = sum(2 in sizes for sizes in component_sizes)
    oversized_witnesses = sum(any(size > 6 for size in sizes) for sizes in component_sizes)
    assert singleton_witnesses >= 2, (band, start, component_sizes)
    assert two_cell_witnesses >= 2, (band, start, component_sizes)
    assert oversized_witnesses >= 2, (band, start, component_sizes)

    for query_index, query in enumerate(grids):
        demos = [grid for index, grid in enumerate(grids) if index != query_index]
        for minimum_size in (2, 3, 4):
            assert any(
                components_of_size_at_least(grid, minimum_size)
                != independent_rule(grid)
                for grid in demos
            ), (band, start, query_index, minimum_size, component_sizes)
        assert any(
            components_of_size_at_most(grid, 6) != independent_rule(grid)
            for grid in demos
        ), (band, start, query_index, "maximum_size=6", component_sizes)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("start", range(8))
def test_every_four_pair_window_and_query_rotation_refutes_all_rivals(band, start):
    pairs = []
    for offset in range(4):
        grid = GEN.generate(1801 + start, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": independent_rule(grid)})
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, query) == []
        for name in RIVALS:
            rival = GEN.LESSON_COMPETITORS[name]
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                band,
                start,
                query_index,
                name,
            )


def test_generated_multi_component_input_is_exact_shortcut_counterexample():
    grid = GEN.generate(
        412,
        1,
        grid_h=10,
        grid_w=15,
        divider_col=6,
        n_magenta=7,
        n_components=3,
        n_distractor_cells=6,
        n_distractor_colors=2,
    )
    intended = independent_rule(grid)
    rival = largest_component_only(grid)
    assert GEN.self_check(grid) == []
    assert len(_components(grid)) == 3
    assert rival != intended
    assert GEN.CANONICAL_SHORTCUTS["largest_magenta_component_only"](grid) == rival


def test_source_bound_shortcut_probe_refutes_every_declared_canonical_shortcut():
    record = SHORTCUT_PROBE.build_record(412, 0, schedule_seed=2609)
    assert set(record["canonical_shortcut_fit"]) == set(GEN.CANONICAL_SHORTCUTS)
    assert all(
        item["fits_all"] for item in record["canonical_shortcut_fit"].values()
    )
    assert all(record["disagrees_with_intended"].values())
    assert record["schedule_rotation_probe"]["rotation_count"] == 96
    assert record["schedule_rotation_probe"]["ambiguity_count"] == 0
    assert all(
        item["ambiguity_count"] == 0
        for item in record["schedule_rotation_probe"]["by_rival"].values()
    )


def test_generation_and_semantic_helpers_are_deterministic_fresh_and_pure():
    for band in BANDS:
        for index in range(12):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            assert first == original
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
                assert first == original
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == original


def test_actual_racket_outputs_match_independent_rule_when_runtime_is_available():
    from arcpuzzles import Catalog

    grids = [pair["input"] for pair in canonical()]
    grids.extend(GEN.generate(319, index) for index in range(12))
    receipt = Catalog(find_root(__file__)).apply(
        TASK_ID,
        grids,
        reference="canonical",
        timeout=180,
        allow_unapproved=True,
    )
    assert receipt["rule_hash_matches_catalog"]
    assert all(item["error"] is None and item["valid_output"] for item in receipt["results"])
    assert [item["output"] for item in receipt["results"]] == [
        independent_rule(grid) for grid in grids
    ]


def test_difficulty_bands_change_layout_without_changing_scheduled_semantics():
    grids = {
        band: GEN.generate(2741, 5, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({tuple(tuple(row) for row in grid) for grid in grids.values()}) == 3
    assert len({tuple(independent_observed(grid).items()) for grid in grids.values()}) == 1
    assert all(GEN.self_check(grid, difficulty=band) == [] for band, grid in grids.items())


def test_component_selector_family_probe_discovers_and_refutes_shortcut_families():
    """Search families, rather than relying only on hand-declared rivals."""
    probe_path = TASK_DIR / "workspace" / "probe_component_selectors.py"
    assert probe_path.exists(), "component-selector family probe is missing"
    spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}_component_selector_probe", probe_path
    )
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    record = probe.build_record(schedule_seed=2609)
    fitting = set(record["canonical_fitting_candidates"])
    assert {
        "size_at_least_2",
        "size_at_least_3",
        "size_at_least_4",
        "size_at_most_6",
        "largest_only",
        "smallest_only",
        "topmost_only",
        "mirror_only_when_single_component",
        "mirror_only_when_total_at_most_6",
    } <= fitting
    assert record["all_candidate_count"] >= 70
    assert record["canonical_fitting_candidate_count"] >= 20
    assert record["rotation_probe"]["rotation_count"] == 96
    assert record["rotation_probe"]["ambiguity_count"] == 0
    assert all(
        item["ambiguity_count"] == 0
        for item in record["rotation_probe"]["by_candidate"].values()
    )


def test_component_selector_probe_derives_component_sizes_independently():
    """Legacy generator observables need not expose the probe's diagnostics."""
    probe_path = TASK_DIR / "workspace" / "probe_component_selectors.py"
    spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}_component_selector_legacy_probe", probe_path
    )
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    def grid_for(size):
        grid = [[0] * 7 for _ in range(3)]
        for row in range(3):
            grid[row][3] = 5
        for col in range(size):
            grid[1][2 - col] = 6
        return grid

    class LegacyObservableGenerator:
        LESSON_SCHEDULE_PERIOD = 1
        EXAMPLES_NEEDED = 1

        @staticmethod
        def generate(seed, sample_index, difficulty=None):
            del seed, difficulty
            return grid_for(2 if sample_index == 0 else 1)

        @staticmethod
        def rule_mirror(grid):
            return probe._mirror_selected(grid, lambda components: components)

        @staticmethod
        def semantic_observables(grid):
            return {"n_components": len(probe._components(grid))}

    record = probe._rotation_probe(
        LegacyObservableGenerator,
        {"drop_singletons": probe._predicate_rule(lambda part: len(part) >= 2)},
        schedule_seed=1,
    )
    assert record["ambiguity_count"] == 3
    ambiguities = record["by_candidate"]["drop_singletons"]["ambiguities"]
    assert {tuple(item["query_component_sizes"]) for item in ambiguities} == {(1,)}
