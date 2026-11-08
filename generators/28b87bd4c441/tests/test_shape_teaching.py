from __future__ import annotations

import copy
import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, _, _ = load_selected_generator("28b87bd4c441", root=ROOT)


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(gen.TASK_ID, root=ROOT)]


def test_canonical_inputs_are_owned_and_strict():
    inputs = _canonical_inputs()
    assert len(inputs) == 4
    for grid in inputs:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_every_profile_is_exactly_observable_and_deterministic():
    for profile in gen.PROFILE_NAMES:
        first = gen.generate(17, 4, difficulty="hard", scene_profile=profile)
        second = gen.generate(17, 4, difficulty="hard", scene_profile=profile)
        assert first == second
        assert first is not second
        assert gen.self_check(first, difficulty="hard") == []
        assert gen.observe_overrides(first) == {"scene_profile": profile}
        assert gen.rule_mirror(first) != first


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis="x")


def test_self_check_rejects_decisive_mutations():
    grid = gen.generate(3, 1, scene_profile="canonical_down_right_l4")

    missing_marker = copy.deepcopy(grid)
    for row in missing_marker:
        for c, value in enumerate(row):
            if value == 2:
                row[c] = 0
    assert any("marker" in error for error in gen.self_check(missing_marker))

    disconnected = copy.deepcopy(grid)
    blob = [(r, c) for r, row in enumerate(disconnected) for c, value in enumerate(row) if value == 5]
    r, c = blob[-1]
    disconnected[r][c] = 0
    disconnected[0][-1] = 5
    assert any("four-connected" in error for error in gen.self_check(disconnected))

    wrong_color = copy.deepcopy(grid)
    r, c = blob[0]
    wrong_color[r][c] = 3
    assert any("only colors" in error for error in gen.self_check(wrong_color))

    second_marker = copy.deepcopy(grid)
    for r, row in enumerate(second_marker):
        for c, value in enumerate(row):
            if value == 0:
                second_marker[r][c] = 2
                break
        else:
            continue
        break
    assert any("exactly one" in error for error in gen.self_check(second_marker))


def test_hollow_anchor_and_axis_profiles_kill_public_shortcuts():
    hollow = gen.generate(9, 2, scene_profile="row_left_hollow_l3")
    assert gen._witness_hollow_bbox_anchor(hollow)
    assert gen._rival_first_blob_cell_anchor(hollow) != gen.rule_mirror(hollow)
    assert gen._rival_diagonal_only(hollow) != gen.rule_mirror(hollow)


def test_full_profile_cycle_is_identifiable():
    seed = 0
    demos = []
    for sample_index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, sample_index)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, gen.EXAMPLES_NEEDED)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []


def _template_key_and_shape(pair):
    """Fit the shortcut from visible labels, independently of generator helpers."""
    grid, output = pair["input"], pair["output"]
    gray = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 5]
    marker, = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 2]
    top, left = min(r for r, _ in gray), min(c for _, c in gray)
    sign = lambda value: (value > 0) - (value < 0)
    key = (len(grid), len(grid[0]), sign(marker[0] - top), sign(marker[1] - left))
    shape = tuple((r - marker[0], c - marker[1])
                  for r, row in enumerate(output) for c, color in enumerate(row) if color == 5)
    return key, shape


def test_canonical_query_has_an_observable_generated_profile():
    """The canonical U has two top tips; it must not be replaced by the P template."""
    query = _canonical_inputs()[-1]
    assert gen.observe_overrides(query) == {"scene_profile": "canonical_up_left_u5"}
    grid = gen.generate(17, 0, scene_profile="canonical_up_left_u5")
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    assert {(r - top, c - left) for r, c in cells} == {(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)}
    assert gen.strict_canonical_like(grid) == []
    assert gen.canonical_profile_signature(grid) == "canonical_up_left_u5"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_schedule_phase_refutes_dimension_and_direction_templates(difficulty):
    """No full ordered lesson may teach one output shape per size and direction."""
    seed = 17
    for start in range(len(gen.SCHEDULE_PROFILES)):
        demos = []
        shapes = {}
        for index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(seed, index, difficulty=difficulty)
            pair = {"input": grid, "output": gen.rule_mirror(grid)}
            demos.append(pair)
            key, shape = _template_key_and_shape(pair)
            shapes.setdefault(key, set()).add(shape)
        assert any(len(variants) >= 2 for variants in shapes.values()), shapes
        query = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
        assert gen.lesson_identifiable(demos, {"input": query}) == []
        # A query label is controller-private and cannot influence the teaching verdict.
        assert gen.lesson_identifiable(demos, {"input": query, "output": [[9]]}) == []


def test_single_template_lesson_is_explicitly_rejected():
    """Repeating old P examples cannot substitute for a shape-copying witness."""
    old_profiles = [name for name in gen.PROFILE_NAMES if not name.endswith("_u5")
                    or name == "row_right_hollow_u5"]
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(3, index, scene_profile=old_profiles[index % len(old_profiles)])
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    reasons = gen.lesson_identifiable(demos, {"input": _canonical_inputs()[-1]})
    assert any("dimension" in reason and "template" in reason for reason in reasons), reasons


@pytest.mark.parametrize("replacement", [False, 0.0])
def test_demo_labels_require_literal_integer_colors(replacement):
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(0, index)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    output = demos[0]["output"]
    r, c = next((r, c) for r, row in enumerate(output)
                for c, value in enumerate(row) if value == 0)
    output[r][c] = replacement
    query = gen.generate(0, gen.EXAMPLES_NEEDED)
    assert any("output" in reason for reason in gen.lesson_identifiable(demos, {"input": query}))
