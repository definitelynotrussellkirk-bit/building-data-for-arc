"""Focused regression tests for the reviewed 5751039becb2 sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "5751039becb2"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1] if (HOME.parents[1] / "shared").exists() else None


def _load_generator():
    explicit = os.environ.get("GENERATOR_UNDER_TEST")
    candidates = [Path(explicit)] if explicit else []
    candidates.append(HOME / "generator.py")
    for path in candidates:
        if path.is_file():
            if ROOT is not None:
                sys.path.insert(0, str(ROOT / "shared/runtime"))
            spec = importlib.util.spec_from_file_location(
                f"reviewed_{TASK_ID}", path
            )
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )


gen = _load_generator()


def _canonical_pairs():
    try:
        from reviewer_support import canonical_pairs, find_root

        return canonical_pairs(TASK_ID, root=find_root(__file__))
    except (ImportError, FileNotFoundError):
        from scripts.canonical_profile_gate import canonical_pairs

        return canonical_pairs(TASK_ID)


def _oracle(grid):
    h, w = len(grid), len(grid[0])
    output = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and grid[r + dr][c + dc] == value
                for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
            ):
                output[r][c] = value
    return output


def _pair(seed, sample_index, band):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": _oracle(grid)}


def test_pins_authority_and_declares_only_observable_controls():
    assert gen.RULE_HASH == "8626f391dcea"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n_survivor_groups",
        "profile",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical",
        "shared_color_singleton",
        "orthogonal_repeat",
        "combined",
    )


@pytest.mark.parametrize(
    "pair", _canonical_pairs(), ids=lambda p: f"{len(p['input'])}x{len(p['input'][0])}"
)
def test_canonical_pairs_are_owned_and_match_independent_oracle(pair):
    source = deepcopy(pair["input"])
    assert gen.self_check(source) == []
    assert gen.strict_canonical_like(source) == []
    assert _oracle(source) == pair["output"]
    assert gen.rule_mirror(source) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 6,
            "grid_w": 7,
            "n_survivor_groups": 2,
            "profile": "canonical",
        },
        {
            "grid_h": 10,
            "grid_w": 12,
            "n_survivor_groups": 4,
            "profile": "combined",
        },
        {
            "grid_h": 7,
            "grid_w": 8,
            "n_survivor_groups": 3,
            "profile": "orthogonal_repeat",
        },
    ],
)
def test_exact_override_cartesian_boundaries_are_constructive(band, overrides):
    grid = gen.generate(173, 9, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides
    assert grid == gen.generate(173, 9, difficulty=band, **overrides)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 5),
        ("grid_h", 11),
        ("grid_w", 6),
        ("grid_w", 13),
        ("n_survivor_groups", 1),
        ("n_survivor_groups", 5),
        ("n_survivor_groups", True),
        ("grid_h", 6.5),
        ("profile", "no_pairs"),
    ],
)
def test_unknown_out_of_range_and_wrong_type_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_three_demo_window_refutes_all_declared_competitors(band):
    period = len(gen.SCHEDULE_PROFILES)
    for start in range(period):
        episode = [_pair(8128, start + offset, band) for offset in range(4)]
        demos, query = episode[: gen.EXAMPLES_NEEDED], episode[-1]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                band,
                start,
                name,
            )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_profiles_and_witnesses_are_present_in_every_band(band):
    grids = [gen.generate(2718, index, difficulty=band) for index in range(8)]
    profiles = [gen.observe_overrides(grid)["profile"] for grid in grids]
    assert profiles == list(gen.SCHEDULE_PROFILES) * 2
    for grid in grids:
        assert gen.self_check(grid) == []
        assert _oracle(grid) == gen.rule_mirror(grid)
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        matches = [grid for grid in grids if witness(grid)]
        assert matches, (band, witness_name)
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert all(rival(grid) != _oracle(grid) for grid in matches), (
                band,
                witness_name,
                rival_name,
            )


def test_declared_canonical_shortcuts_fit_public_pairs_and_are_refuted_by_schedule():
    pairs = _canonical_pairs()
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
    generated = [gen.generate(99, index, difficulty="medium") for index in range(4)]
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert any(rival(grid) != _oracle(grid) for grid in generated), name


def test_canonical_profiles_are_interleaved_in_every_band():
    canonical_profiles = {(6, 7, 5), (7, 8, 5)}
    for band in ("easy", "medium", "hard"):
        observed = set()
        for index in range(12):
            grid = gen.generate(909, index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            if profile in canonical_profiles:
                observed.add(profile)
        assert observed == canonical_profiles


def test_rich_slot_dimensions_scale_with_difficulty():
    sample_index = 3
    easy = gen.observe_overrides(gen.generate(12345, sample_index, difficulty="easy"))
    medium = gen.observe_overrides(gen.generate(12345, sample_index, difficulty="medium"))
    hard = gen.observe_overrides(gen.generate(12345, sample_index, difficulty="hard"))
    assert easy["grid_h"] <= medium["grid_h"] <= hard["grid_h"]
    assert easy["grid_w"] <= medium["grid_w"] <= hard["grid_w"]
    assert (easy["grid_h"], easy["grid_w"]) != (hard["grid_h"], hard["grid_w"])


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 7 for _ in range(6)],
        [[1] * 7 for _ in range(6)],
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 2, 2, 0, 0, 0, 0],
            [0, 2, 2, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
    ],
)
def test_self_check_rejects_malformed_and_identity_impostors(grid):
    assert gen.self_check(grid)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261003)
    before = random.getstate()
    first = gen.generate(44, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(44, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_workspace_curriculum_probe_checks_every_cyclic_start_and_dynamic_contract():
    workspace = HOME / "workspace" / "curriculum_probe.py"
    spec = importlib.util.spec_from_file_location("curriculum_probe_5751039becb2", workspace)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.run(per_band=4, seed=24680, generator=gen)
    assert report["task_id"] == TASK_ID
    assert report["period"] == len(gen.SCHEDULE_PROFILES)
    assert report["lessons_total"] == 12
    assert report["oracle_mismatches"] == 0
    assert report["unidentifiable_lessons"] == 0
    assert report["rival_survivals"] == {
        name: 0 for name in gen.LESSON_COMPETITORS
    }
    assert all(
        starts == list(range(len(gen.SCHEDULE_PROFILES)))
        for starts in report["cyclic_starts_by_band"].values()
    )
