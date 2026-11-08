"""Focused regression tests for the reviewed 01bb2cbe1309 generator."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "01bb2cbe1309"
HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"reviewed_{TASK_ID}", HOME / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict]:
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open(
        encoding="utf-8"
    ) as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [*row["train"], *row["test"]]
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def test_rule_pin_unknown_override_and_canonical_python_oracle() -> None:
    gen = _load_generator()
    assert gen.RULE_HASH == "d45fd86e0516"
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    for pair in _canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("profile", ("canonical", "blocked", "axis", "mismatch"))
@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_scene_profile_override_is_exact_and_observable(profile: str, band: str) -> None:
    gen = _load_generator()
    grid = gen.generate(
        991,
        17,
        difficulty=band,
        grid_h=5,
        grid_w=6,
        scene_profile=profile,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 5,
        "grid_w": 6,
        "scene_profile": profile,
    }


def test_four_consecutive_demos_cover_the_curriculum_and_identify_the_query() -> None:
    gen = _load_generator()
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            observed = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(20261002, sample_index, difficulty=band)
                observed.append(gen.observe_overrides(grid)["scene_profile"])
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert set(observed) == set(gen.SCHEDULE_PROFILES)
            query_grid = gen.generate(
                20261002, start + gen.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []


def test_declared_shortcuts_fit_canonical_but_each_generated_witness_refutes_its_rival() -> None:
    gen = _load_generator()
    pairs = _canonical_pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    witness_profiles = {
        "both_diagonal_orientations": "canonical",
        "blocked_corner_is_preserved": "blocked",
        "axis_pair_is_not_a_target": "axis",
        "endpoint_colors_must_match": "mismatch",
    }
    for witness_name, profile in witness_profiles.items():
        grid = gen.generate(431, 0, scene_profile=profile)
        assert gen.SEMANTIC_WITNESSES[witness_name](grid)
        official = gen.rule_mirror(grid)
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != official


def test_distribution_is_deterministic_fresh_diverse_and_has_strict_support() -> None:
    gen = _load_generator()
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(81, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(81, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    for band_index, band in enumerate(("easy", "medium", "hard")):
        profiles = set()
        strict_hits = 0
        signatures = set()
        for index in range(160):
            grid = gen.generate(10000 + band_index * 1000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            profiles.add(gen.observe_overrides(grid)["scene_profile"])
            strict_hits += gen.strict_canonical_like(grid) == []
            signatures.add(tuple(tuple(row) for row in grid))
        assert profiles == set(gen.SCHEDULE_PROFILES)
        assert strict_hits >= 12
        assert len(signatures) >= 150


def test_self_check_rejects_targeted_impostors() -> None:
    gen = _load_generator()
    valid = gen.generate(123, 0, scene_profile="canonical", grid_h=6, grid_w=7)
    assert gen.self_check(valid) == []

    blank = [[0 for _ in row] for row in valid]
    assert gen.self_check(blank)

    singleton = [[0 for _ in row] for row in valid]
    singleton[2][2] = 4
    assert gen.self_check(singleton)

    merged = copy.deepcopy(valid)
    # Add a bridge cell between the two deliberately separated local motifs.
    nonzero = [(r, c) for r, row in enumerate(merged) for c, value in enumerate(row) if value]
    r0 = sum(r for r, _ in nonzero) // len(nonzero)
    c0 = sum(c for _, c in nonzero) // len(nonzero)
    merged[r0][c0] = 9
    assert gen.self_check(merged)
