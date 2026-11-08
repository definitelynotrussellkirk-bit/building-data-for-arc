from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

from scripts.generator_module_loader import load_module_from_path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "80a3c4f25880"
MODULE = load_module_from_path(
    "test_generator_80a3c4f25880_module",
    ROOT / "puzzle_generators/per_puzzle/80a3c4f25880/generator.py",
)
BASE_PATH = ROOT / "data/base/solutions/banks/276b5e4c56a1/medium_b03__80a3c4f25880.json"


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row not found")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _blank(height: int, width: int):
    return [[0 for _ in range(width)] for _ in range(height)]


def _paint(grid, cells, color):
    for row, col in cells:
        grid[row][col] = color
    return grid


def test_rule_hash_and_task_local_authorities_are_synchronized():
    row = _canonical_row()
    base = json.loads(BASE_PATH.read_text())
    authorities = [
        row["program_solution"],
        base["racket_target"]["raw_code"],
        base["racket_target"]["target_code"],
    ]
    assert len(set(authorities)) == 1
    assert {_normalized_hash(source) for source in authorities} == {MODULE.RULE_HASH}
    assert MODULE.RULE_HASH == "17e5167b1aa3"


def test_all_canonical_inputs_are_accepted_and_mirror_exact_outputs():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original
        assert MODULE.canonical_profile_signature(pair["input"]) is not None


def test_three_sequential_demonstrations_expose_all_rotation_keys():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grids = [
                MODULE.generate(seed=seed, sample_index=index, difficulty=band)
                for index in range(3)
            ]
            assert [grid[0][0] for grid in grids] == [1, 2, 3]
            assert all(MODULE.self_check(grid, difficulty=band) == [] for grid in grids)


def test_every_declared_profile_and_key_is_exactly_observable():
    for profile in MODULE.PROFILE_NAMES:
        for key in (1, 2, 3):
            grid = MODULE.generate(
                seed=431,
                sample_index=17,
                difficulty="hard",
                scene_profile=profile,
                key=key,
                blob_color=9,
            )
            assert MODULE.self_check(
                grid,
                difficulty="hard",
                meta={"overrides": {"scene_profile": profile, "key": key, "blob_color": 9}},
            ) == []
            assert MODULE.observe_overrides(grid) == {
                "scene_profile": profile,
                "key": key,
                "blob_color": 9,
            }
            assert MODULE.rule_mirror(grid) != MODULE._analyze(grid)["crop"]


def test_self_check_rejects_targeted_shortcut_impostors():
    # Invalid/absent key whose replacement color is absent from the body.
    invalid_key = MODULE.generate(seed=7, sample_index=0, difficulty="easy")
    invalid_key[0][0] = 8
    assert any("key" in error for error in MODULE.self_check(invalid_key))

    # Canonical morphology moved into the reserved key moat.
    corner_blob = _blank(7, 7)
    corner_blob[0][0] = 1
    _paint(corner_blob, ((0, 1), (1, 1), (2, 1), (2, 2)), 5)
    assert any("moat" in error for error in MODULE.self_check(corner_blob))

    # Count-only shortcut: four cells but a solid rectangle rather than a canonical shape.
    rectangle = _blank(7, 7)
    rectangle[0][0] = 1
    _paint(rectangle, ((3, 3), (3, 4), (4, 3), (4, 4)), 5)
    assert any("morphology" in error for error in MODULE.self_check(rectangle))

    # One matching object plus a disconnected same-color answer leak.
    disconnected = _blank(7, 7)
    disconnected[0][0] = 1
    _paint(disconnected, ((2, 2), (3, 2), (4, 2), (4, 3), (6, 6)), 5)
    errors = MODULE.self_check(disconnected)
    assert any("4-connected" in error for error in errors)

    # Correct shape on an unobserved dimension tuple is a broad-superfamily impostor.
    wrong_dims = _blank(8, 7)
    wrong_dims[0][0] = 1
    _paint(wrong_dims, ((2, 2), (3, 2), (4, 2), (4, 3)), 5)
    assert any("linked profiles" in error for error in MODULE.self_check(wrong_dims))

    # Modal-color echo shortcut: the body may not reuse the control-key color.
    same_color = _blank(7, 7)
    same_color[0][0] = 1
    _paint(same_color, ((2, 2), (3, 2), (4, 2), (4, 3)), 1)
    assert any("differ from the key" in error for error in MODULE.self_check(same_color))


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(991827)
    before = random.getstate()
    first = MODULE.generate(seed=55, sample_index=13, difficulty="medium")
    after = random.getstate()
    second = MODULE.generate(seed=55, sample_index=13, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    third = MODULE.generate(seed=55, sample_index=13, difficulty="medium")
    assert third == second


def test_unknown_or_incompatible_overrides_reject_loudly():
    try:
        MODULE.generate(seed=1, sample_index=0, mystery_axis=1)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was silently accepted")

    try:
        MODULE.generate(seed=1, sample_index=0, key=1, blob_color=1)
    except ValueError as exc:
        assert "blob_color" in str(exc)
    else:
        raise AssertionError("incompatible key/blob_color was silently accepted")
