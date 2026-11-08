from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

TASK_ID = "85782e8a5dc9"
EXPECTED_RULE_HASH = "8de2ee81f8fa"
EXPECTED_PROFILES = (
    "quarter_turn",
    "half_turn_color_key",
    "axis_reflection",
    "diagonal_reflection",
)
EXPECTED_SCHEDULE = (
    "quarter_turn",
    "half_turn_color_key",
    "quarter_turn",
    "half_turn_color_key",
    "axis_reflection",
    "quarter_turn",
    "half_turn_color_key",
    "quarter_turn",
    "half_turn_color_key",
    "diagonal_reflection",
)
EXPECTED_TRANSFORMS = {
    "rot90",
    "rot180",
    "flip_lr",
    "flip_ud",
    "transpose",
    "anti_transpose",
}

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _signature(grid: list[list[int]]) -> tuple[int, int, int]:
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def test_public_contract_is_small_exact_and_rule_bound() -> None:
    generator = _load_generator()
    assert generator.RULE_HASH == EXPECTED_RULE_HASH
    assert tuple(generator.SCENE_PROFILES) == EXPECTED_PROFILES
    assert set(generator.AXES) == {"scene_profile"}
    assert generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert generator.MIN_STRICT_FRAC == 1.0
    assert generator.EXAMPLES_NEEDED == 4
    assert callable(generator.schedule_profile)
    assert callable(generator.observe_overrides)
    assert callable(generator.rule_mirror)
    assert callable(generator.lesson_identifiable)


def test_unknown_or_invalid_override_fails_loudly() -> None:
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, typo_profile="quarter_turn")
    with pytest.raises(ValueError, match="scene_profile"):
        generator.generate(0, 0, scene_profile="identity")
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(0, 0, difficulty="nightmare")


def test_schedule_redundantly_covers_query_rotation_witnesses() -> None:
    generator = _load_generator()
    for band in (None, "easy", "medium", "hard"):
        observed_period = tuple(
            generator.schedule_profile(991, sample_index, band)
            for sample_index in range(len(EXPECTED_SCHEDULE))
        )
        assert observed_period == EXPECTED_SCHEDULE
        for start in range(20):
            window = [
                generator.schedule_profile(991, start + offset, band)
                for offset in range(generator.EXAMPLES_NEEDED + 1)
            ]
            assert window.count("quarter_turn") >= 2
            assert window.count("half_turn_color_key") >= 2


@pytest.mark.parametrize("profile", EXPECTED_PROFILES)
def test_profile_override_is_exactly_observable(profile: str) -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        grid = generator.generate(17, 9, difficulty=band, scene_profile=profile)
        assert generator.observe_overrides(grid) == {"scene_profile": profile}
        assert generator.self_check(grid, difficulty=band) == []
        assert generator.strict_canonical_like(grid) == []


def test_canonical_pairs_are_accepted_and_python_mirror_matches_authority() -> None:
    generator = _load_generator()
    for pair in _canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_default_distribution_stays_on_exact_canonical_shape_palette_profiles() -> None:
    generator = _load_generator()
    signatures = {_signature(pair["input"]) for pair in _canonical_pairs()}
    assert signatures == {(6, 20, 3), (6, 20, 4), (6, 20, 5)}
    seen = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for sample_index in range(8):
                grid = generator.generate(seed, sample_index, difficulty=band)
                seen.add(_signature(grid))
                assert _signature(grid) in signatures
                assert generator.self_check(grid, difficulty=band) == []
    assert seen == signatures


def test_all_six_selected_nonidentity_transforms_are_generated() -> None:
    generator = _load_generator()
    seen = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(64):
            for sample_index in range(10):
                grid = generator.generate(seed, sample_index, difficulty=band)
                seen.add(generator.analyze_grid(grid)["transform"])
    assert seen == EXPECTED_TRANSFORMS


def test_half_turn_profile_forces_color_aware_transform_inference() -> None:
    generator = _load_generator()
    for seed in range(16):
        grid = generator.generate(
            seed, 5, difficulty="medium", scene_profile="half_turn_color_key"
        )
        analysis = generator.analyze_grid(grid)
        assert analysis["transform"] == "rot180"
        assert analysis["a_mask"] == analysis["b_mask"]
        assert analysis["a"] != analysis["b"]
        assert (
            generator.SEMANTIC_RIVALS["infer_transform_from_occupancy_only"](grid)
            != generator.rule_mirror(grid)
        )


def test_generated_answer_is_transfer_to_c_not_copy_of_any_visible_interior() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        for profile in EXPECTED_PROFILES:
            for seed in range(8):
                grid = generator.generate(
                    seed, 3, difficulty=band, scene_profile=profile
                )
                analysis = generator.analyze_grid(grid)
                answer = generator.rule_mirror(grid)
                assert answer not in (analysis["a"], analysis["b"], analysis["c"])
                assert {
                    value for row in answer for value in row if value != 0
                } == {
                    value for row in analysis["c"] for value in row if value != 0
                }


def test_every_query_rotation_refutes_every_declared_rival() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        for start in range(20):
            pairs = []
            for offset in range(generator.EXAMPLES_NEEDED + 1):
                input_grid = generator.generate(
                    44, start + offset, difficulty=band
                )
                pairs.append(
                    {"input": input_grid, "output": generator.rule_mirror(input_grid)}
                )
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert generator.lesson_identifiable(demos, query) == []
                for name, rival in generator.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), (start, query_index, name)


def test_generation_is_deterministic_and_rule_helpers_are_input_pure() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        first = generator.generate(73, 11, difficulty=band)
        assert first == generator.generate(73, 11, difficulty=band)
        original = copy.deepcopy(first)
        generator.analyze_grid(first)
        generator.observe_overrides(first)
        generator.rule_mirror(first)
        for rival in generator.SEMANTIC_RIVALS.values():
            rival(first)
        assert first == original


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 20 for _ in range(6)],
        [[0] * 20 for _ in range(6)],
    ],
)
def test_malformed_or_off_manifold_grids_return_diagnostics(grid) -> None:
    generator = _load_generator()
    assert generator.self_check(grid)
