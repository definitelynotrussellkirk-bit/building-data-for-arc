"""Semantic regressions for connectivity witnesses and teachable lessons."""
import copy
import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "33275a4aae3e"
STEP_PROFILES = ("stepped_l_22x25", "stepped_r_22x25")

@pytest.fixture(scope="module")
def generator():
    return load_selected_generator(TASK_ID, root=find_root(__file__))[0]

def test_rivals_fit_every_usable_canonical_pair(generator):
    assert hasattr(generator, "CANONICAL_SHORTCUTS"), "Executable canonical rivals are required"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 8
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], (name, pair["variant"], pair["split"], pair["pair_index"])

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", STEP_PROFILES)
def test_stepped_profiles_are_lawful_observable_counterexamples(generator, band, profile):
    assert profile in generator.SCENE_PROFILES, "Production needs the stepped counterexample family"
    for seed in range(5):
        grid = generator.generate(seed, 3, difficulty=band, scene_profile=profile)
        original = copy.deepcopy(grid)
        assert generator.self_check(grid) == []
        assert generator.observe_overrides(grid) == {"scene_profile": profile}
        expected = generator.solve_python(grid)
        for name, rival in generator.CANONICAL_SHORTCUTS.items():
            assert rival(grid) != expected, name
        assert grid == original

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_rotation_retains_a_counterexample_in_three_demos(generator, band):
    assert getattr(generator, "EXAMPLES_NEEDED", None) == 3
    assert getattr(generator, "LESSON_SCHEDULE_PERIOD", None) == 2
    for start in range(4):
        pairs = []
        for index in range(start, start + 4):
            grid = generator.generate(17, index, difficulty=band)
            pairs.append({"input": grid, "output": generator.solve_python(grid)})
            is_step = generator.observe_overrides(grid)["scene_profile"] in STEP_PROFILES
            assert is_step == (index % 2 == 0)
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            assert generator.lesson_identifiable(demos, query) == []
            for name, rival in generator.CANONICAL_SHORTCUTS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name

def test_lesson_hook_detects_unwitnessed_query_ambiguity(generator):
    assert hasattr(generator, "lesson_identifiable"), "Need an executable lesson contract"
    demos = []
    for index in range(3):
        grid = generator.generate(17, index, scene_profile="two_room_lr_22x25")
        demos.append({"input": grid, "output": generator.solve_python(grid)})
    query_grid = generator.generate(17, 3, scene_profile=STEP_PROFILES[0])
    reasons = generator.lesson_identifiable(demos, {"input": query_grid, "output": generator.solve_python(query_grid)})
    for name in generator.CANONICAL_SHORTCUTS:
        assert any(name in reason for reason in reasons), (name, reasons)

def test_strict_hook_accepts_all_canonical_inputs(generator):
    assert hasattr(generator, "strict_canonical_like")
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True):
        assert generator.strict_canonical_like(pair["input"]) == []


def test_null_scene_profile_preserves_default_schedule(generator):
    # GenCtx treats None as an absent override; the generator must do likewise.
    for index in range(4):
        assert generator.generate(3, index, scene_profile=None) == generator.generate(3, index)
