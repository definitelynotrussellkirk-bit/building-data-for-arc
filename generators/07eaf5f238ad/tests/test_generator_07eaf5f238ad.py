from __future__ import annotations

import copy
import importlib.util
import json
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "07eaf5f238ad"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CANONICAL_PROFILES = {(8, 10, 3), (11, 11, 4), (11, 12, 4)}
TEXTURES = (
    "plain",
    "absent_color",
    "repeat_header",
    "first_wins",
    "decoy_colors",
    "rich",
)


def _palette_size(grid):
    return len({value for row in grid for value in row})


def _lesson(seed: int, start: int, difficulty: str):
    pairs = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    return pairs[: GEN.EXAMPLES_NEEDED], pairs[-1]


def test_rule_pin_and_canonical_outputs_are_exact():
    assert GEN.RULE_HASH == "d10bfd060d8f"
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_boundaries_and_textures_are_observable():
    cases = [
        {"grid_h": 8, "grid_w": 10, "n_header": 2, "texture": "plain"},
        {"grid_h": 16, "grid_w": 18, "n_header": 4, "texture": "rich"},
    ]
    cases.extend(
        {"grid_h": 11, "grid_w": 12, "n_header": 3, "texture": texture}
        for texture in TEXTURES
    )
    for index, requested in enumerate(cases):
        grid = GEN.generate(5100 + index, index, difficulty="easy", **requested)
        assert GEN.self_check(grid, meta={"overrides": requested}) == []
        assert GEN.observe_overrides(grid) == requested

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(0, 0, typo_axis=3)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_schedule_hits_every_canonical_profile_and_rich_witness(difficulty):
    seen_profiles = set()
    for sample_index in range(6):
        grid = GEN.generate(711, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        profile = (len(grid), len(grid[0]), _palette_size(grid))
        if profile in CANONICAL_PROFILES:
            seen_profiles.add(profile)
        if sample_index % 2 == 0:
            assert GEN.observe_overrides(grid)["texture"] == "rich"
            intended = GEN.rule_mirror(grid)
            assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
            assert all(
                rival(grid) != intended for rival in GEN.SEMANTIC_RIVALS.values()
            )
    assert seen_profiles == CANONICAL_PROFILES


def test_retained_deduplicate_header_counterexample_is_exact():
    path = (
        ROOT
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "deduplicate_header.json"
    )
    case = json.loads(path.read_text())
    grid = case["input"]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == case["intended_output"]
    assert GEN.CANONICAL_SHORTCUTS["deduplicate_header"](grid) == case[
        "deduplicate_header_output"
    ]
    assert case["intended_output"] != case["deduplicate_header_output"]


def test_declared_canonical_shortcuts_are_real_and_have_counterexamples():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert {
        "deduplicate_header",
        "last_object_of_color",
        "require_all_header_colors",
        "append_non_header_objects",
    } <= set(GEN.CANONICAL_SHORTCUTS)

    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert shortcut(pair["input"]) == pair["output"], name
        rich = GEN.generate(808, 0, difficulty="medium")
        assert shortcut(rich) != GEN.rule_mirror(rich), name


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_sliding_lesson_and_rotation_refutes_named_competitors(difficulty):
    for start in range(6):
        demos, query = _lesson(404, start, difficulty)
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name

        all_pairs = [*demos, query]
        for held_out in range(len(all_pairs)):
            rotated_demos = [
                pair for index, pair in enumerate(all_pairs) if index != held_out
            ]
            assert GEN.lesson_identifiable(
                rotated_demos, all_pairs[held_out]
            ) == []


def test_self_check_rejects_structural_impostors():
    full_one_color = [[1] * 10 for _ in range(8)]
    assert GEN.self_check(full_one_color)

    valid = GEN.generate(99, 0, difficulty="medium")
    contaminated_gap = copy.deepcopy(valid)
    contaminated_gap[1][0] = 9
    assert GEN.self_check(contaminated_gap)

    touching_objects = copy.deepcopy(valid)
    # Force two different colours to touch inside the body.
    body_points = [
        (r, c)
        for r in range(2, len(touching_objects))
        for c, value in enumerate(touching_objects[r])
        if value
    ]
    r, c = body_points[0]
    neighbour = (r, c + 1 if c + 1 < len(touching_objects[0]) else c - 1)
    touching_objects[neighbour[0]][neighbour[1]] = (
        touching_objects[r][c] % 9
    ) + 1
    assert GEN.self_check(touching_objects)


def test_generation_is_deterministic_fresh_and_global_random_pure():
    random.seed(314159)
    state = random.getstate()
    first = GEN.generate(12345, 7, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(12345, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
