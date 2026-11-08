from __future__ import annotations

import importlib

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "6d26bc40cbb2"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_rule_hash_is_selected_canonical_source():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)


def test_all_canonical_inputs_are_owned_and_python_mirror_matches():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.solve_python(pair["input"]) == pair["output"]


def test_canonical_clipped_copy_is_valid_regression():
    pair = canonical_pairs(TASK_ID)[2]
    facts = gen.analyze_scene(pair["input"])["facts"]
    assert facts["copy_extent"] == "clipped"
    assert facts["clipped_count"] == 1
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 6},
        {"grid_h": 12},
        {"grid_w": 7},
        {"grid_w": 14},
        {"payload_size": 3},
        {"payload_size": 7},
        {"palette_size": 1},
        {"palette_size": 3},
        {"copy_extent": "fully_visible"},
        {"copy_extent": "clipped"},
        {
            "grid_h": 6,
            "grid_w": 7,
            "payload_size": 7,
            "palette_size": 3,
            "copy_extent": "clipped",
        },
        {
            "grid_h": 6,
            "grid_w": 7,
            "payload_size": 7,
            "palette_size": 3,
            "copy_extent": "fully_visible",
        },
    ],
)
def test_exact_override_boundaries_round_trip(overrides):
    grid = gen.generate(0x6D26, 17, difficulty="hard", **overrides)
    observed = gen.observe_overrides(grid)
    for axis, requested in overrides.items():
        assert observed[axis] == requested
    assert gen.strict_canonical_like(grid) == []


def test_unknown_override_key_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, typo_axis=3)


def test_self_check_rejects_four_structural_impostor_classes():
    valid = gen.generate(77, 11, difficulty="medium")
    markers = gen.analyze_scene(valid)["facts"]["markers"]

    one_marker = [row[:] for row in valid]
    one_marker[markers[0][0]][markers[0][1]] = 0
    assert gen.self_check(one_marker)

    three_markers = [row[:] for row in valid]
    for r, row in enumerate(three_markers):
        for c, value in enumerate(row):
            if value == 0:
                three_markers[r][c] = 9
                break
        else:
            continue
        break
    assert gen.self_check(three_markers)

    no_payload = [[9 if value == 9 else 0 for value in row] for row in valid]
    assert gen.self_check(no_payload)

    disconnected = [row[:] for row in valid]
    payload = set(gen.analyze_scene(valid)["facts"]["payload"])
    marker_set = set(markers)
    placed = False
    for r, row in enumerate(disconnected):
        for c, value in enumerate(row):
            if value != 0:
                continue
            if (r, c) in marker_set:
                continue
            if all(abs(r-pr) + abs(c-pc) != 1 for pr, pc in payload):
                disconnected[r][c] = 8
                placed = True
                break
        if placed:
            break
    assert placed
    assert gen.self_check(disconnected)


def test_generated_scene_refutes_core_rivals_and_multicolor_shortcut():
    grid = gen.generate(
        4242,
        19,
        difficulty="medium",
        palette_size=3,
        copy_extent="clipped",
    )
    authoritative = gen.solve_python(grid)
    assert gen.rival_remove_markers_only(grid) != authoritative
    assert gen.rival_move_instead_of_copy(grid) != authoritative
    assert gen.rival_reverse_vector_copy(grid) != authoritative
    assert gen.rival_modal_color_only(grid) != authoritative
