from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, _generator_path, _generator_sha256 = load_selected_generator("abee0b4bed48", root=ROOT)


def _canonical_pairs():
    return canonical_pairs("abee0b4bed48", root=ROOT)


def _first_zero(grid):
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0:
                return row, col
    raise AssertionError("test grid unexpectedly has no background cell")


def test_canonical_pairs_are_accepted_and_mirrored_exactly():
    for pair in _canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"], "analysis/mirror must not mutate the input"


def test_every_declared_profile_is_exactly_observable_and_fresh():
    for index, profile in enumerate(gen.SCENE_PROFILES):
        kwargs = dict(
            seed=10_000 + index,
            sample_index=20_000 + index,
            difficulty=("easy", "medium", "hard")[index % 3],
            scene_profile=profile,
        )
        first = gen.generate(**kwargs)
        second = gen.generate(**kwargs)
        assert first == second
        assert first is not second
        assert all(left is not right for left, right in zip(first, second))
        assert gen.observe_overrides(first) == {"scene_profile": profile}
        assert gen.self_check(
            first,
            meta={"overrides": {"scene_profile": profile}},
        ) == []
        first[0][0] = 9
        assert gen.generate(**kwargs) == second, "returned grids must not share state"


def test_generation_preserves_process_global_rng_state():
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(43, 71, difficulty="hard")
    after = random.getstate()
    second = gen.generate(43, 71, difficulty="hard")
    assert before == after
    assert first == second


def test_structural_impostors_are_rejected_without_crashing():
    base = gen.generate(
        321,
        654,
        difficulty="medium",
        scene_profile="all_labels",
    )
    impostors = {}

    illegal_color = copy.deepcopy(base)
    row, col = _first_zero(illegal_color)
    illegal_color[row][col] = 2  # preserve every gray-cell branch count
    impostors["illegal nuisance color"] = illegal_color

    empty_zone = copy.deepcopy(base)
    for row in range(3):
        for col in range(3):
            empty_zone[row][col] = 0
    impostors["empty zone"] = empty_zone

    two_cell_zone = copy.deepcopy(base)
    for row in range(3):
        for col in range(3):
            two_cell_zone[row][col] = 0
    two_cell_zone[0][0] = 5
    two_cell_zone[2][2] = 5
    impostors["two-cell zone"] = two_cell_zone

    unlinked = [[0 for _ in base[0]] for _ in range(3)]
    for zone in range(len(base[0]) // 3):
        for col in range(3):
            unlinked[1][3 * zone + col] = 5
    impostors["unrecognized all-middle-row lesson"] = unlinked

    ragged = copy.deepcopy(base)
    ragged[1].pop()
    impostors["ragged grid"] = ragged

    for label, grid in impostors.items():
        errors = gen.self_check(grid)
        assert errors, f"self_check accepted targeted impostor: {label}"


def test_distribution_breaks_position_ring_and_middle_row_shortcuts():
    one_positions = set()
    eight_holes = set()
    other_shapes = set()
    count3_branches = set()

    for seed in range(120):
        for profile in (
            "one_position_pair",
            "eight_hole_pair",
            "other_shape_pair",
            "canonical_diagonals",
            "count3_six",
        ):
            grid = gen.generate(
                seed,
                9_000 + seed,
                difficulty="hard",
                scene_profile=profile,
            )
            analysis = gen._analysis(grid)
            assert analysis["errors"] == []
            for record in analysis["records"]:
                if record["one_position"] is not None:
                    one_positions.add(record["one_position"])
                if record["eight_hole"] is not None:
                    eight_holes.add(record["eight_hole"])
                if record["other_shape"] is not None:
                    other_shapes.add(record["other_shape"])
                if record["kind"] in {"top", "bottom", "other"}:
                    count3_branches.add(record["kind"])

    assert one_positions == set(gen._ALL_CELLS)
    assert eight_holes == set(gen._ALL_CELLS)
    assert len(other_shapes) >= 70
    assert gen._MAIN_DIAGONAL in other_shapes
    assert gen._ANTI_DIAGONAL in other_shapes
    assert gen._MIDDLE in other_shapes
    assert count3_branches == {"top", "bottom", "other"}


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=True)
    with pytest.raises(ValueError, match="override"):
        gen.generate(1, 2, scene_profile="not_a_profile")
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 2, difficulty="impossible")
