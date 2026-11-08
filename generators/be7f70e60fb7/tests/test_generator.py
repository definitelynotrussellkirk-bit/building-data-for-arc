from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_ID = "be7f70e60fb7"
EXPECTED_PROFILES = (
    "canonical_two_pairs",
    "canonical_three_pairs",
    "alignment_decoy",
    "cardinality_decoys",
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


def _grid(rows: list[str]) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


def _canonical_signatures() -> set[tuple[int, int, int]]:
    row = _canonical_row()
    signatures = set()
    for pair in [*row["train"], row["test"]]:
        grid = _grid(pair["input"])
        signatures.add(
            (len(grid), len(grid[0]), len({value for line in grid for value in line}))
        )
    return signatures


def test_public_contract_is_one_observable_scene_profile() -> None:
    generator = _load_generator()
    assert getattr(generator, "RULE_HASH", None) == "d264380c5850"
    assert tuple(getattr(generator, "SCENE_PROFILES", ())) == EXPECTED_PROFILES
    assert set(generator.AXES) == {"scene_profile"}
    assert callable(getattr(generator, "schedule_profile", None))
    assert callable(getattr(generator, "observe_overrides", None))
    assert getattr(generator, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == ()


def test_unknown_override_is_rejected() -> None:
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, difficulty="medium", typo_profile="alignment_decoy")


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
        grid = generator.generate(17, 5, difficulty=band, scene_profile=profile)
        assert generator.observe_overrides(grid) == {"scene_profile": profile}
        assert generator.self_check(grid, difficulty=band) == []


def test_default_generation_stays_on_canonical_shape_palette_support() -> None:
    generator = _load_generator()
    signatures = _canonical_signatures()
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            for sample_index in range(len(EXPECTED_PROFILES)):
                grid = generator.generate(seed, sample_index, difficulty=band)
                signature = (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
                assert signature in signatures
                assert generator.observe_overrides(grid)["scene_profile"] in EXPECTED_PROFILES
                assert generator.self_check(grid, difficulty=band) == []


def test_alignment_decoy_exercises_alignment_precondition() -> None:
    generator = _load_generator()
    grid = generator.generate(
        31, 2, difficulty="medium", scene_profile="alignment_decoy"
    )
    analysis = generator.analyze_grid(grid)
    assert analysis["aligned_pair_count"] == 2
    assert analysis["diagonal_pair_count"] == 1
    assert analysis["aligned_triple_count"] == 0
    assert analysis["singleton_count"] == 0
    assert generator.rule_mirror(grid) != grid


def test_cardinality_decoys_exercise_exactly_two_precondition() -> None:
    generator = _load_generator()
    grid = generator.generate(
        37, 3, difficulty="hard", scene_profile="cardinality_decoys"
    )
    analysis = generator.analyze_grid(grid)
    assert analysis["aligned_pair_count"] == 1
    assert analysis["diagonal_pair_count"] == 0
    assert analysis["aligned_triple_count"] == 1
    assert analysis["singleton_count"] == 1
    assert generator.rule_mirror(grid) != grid


def test_rule_mirror_matches_all_canonical_pairs() -> None:
    generator = _load_generator()
    row = _canonical_row()
    for pair in [*row["train"], row["test"]]:
        input_grid = _grid(pair["input"])
        output_grid = _grid(pair["output"])
        assert generator.rule_mirror(input_grid) == output_grid
        assert generator.strict_canonical_like(input_grid) == []
        assert generator.self_check(input_grid) == []


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
        grids = {
            tuple(
                tuple(row)
                for row in generator.generate(
                    73, 1, difficulty=band, scene_profile=profile
                )
            )
            for band in ("easy", "medium", "hard")
        }
        assert len(grids) == 3
