"""Regression tests for the ecd1f88fc6d3 directed-ray curriculum."""
from __future__ import annotations

import importlib.util
import random
from pathlib import Path
import sys

import pytest

TASK_ID = "ecd1f88fc6d3"
HERE = Path(__file__).resolve()
REPO = next((p for p in HERE.parents if (p / "shared/runtime").is_dir()), None)
if REPO is not None:
    sys.path.insert(0, str(REPO / "shared/runtime"))
    SOURCE = REPO / "generators" / TASK_ID / "generator.py"
else:
    ROOT = next(p for p in HERE.parents if (p / "puzzle_generators").is_dir())
    sys.path.insert(0, str(ROOT))
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location(f"{TASK_ID}_review_subject", SOURCE)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

_CANONICAL_PAIRS = (
    (
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 5, 4, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0],
            [0, 0, 0, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 5, 5, 5, 5, 5],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0],
        ],
    ),
    (
        [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 3, 6, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [6, 6, 6, 6, 6, 6, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
    ),
    (
        [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 5, 0, 4, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 3, 6, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [6, 6, 6, 6, 6, 6, 6, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
    ),
)


def _palette_size(grid: list[list[int]]) -> int:
    return len({value for row in grid for value in row})


def test_rule_hash_and_python_mirror_match_all_canonical_pairs() -> None:
    assert getattr(gen, "RULE_HASH", None) == "16da73149c81"
    assert callable(getattr(gen, "rule_mirror", None))
    for input_grid, output_grid in _CANONICAL_PAIRS:
        assert gen.rule_mirror(input_grid) == output_grid


def test_self_check_accepts_all_canonical_inputs_including_distractors() -> None:
    assert callable(getattr(gen, "self_check", None))
    assert [gen.self_check(pair[0]) for pair in _CANONICAL_PAIRS] == [[], [], []]


def test_unknown_difficulty_and_override_are_rejected() -> None:
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="legendary")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, invented_axis=True)


def test_scheduled_profiles_cover_exact_canonical_shape_palette_profiles() -> None:
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_small",
        "canonical_medium",
        "canonical_distractor",
        "direction_sweep",
    )
    expected = ((7, 7, 5), (8, 8, 5), (9, 9, 7))
    for band in (None, "easy", "medium", "hard"):
        actual = []
        for index in range(3):
            grid = gen.generate(223, index, difficulty=band)
            actual.append((len(grid), len(grid[0]), _palette_size(grid)))
            assert gen.observe_overrides(grid)["scene_profile"] == gen.SCHEDULE_PROFILES[index]
        assert tuple(actual) == expected


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(7, 7), (7, 9), (9, 7), (9, 9)])
def test_every_profile_honours_boundary_size_overrides(band, height, width) -> None:
    for profile in getattr(gen, "SCHEDULE_PROFILES", ()):
        kwargs = {
            "difficulty": band,
            "grid_h": height,
            "grid_w": width,
            "scene_profile": profile,
        }
        first = gen.generate(901, 17, **kwargs)
        second = gen.generate(901, 17, **kwargs)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert gen.self_check(first, difficulty=band, meta={"overrides": kwargs}) == []
        assert gen.observe_overrides(first) == {
            "grid_h": height,
            "grid_w": width,
            "scene_profile": profile,
        }


def test_distractor_profile_proves_markers_vanish_and_rays_cross_markers() -> None:
    grid = gen.generate(19, 2, difficulty="hard", scene_profile="canonical_distractor")
    facts = gen._analyze(grid)
    assert not facts["errors"]
    assert len(facts["emitters"]) == 2
    assert len(facts["untriggered_markers"]) == 2
    output = gen.rule_mirror(grid)
    assert any(
        grid[r][c] != 0 and output[r][c] not in (0, grid[r][c])
        for r, c in facts["untriggered_markers"]
    ), "a non-triggering marker must be overwritten by an active ray"
    assert any(output[r][c] == 0 for r, c in facts["untriggered_markers"]), (
        "an isolated marker must disappear"
    )


def test_witnesses_and_rivals_have_measured_counterexamples() -> None:
    seen_directions: set[str] = set()
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    rival_differences = {name: 0 for name in gen.SEMANTIC_RIVALS}
    for index in range(12):
        grid = gen.generate(37, index, difficulty="hard")
        expected = gen.rule_mirror(grid)
        seen_directions.update(item["direction"] for item in gen._analyze(grid)["emitters"])
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            witness_hits[name] += bool(predicate(grid))
        for name, rival in gen.SEMANTIC_RIVALS.items():
            rival_differences[name] += rival(grid) != expected
    assert seen_directions == {"up", "down", "left", "right"}
    assert all(witness_hits.values()), witness_hits
    assert all(rival_differences.values()), rival_differences


def test_generation_preserves_global_rng_state() -> None:
    random.seed(20261002)
    before = random.getstate()
    gen.generate(123, 7, difficulty="hard")
    assert random.getstate() == before


def test_every_three_demo_window_refutes_all_declared_rivals() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(771, index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            profiles = [gen.observe_overrides(pair["input"])["scene_profile"] for pair in demos]
            assert "canonical_distractor" in profiles, (band, start, profiles)
            for name, competitor in gen.SEMANTIC_RIVALS.items():
                assert any(
                    competitor(pair["input"]) != pair["output"] for pair in demos
                ), (band, start, name, profiles)
