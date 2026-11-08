from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "72b99d3a9be8"
ROOT = find_root(__file__)
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def test_every_canonical_input_is_in_the_rule_domain() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 10
    assert all(gen.self_check(pair["input"]) == [] for pair in pairs)


def test_unknown_override_is_rejected_without_perturbing_valid_draws() -> None:
    before = gen.generate(9, 3, difficulty="medium")
    with pytest.raises(TypeError, match="unknown override axis"):
        gen.generate(9, 3, difficulty="medium", wall_orientaton="vertical")
    assert gen.generate(9, 3, difficulty="medium") == before


@pytest.mark.parametrize("orientation", ["horizontal", "vertical"])
def test_forced_bounce_wall_orientation_is_observable(orientation: str) -> None:
    grid = gen.generate(
        23,
        7,
        difficulty="medium",
        grid_h=18,
        grid_w=19,
        diagonal="down_right",
        wall_orientation=orientation,
        n_bars=4,
    )
    facts = gen.trace_rule(grid, reflector_color=2)
    assert gen.self_check(grid) == []
    assert facts["bounce_events"]
    assert facts["bounce_events"][0]["orientation"] == orientation
    assert facts["crossed_colors"] >= {2, 3}
    assert (len(grid), len(grid[0])) == (18, 19)


def test_normal_schedule_exercises_both_reflection_axes() -> None:
    seen = set()
    for sample_index in range(32):
        grid = gen.generate(101, sample_index, difficulty="medium")
        facts = gen.trace_rule(grid, reflector_color=2)
        seen.update(event["orientation"] for event in facts["bounce_events"])
    assert seen == {"horizontal", "vertical"}


def test_python_mirror_matches_saved_canonical_labels() -> None:
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True):
        assert gen.rule_mirror(pair["input"]) == pair["output"]
