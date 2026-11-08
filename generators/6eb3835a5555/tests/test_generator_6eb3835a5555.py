from __future__ import annotations

import copy
import importlib.util
import random
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root

TASK_ID = "6eb3835a5555"
MODULE_PATH = REPO / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", MODULE_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)


def pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def labelled(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_metadata_and_axis_contract_are_current_and_minimal():
    assert GEN.RULE_HASH == "2944822b1e33"
    assert GEN.SUMMARY == (
        "Fill each gray-wall room when it contains exactly one distinct seed color; "
        "leave empty or multi-color rooms unchanged."
    )
    assert set(GEN.AXES) == {"scene_profile"}
    assert tuple(GEN.AXES["scene_profile"]["valid"].split("|")) == GEN.SCENE_PROFILES
    assert GEN.HELPFUL_TEXTURES == GEN.DEGENERATE_TEXTURES == GEN.LAWFUL_DEGENERATE_TEXTURES == ()


def test_rule_mirror_matches_every_canonical_pair_and_self_check_accepts_inputs():
    assert len(pairs()) == 3
    for pair in pairs():
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_each_default_draw_is_lawful_and_refutes_both_key_rival_families(difficulty):
    for sample_index in range(len(GEN.SCENE_PROFILES) * 2):
        grid = GEN.generate(107, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        assert GEN.SEMANTIC_WITNESSES["repeated_same_color_room"](grid)
        assert GEN.SEMANTIC_WITNESSES["conflicting_seed_colors"](grid)
        intended = GEN.rule_mirror(grid)
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert rival(grid) != intended, (difficulty, sample_index, name)


def test_every_profile_is_an_exact_observable_override():
    realized = set()
    for profile in GEN.SCENE_PROFILES:
        grid = GEN.generate(211, 3, difficulty="hard", scene_profile=profile)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {"scene_profile": profile}
        assert GEN.generate(211, 3, difficulty="hard", scene_profile=profile) == grid
        realized.add(frozen(grid))
    assert len(realized) == len(GEN.SCENE_PROFILES)


def test_default_schedule_anchors_both_exact_canonical_profiles_in_every_band():
    canonical_profiles = {(7, 8, 6), (7, 9, 6)}
    for difficulty in ("easy", "medium", "hard"):
        observed = []
        for sample_index in range(len(GEN.SCENE_PROFILES)):
            grid = GEN.generate(313, sample_index, difficulty=difficulty)
            observed.append((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert canonical_profiles <= set(observed)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", -1])
def test_sample_index_rejects_invalid_scalars(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, bad)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "missing"},
        {"scene_profile": 1},
        {"texture": "default"},
        {"grid_h": 7},
        {"typo_axis": None},
        {"difficulty": "expert"},
    ],
)
def test_unknown_or_invalid_controls_fail_closed(kwargs):
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, difficulty=difficulty, **kwargs)


def test_exactly_one_seed_cell_is_a_real_canonical_shortcut_but_not_a_generated_shortcut():
    rival = GEN.CANONICAL_SHORTCUTS["exactly_one_seed_cell"]
    for pair in pairs():
        assert rival(pair["input"]) == pair["output"]
    witness = GEN.generate(419, 0, scene_profile="canonical_7x9")
    assert rival(witness) != GEN.rule_mirror(witness)


def test_generated_lessons_are_identifiable_under_every_query_rotation():
    lesson = [labelled(GEN.generate(521, index, difficulty="medium")) for index in range(5)]
    for query_index in range(len(lesson)):
        query = lesson[query_index]
        demos = lesson[:query_index] + lesson[query_index + 1 :]
        assert GEN.lesson_identifiable(demos, query) == []


def test_lesson_identifiable_detects_the_canonical_shortcut_when_demos_lack_repeat_witness():
    public = pairs()
    reasons = GEN.lesson_identifiable(public[:2], public[2])
    assert any("exactly_one_seed_cell" in reason for reason in reasons)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(991)
    state = random.getstate()
    first = GEN.generate(73, 6, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(73, 6, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 0
    assert GEN.generate(73, 6, difficulty="hard") == second
