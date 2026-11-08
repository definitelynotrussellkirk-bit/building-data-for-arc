from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_ID = "611cc0f4e0fe"
EXPECTED_PROFILES = (
    "canonical_opposite_slopes",
    "same_slope_pairs",
    "off_slope_decoy",
    "three_pairs",
)
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = REPO / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row() -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _grid(rows) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


def _signature(grid: list[list[int]]) -> tuple[int, int, int]:
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _canonical_signatures() -> set[tuple[int, int, int]]:
    row = _canonical_row()
    return {
        _signature(_grid(pair["input"]))
        for pair in [*row["train"], *row["test"]]
    }


def test_public_contract_is_one_observable_scene_profile() -> None:
    generator = _load_generator()
    assert getattr(generator, "RULE_HASH", None) == "51d7c63afd4f"
    assert tuple(getattr(generator, "SCENE_PROFILES", ())) == EXPECTED_PROFILES
    assert set(generator.AXES) == {"scene_profile"}
    assert callable(getattr(generator, "schedule_profile", None))
    assert callable(getattr(generator, "observe_overrides", None))
    assert getattr(generator, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == ()
    assert getattr(generator, "HELPFUL_TEXTURES", None) == ()
    assert getattr(generator, "DEGENERATE_TEXTURES", None) == ()


def test_unknown_or_invalid_override_is_rejected() -> None:
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, difficulty="medium", typo_profile="three_pairs")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        generator.generate(0, 0, difficulty="medium", scene_profile="not_a_profile")


def test_four_consecutive_examples_cover_every_profile() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            observed = {
                generator.schedule_profile(123, start + offset, band)
                for offset in range(len(EXPECTED_PROFILES))
            }
            assert observed == set(EXPECTED_PROFILES)


@pytest.mark.parametrize("profile", EXPECTED_PROFILES)
def test_profile_override_is_exactly_observable(profile: str) -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        for seed in range(4):
            grid = generator.generate(
                seed, 5, difficulty=band, scene_profile=profile
            )
            assert generator.observe_overrides(grid) == {"scene_profile": profile}
            assert generator.self_check(grid, difficulty=band) == []
            assert generator.rule_mirror(grid) != grid


def test_each_band_has_canonical_profile_support_in_every_four_draws() -> None:
    generator = _load_generator()
    signatures = _canonical_signatures()
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            grids = [
                generator.generate(23, start + offset, difficulty=band)
                for offset in range(len(EXPECTED_PROFILES))
            ]
            assert any(
                generator.observe_overrides(grid)["scene_profile"]
                == "canonical_opposite_slopes"
                and _signature(grid) in signatures
                for grid in grids
            )


def test_three_of_four_profiles_retain_exact_canonical_shape_palette_support() -> None:
    generator = _load_generator()
    signatures = _canonical_signatures()
    for band in ("easy", "medium", "hard"):
        for profile in EXPECTED_PROFILES[:3]:
            for seed in range(8):
                grid = generator.generate(
                    seed, 0, difficulty=band, scene_profile=profile
                )
                assert _signature(grid) in signatures


def test_profiles_have_the_declared_semantic_structure() -> None:
    generator = _load_generator()
    expected = {
        "canonical_opposite_slopes": {
            "diagonal_pair_count": 2,
            "positive_slope_pair_count": 1,
            "negative_slope_pair_count": 1,
            "off_slope_pair_count": 0,
        },
        "same_slope_pairs": {
            "diagonal_pair_count": 2,
            "off_slope_pair_count": 0,
        },
        "off_slope_decoy": {
            "diagonal_pair_count": 1,
            "off_slope_pair_count": 1,
        },
        "three_pairs": {
            "diagonal_pair_count": 3,
            "positive_slope_pair_count": 2,
            "negative_slope_pair_count": 1,
            "off_slope_pair_count": 0,
        },
    }
    for profile, requirements in expected.items():
        grid = generator.generate(
            31, 2, difficulty="medium", scene_profile=profile
        )
        analysis = generator.analyze_grid(grid)
        for key, value in requirements.items():
            assert analysis[key] == value, (profile, key, analysis)
        if profile == "same_slope_pairs":
            slope_counts = {
                analysis["positive_slope_pair_count"],
                analysis["negative_slope_pair_count"],
            }
            assert slope_counts == {0, 2}


def test_rule_mirror_matches_all_canonical_pairs_and_strict_grammar() -> None:
    generator = _load_generator()
    row = _canonical_row()
    for pair in [*row["train"], *row["test"]]:
        input_grid = _grid(pair["input"])
        output_grid = _grid(pair["output"])
        assert generator.rule_mirror(input_grid) == output_grid
        assert generator.strict_canonical_like(input_grid) == []
        assert generator.self_check(input_grid) == []
        assert generator.observe_overrides(input_grid) == {
            "scene_profile": "canonical_opposite_slopes"
        }


def test_self_check_rejects_blank_axis_aligned_and_shallow_diagonal_impostors() -> None:
    generator = _load_generator()
    blank = [[0] * 7 for _ in range(7)]
    axis = [[0] * 7 for _ in range(7)]
    axis[1][1] = axis[1][5] = 2
    axis[5][1] = axis[5][5] = 4
    shallow = [[0] * 7 for _ in range(7)]
    shallow[0][0] = shallow[4][2] = 2
    shallow[1][6] = shallow[5][4] = 4

    assert generator.self_check(blank)
    assert generator.self_check(axis)
    assert generator.self_check(shallow)


def test_exact_non45_witness_refutes_connect_every_pair_rival() -> None:
    generator = _load_generator()
    witness = [
        [2, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 4],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    intended = [
        [2, 0, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 0, 4],
        [0, 0, 2, 0, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    assert generator.observe_overrides(witness) == {
        "scene_profile": "off_slope_decoy"
    }
    assert generator.self_check(witness) == []
    assert generator.rule_mirror(witness) == intended
    rival = generator.SEMANTIC_RIVALS["connect_every_repeated_pair_with_bresenham"]
    assert rival(witness) != intended


def test_one_scheduled_lesson_refutes_every_declared_rival() -> None:
    generator = _load_generator()
    demos = []
    for sample_index in range(len(EXPECTED_PROFILES)):
        input_grid = generator.generate(44, sample_index, difficulty="medium")
        demos.append({"input": input_grid, "output": generator.rule_mirror(input_grid)})
    query_input = generator.generate(44, len(EXPECTED_PROFILES), difficulty="medium")
    query = {"input": query_input, "output": generator.rule_mirror(query_input)}

    assert generator.lesson_identifiable(demos, query) == []
    for name, rival in generator.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_generation_is_deterministic_and_band_keyed() -> None:
    generator = _load_generator()
    for profile in EXPECTED_PROFILES:
        same = generator.generate(73, 1, difficulty="medium", scene_profile=profile)
        assert same == generator.generate(
            73, 1, difficulty="medium", scene_profile=profile
        )
        dimensions = {
            (
                len(generator.generate(73, 1, difficulty=band, scene_profile=profile)),
                len(generator.generate(73, 1, difficulty=band, scene_profile=profile)[0]),
            )
            for band in ("easy", "medium", "hard")
        }
        assert dimensions == {(7, 7), (8, 10), (10, 10)}


def test_declared_strict_floor_allows_pinned_census_variance() -> None:
    generator = _load_generator()
    # The exact canonical profile is one of four scheduled branches, but the
    # semantic census deliberately samples non-lockstep residues.  A 20% floor
    # is a conservative honest lower bound for that nominal 25% curriculum.
    assert generator.MIN_STRICT_FRAC == pytest.approx(0.20)
