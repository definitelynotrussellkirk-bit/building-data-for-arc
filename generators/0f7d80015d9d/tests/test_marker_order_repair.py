from __future__ import annotations

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "0f7d80015d9d"
ROOT = find_root(__file__)
gen, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _facts(grid):
    facts = gen._analyze(grid)
    assert facts["errors"] == []
    return facts


def test_marker_order_shortcut_is_declared_and_fits_every_canonical_pair():
    """Catches deleting the audited shortcut from canonical-shortcut evidence."""
    rival = gen.CANONICAL_SHORTCUTS["red_left_of_cyan"]
    pairs = canonical_pairs(TASK_ID, root=ROOT)

    assert len(pairs) == 4
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


def test_generated_same_side_profile_reverses_marker_order_and_midpoint_side():
    """Catches restoring red-right/cyan-midpoint, which teaches marker ordering."""
    width_three_seen = False
    for seed in range(128):
        grid = gen.generate(
            seed,
            3,
            grid_h=7,
            grid_w=7,
            rect_aspect="tall",
            scene_profile="right_same_side",
        )
        facts = _facts(grid)
        red_col = facts["red"][1]
        cyan_col = facts["cyan"][1]

        assert facts["scene_profile"] == "right_same_side"
        assert red_col == facts["midpoint"] < cyan_col
        assert gen.rule_mirror(grid) != gen._rival_red_left_of_cyan(grid)
        width_three_seen |= facts["rect_w"] == 3

    assert width_three_seen, "deterministic support probe never exercised width three"


def test_four_profile_lesson_refutes_every_declared_competitor():
    """Catches a declared rival surviving the actual four-demo teaching window."""
    demos = []
    for index, profile in enumerate(gen.SCHEDULE_PROFILES):
        grid = gen.generate(
            731,
            index,
            grid_h=11,
            grid_w=11,
            rect_aspect="wide",
            scene_profile=profile,
        )
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})

    query_grid = gen.generate(
        731,
        4,
        grid_h=13,
        grid_w=13,
        rect_aspect="tall",
        scene_profile="right_opposite",
    )

    assert gen.lesson_identifiable(demos, {"input": query_grid}) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(
            rival(demo["input"]) != demo["output"] for demo in demos
        ), f"declared competitor survived: {name}"
