"""Focused regression tests for the reviewed a2d8f0cb0fdb generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))
from puzzle_generators import base as generator_base


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "reviewed_a2d8f0cb0fdb", HOME / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_row():
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "a2d8f0cb0fdb":
            return row
    raise AssertionError("canonical row missing")


def canonical_pairs(_task_id):
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + test


def canonical_rule_source(_task_id):
    return _canonical_row()["program_solution"]


def _episode(seed: int, start: int, band: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, start + offset, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    return demos, {"input": query_grid, "output": gen.rule_mirror(query_grid)}


def test_rule_hash_and_all_canonical_pairs():
    expected_hash = hashlib.sha256(
        " ".join(canonical_rule_source(gen.TASK_ID).split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == expected_hash == "b1048663f6a3"

    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_adversarial_fixture_refutes_canonical_shortcuts():
    grid = [
        [0, 3, 0, 7, 0, 0],
        [1, 0, 5, 1, 0, 0],
        [0, 1, 0, 0, 4, 1],
        [0, 0, 1, 0, 0, 0],
    ]
    expected = [
        [0, 0, 0, 0, 0, 0],
        [3, 0, 0, 3, 0, 0],
        [0, 3, 0, 0, 0, 3],
        [0, 0, 3, 0, 0, 0],
    ]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == expected
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert shortcut(grid) != expected, name


def test_every_profile_is_overrideable_observable_and_valid():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                10_000 + index,
                20_000 + index,
                difficulty=band,
                scene_profile=profile,
            )
            assert gen.self_check(grid) == []
            assert gen.teaching_check(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="canonical_anchor")
    with pytest.raises(ValueError, match="scene_profile"):
        gen.generate(1, 0, scene_profile="unknown")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_default_schedule_is_recorded_and_every_window_refutes_rivals():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band in ("easy", "medium", "hard"):
            observed = []
            for index in range(8):
                grid = gen.generate(41_000, index, difficulty=band)
                profile = gen.observe_overrides(grid)["scene_profile"]
                observed.append(profile)
                assert captured[-1].recorded_draws()["scene_profile"] == profile
            expected_cycle = [
                "canonical_anchor",
                "header_choice",
                "body_filter",
                "canonical_anchor",
                "combined",
            ]
            assert observed == (expected_cycle * 2)[:8]
    finally:
        generator_base.set_ctx_observer(None)

    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos, query = _episode(91_000 + start, start, band)
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_schedule_has_canonical_profile_support_in_every_band():
    for band in ("easy", "medium", "hard"):
        anchors = [
            gen.generate(70_000 + index, index, difficulty=band)
            for index in range(20)
            if gen.schedule_profile(70_000 + index, index, band) == "canonical_anchor"
        ]
        assert len(anchors) == 8
        for grid in anchors:
            palette_size = len({value for row in grid for value in row})
            assert (len(grid), len(grid[0]), palette_size) in {(4, 5, 3), (4, 6, 3)}


def test_semantic_witnesses_fire_and_claim_real_rival_disagreements():
    grids = {
        profile: gen.generate(82_000, index, scene_profile=profile)
        for index, profile in enumerate(gen.SCENE_PROFILES)
    }
    assert gen.SEMANTIC_WITNESSES["multiple_header_markers"](grids["header_choice"])
    assert gen.SEMANTIC_WITNESSES["body_distractors"](grids["body_filter"])
    assert all(witness(grids["combined"]) for witness in gen.SEMANTIC_WITNESSES.values())

    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        witness_grid = next(grid for grid in grids.values() if witness(grid))
        authority = gen.rule_mirror(witness_grid)
        assert any(gen.SEMANTIC_RIVALS[name](witness_grid) != authority for name in rival_names)


def test_all_declared_shortcuts_fit_every_canonical_pair():
    pairs = canonical_pairs(gen.TASK_ID)
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_malformed_and_semantically_empty_inputs_are_diagnostic():
    bad_grids = [
        None,
        [],
        [[]],
        [[0, 2], [1]],
        [[False, 2], [1, 0]],
        [[0, 0], [1, 0]],
        [[0, 2], [0, 0]],
        [[1, 1], [1, 1]],
        [[1, 1, 0], [1, 1, 0], [0, 0, 0]],
    ]
    for grid in bad_grids:
        assert gen.self_check(grid)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261003)
    state = random.getstate()
    first = gen.generate(12_345, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(12_345, 7, difficulty="hard")
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert second == gen.generate(12_345, 7, difficulty="hard")


def test_lesson_probe_plans_required_source_bound_census():
    path = HOME / "workspace" / "lesson_probe.py"
    spec = importlib.util.spec_from_file_location("a2d8f0cb0fdb_lesson_probe", path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    plan = probe._plan(100, gen.EXAMPLES_NEEDED)
    assert len(plan) == 300
    assert probe.TASK_ID == gen.TASK_ID
    assert probe.SCHEDULE_LENGTH == len(gen._SCHEDULE) == 5
    for band in ("easy", "medium", "hard"):
        rows = [row for row in plan if row["band"] == band]
        assert len(rows) == 100
        assert {row["sample_index"] % probe.SCHEDULE_LENGTH for row in rows} == set(range(5))
        assert all(row["n_demos"] == gen.EXAMPLES_NEEDED for row in rows)
