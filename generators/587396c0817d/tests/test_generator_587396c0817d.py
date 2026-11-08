from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "587396c0817d"
ROOT = find_root(__file__)
MOD, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _canonical_rule_source() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(TASK_ID)


def test_canonical_inputs_are_owned_and_python_oracle_matches_every_label():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert MOD.self_check(pair["input"]) == []
        assert MOD.strict_canonical_like(pair["input"]) == []
        assert MOD._apply_rule(pair["input"]) == pair["output"]


def test_rank_cap_five_is_a_real_canonical_fitting_rival():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert all(
        MOD.SEMANTIC_RIVALS["rank_cap_5"](pair["input"]) == pair["output"]
        for pair in pairs
    )

    witness = [
        [0, 1, 2, 3, 4, 5, 6, 7],
        [7, 7, 7, 7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7, 7, 7, 7],
    ]
    intended = MOD._apply_rule(witness)
    rival = MOD.SEMANTIC_RIVALS["rank_cap_5"](witness)
    assert MOD.self_check(witness) == []
    assert MOD.SEMANTIC_WITNESSES["rank_six_anchor"](witness)
    assert intended[0] == [8, 8, 8, 8, 8, 8, 8, 7]
    assert rival[0] == [7, 8, 8, 8, 8, 8, 8, 8]
    assert intended != rival


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_two_profile_schedule_is_rotation_safe_and_teaches_the_rival(band):
    assert MOD.EXAMPLES_NEEDED == 3
    assert MOD.LESSON_SCHEDULE_PERIOD == 2
    assert set(MOD.SCHEDULE_PROFILES) == {"rank_six_witness", "canonical_core"}

    for start in range(MOD.LESSON_SCHEDULE_PERIOD):
        pairs = []
        profiles = []
        for offset in range(MOD.EXAMPLES_NEEDED + 1):
            sample_index = start + offset
            grid = MOD.generate(137, sample_index, difficulty=band)
            assert MOD.self_check(grid, difficulty=band) == []
            profile = MOD.schedule_profile(137, sample_index, band)
            profiles.append(profile)
            if profile == "rank_six_witness":
                assert MOD.SEMANTIC_WITNESSES["rank_six_anchor"](grid)
            else:
                assert _profile(grid) in {(10, 10, 5), (10, 10, 10)}
            pairs.append({"input": grid, "output": MOD._apply_rule(grid)})

        assert profiles.count("rank_six_witness") == 2
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert MOD.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_exact_support_in_every_band(band):
    canonical_profiles = {
        _profile(pair["input"])
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    }
    hits = 0
    for index in range(20):
        seed = _pinned_seed(band, index)
        sample_index = seed % 7919 + index
        grid = MOD.generate(seed, sample_index, difficulty=band)
        hits += _profile(grid) in canonical_profiles
    assert hits >= 1


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty", "overrides"),
    [
        (True, 0, None, {}),
        (1.5, 0, None, {}),
        ("1", 0, None, {}),
        (1, True, None, {}),
        (1, 1.5, None, {}),
        (1, "1", None, {}),
        (1, -1, None, {}),
        (1, 0, True, {}),
        (1, 0, 1, {}),
        (1, 0, 1.5, {}),
        (1, 0, "__invalid_difficulty__", {}),
        *[
            (1, 0, "medium", {axis: value})
            for axis in ("grid_h", "grid_w", "n_active_rows", "n_decoy_rows")
            for value in (True, 12.5, "12")
        ],
        *[
            (1, 0, "medium", {axis: value})
            for axis in ("bar_length_kind", "texture", "idx_kind", "palette_kind")
            for value in (True, 1, "__invalid__")
        ],
        (1, 0, "medium", {"grid_h": 5}),
        (1, 0, "medium", {"grid_w": 21}),
        (1, 0, "medium", {"n_active_rows": 0}),
        (1, 0, "medium", {"n_decoy_rows": 6}),
        (1, 0, "medium", {"typo_axis": 1}),
    ],
)
def test_generate_rejects_malformed_scalar_arguments(
    seed, sample_index, difficulty, overrides
):
    with pytest.raises((TypeError, ValueError)):
        MOD.generate(seed, sample_index, difficulty=difficulty, **overrides)


def test_exact_axis_boundaries_remain_observable_in_every_band():
    for band in (None, "easy", "medium", "hard"):
        for axis, values in {
            "grid_h": (6, 18),
            "grid_w": (8, 20),
            "n_active_rows": (1, 6),
            "n_decoy_rows": (0, 5),
        }.items():
            for value in values:
                overrides = {
                    "grid_h": 18,
                    "grid_w": 20,
                    "n_active_rows": 6,
                    "n_decoy_rows": 5,
                    axis: value,
                }
                if overrides["n_active_rows"] + overrides["n_decoy_rows"] > overrides["grid_h"]:
                    # Keep the other exact count legal while testing a small height.
                    overrides["n_decoy_rows"] = 0
                grid = MOD.generate(211, 7, difficulty=band, **overrides)
                assert MOD.self_check(grid, difficulty=band) == []
                observed = MOD.observe_overrides(grid)
                if axis in observed:
                    assert observed[axis] == value
                else:
                    assert (len(grid) if axis == "grid_h" else len(grid[0])) == value


def test_alias_conflict_is_rejected_and_valid_enums_are_deterministic():
    with pytest.raises(ValueError, match="conflicting aliases"):
        MOD.generate(
            1,
            0,
            texture="small",
            bar_length_kind="large",
        )
    first = MOD.generate(
        31337,
        29,
        difficulty="hard",
        texture="large",
        idx_kind="right_biased",
        palette_kind="broad",
    )
    second = MOD.generate(
        31337,
        29,
        difficulty="hard",
        texture="large",
        idx_kind="right_biased",
        palette_kind="broad",
    )
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_bar_color_parametric_prototype_preserves_exact_default_authority():
    path = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    spec = importlib.util.spec_from_file_location("bar_color_prototype", path)
    assert spec is not None and spec.loader is not None
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)

    canonical = _canonical_rule_source()
    default = prototype.instantiate_rule(8, root=ROOT)
    alternative = prototype.instantiate_rule(3, root=ROOT)
    assert default == canonical
    assert alternative != default
    assert prototype.choose_bar_color(0) == 8
    assert prototype.choose_bar_color(1) == 3

    witness = MOD.generate(29, 0, difficulty="medium")
    assert MOD._apply_rule(witness, bar_color=8) != MOD._apply_rule(witness, bar_color=3)
    public = prototype.public_challenge(
        {
            "pairs": [
                {"input": witness, "output": MOD._apply_rule(witness, bar_color=8)}
                for _ in range(4)
            ]
        }
    )
    assert len(public["train"]) == 3
    assert list(public["test"][0]) == ["input"]
