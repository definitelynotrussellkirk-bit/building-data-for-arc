from __future__ import annotations

import copy
import hashlib
import json
import importlib.util
import os
import random
from pathlib import Path

import pytest

GENERATOR_PATH = Path(os.environ.get(
    "GENERATOR_UNDER_TEST",
    Path(__file__).resolve().parents[1] / "generator.py",
))
_spec = importlib.util.spec_from_file_location("generator_7213d98ef029_under_test", GENERATOR_PATH)
assert _spec is not None and _spec.loader is not None
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)
TASK_ID = "7213d98ef029"


def _canonical_row():
    candidates = [
        Path(__file__).resolve().parents[3] / "shared/data/canonical/puzzles.jsonl",
        Path.cwd() / "shared/data/canonical/puzzles.jsonl",
        Path.cwd() / "data/canonical/puzzles.jsonl",
    ]
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    assert path is not None, f"canonical ledger not found in {candidates}"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"canonical row {TASK_ID} not found")


def canonical_pairs():
    row = _canonical_row()
    return list(row["train"]) + list(row["test"])


def canonical_rule_hash():
    source = _canonical_row()["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _declared_incompatible(requested: dict[str, str]) -> bool:
    for declaration in gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS:
        if all(
            axis in requested
            and (expected is None or requested[axis] == expected)
            for axis, expected in declaration.items()
        ):
            return True
    return False


def test_rule_hash_and_all_canonical_pairs():
    assert gen.RULE_HASH == canonical_rule_hash()
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]


def test_all_exact_axis_combinations_are_realized_and_observed():
    case_index = 0
    rejected = 0
    for band in ("easy", "medium", "hard"):
        for shape in gen.SHAPE_PROFILES:
            for scene in gen.SCENE_PROFILES:
                for palette in gen.PALETTE_KINDS:
                    requested = {
                        "shape_profile": shape,
                        "scene_profile": scene,
                        "palette_kind": palette,
                    }
                    if _declared_incompatible(requested):
                        with pytest.raises(ValueError, match="incompatible overrides"):
                            gen.generate(
                                10_000 + case_index,
                                case_index,
                                difficulty=band,
                                **requested,
                            )
                        rejected += 1
                        case_index += 1
                        continue
                    grid = gen.generate(
                        10_000 + case_index,
                        case_index,
                        difficulty=band,
                        **requested,
                    )
                    assert gen.self_check(grid, difficulty=band) == []
                    assert gen.strict_canonical_like(grid) == []
                    assert gen.observe_overrides(grid) == requested
                    case_index += 1
    assert case_index == (
        3 * len(gen.SHAPE_PROFILES) * len(gen.SCENE_PROFILES) * len(gen.PALETTE_KINDS)
    )
    assert rejected == 3 * len(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS)


def test_default_distribution_reaches_both_canonical_palette_sizes():
    palette_sizes = {
        len({value for row in gen.generate(seed, index, difficulty=band) for value in row})
        for band in ("easy", "medium", "hard")
        for seed in range(9)
        for index in range(20)
    }
    assert {5, 6} <= palette_sizes


def test_every_four_sample_window_is_identifiable_and_covers_schedule():
    for band in ("easy", "medium", "hard"):
        for seed in range(7):
            for start in range(12):
                demos = [
                    _pair(seed, start + offset, band)
                    for offset in range(gen.EXAMPLES_NEEDED)
                ]
                assert gen.lesson_identifiable(demos, None) == []
                observed = [gen.observe_overrides(pair["input"]) for pair in demos]
                assert {row["scene_profile"] for row in observed} == set(gen.SCENE_PROFILES)
                assert len({row["shape_profile"] for row in observed}) >= 2
                assert len({row["palette_kind"] for row in observed}) >= 2


def test_declared_witnesses_have_real_rival_counterexamples():
    grids = [
        gen.generate(31, index, difficulty="medium")
        for index in range(16)
    ]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        for grid in firing:
            official = gen.rule_mirror(grid)
            assert any(gen.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)


def test_self_check_rejects_structural_impostors():
    valid = gen.generate(17, 23, scene_profile="dual_gap")
    assert gen.self_check(valid) == []

    mutations = []
    corner = copy.deepcopy(valid)
    corner[0][0] = 5
    mutations.append(corner)

    missing_top = copy.deepcopy(valid)
    missing_top[0][1] = 0
    mutations.append(missing_top)

    missing_left = copy.deepcopy(valid)
    missing_left[1][0] = 0
    mutations.append(missing_left)

    painted = copy.deepcopy(valid)
    painted[1][1] = 6
    mutations.append(painted)

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    mutations.append(ragged)

    invalid_color = copy.deepcopy(valid)
    invalid_color[0][1] = 12
    mutations.append(invalid_color)

    for grid in mutations:
        assert gen.self_check(grid)


def test_replay_is_deterministic_fresh_global_rng_pure_and_invalid_calls_fail():
    before = random.getstate()
    first = gen.generate(42, 17, difficulty="hard")
    second = gen.generate(42, 17, difficulty="hard")
    after = random.getstate()

    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after

    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 2, difficulty="extreme")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, typo_axis="dual_gap")
    with pytest.raises(ValueError):
        gen.generate(1, 2, scene_profile="not_a_scene")
    with pytest.raises(ValueError):
        gen.generate(1, 2, shape_profile="r9_c9")
    with pytest.raises(ValueError):
        gen.generate(1, 2, palette_kind="rainbow")
