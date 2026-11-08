"""Focused regressions for the global singleton-color erasure curriculum."""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import importlib.util
import itertools
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "8ab614412470"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__))
BANDS = (None, "easy", "medium", "hard")
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "n_repeated_colors",
    "n_singleton_colors",
    "repeat_pattern",
}


def _rule_output(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value != 0)
    return [
        [value if value != 0 and counts[value] > 1 else 0 for value in row]
        for row in grid
    ]


def _observed(grid: list[list[int]]) -> dict[str, object]:
    counts = Counter(value for row in grid for value in row if value != 0)
    repeated = sorted(count for count in counts.values() if count > 1)
    singletons = sum(count == 1 for count in counts.values())
    if repeated and all(count == 2 for count in repeated):
        pattern = "pairs"
    elif repeated and set(repeated) <= {2, 3} and 3 in repeated:
        pattern = "mixed"
    elif repeated and set(repeated) <= {2, 4} and 4 in repeated:
        pattern = "heavy"
    else:
        pattern = "unknown"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_repeated_colors": len(repeated),
        "n_singleton_colors": singletons,
        "repeat_pattern": pattern,
    }


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _positions_by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                positions[value].append((row, col))
    return positions


def test_metadata_and_authority_pin_are_explicit() -> None:
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.RULE_HASH == "f20d2d2ae760"
    assert GEN.VERSION == "2.0.0"
    assert set(GEN.AXES) == EXPECTED_AXES
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_5x7",
        "canonical_5x8",
        "canonical_6x6",
        "broad",
    )


@pytest.mark.parametrize(
    "pair",
    CANONICAL,
    ids=[f"{pair['split']}-{pair['pair_index']}" for pair in CANONICAL],
)
def test_every_canonical_pair_is_accepted_and_matches_the_independent_oracle(pair: dict) -> None:
    original = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _rule_output(pair["input"]) == pair["output"]
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", BANDS)
def test_exact_overrides_are_constructive_observable_and_deterministic_in_every_band(band) -> None:
    requested = {
        "grid_h": 5,
        "grid_w": 5,
        "n_repeated_colors": 5,
        "n_singleton_colors": 4,
        "repeat_pattern": "heavy",
    }
    grid = GEN.generate(3701, 11, difficulty=band, **requested)
    assert grid == GEN.generate(3701, 11, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert _observed(grid) == requested
    assert GEN.observe_overrides(grid) == requested
    assert GEN.rule_mirror(grid) == _rule_output(grid)


@pytest.mark.parametrize("band", BANDS)
def test_every_advertised_boundary_combination_is_constructive(band) -> None:
    domains = {
        "grid_h": (5, 9),
        "grid_w": (5, 9),
        "n_repeated_colors": (2, 5),
        "n_singleton_colors": (2, 4),
        "repeat_pattern": ("pairs", "mixed", "heavy"),
    }
    for index, values in enumerate(itertools.product(*domains.values())):
        requested = dict(zip(domains, values))
        grid = GEN.generate(5000 + index, index * 13 + 1, difficulty=band, **requested)
        assert GEN.self_check(grid) == []
        assert _observed(grid) == requested


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 4},
        {"grid_h": 10},
        {"grid_w": True},
        {"grid_w": 5.0},
        {"n_repeated_colors": 1},
        {"n_repeated_colors": 6},
        {"n_singleton_colors": 1},
        {"n_singleton_colors": 5},
        {"repeat_pattern": "triples"},
        {"repeat_pattern": 2},
    ],
)
def test_invalid_or_unknown_overrides_fail_closed(kwargs) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ("expert", 0.5, 1, True))
def test_invalid_difficulty_fails_closed(difficulty) -> None:
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_anchors_canonical_profiles_and_broad_support_in_every_band(band) -> None:
    profiles = set()
    observed = []
    for index in range(40):
        grid = GEN.generate(9100 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert grid == GEN.generate(9100 + index, index, difficulty=band)
        profiles.add(_profile(grid))
        observed.append(_observed(grid))

    assert {(5, 7, 6), (5, 8, 6), (6, 6, 7)} <= profiles
    assert {item["repeat_pattern"] for item in observed} == {"pairs", "mixed", "heavy"}
    assert len({(item["grid_h"], item["grid_w"]) for item in observed}) >= 6
    assert {item["n_repeated_colors"] for item in observed} >= {2, 3, 5}
    assert {item["n_singleton_colors"] for item in observed} == {2, 3, 4}


@pytest.mark.parametrize("band", BANDS)
def test_generated_inputs_contain_global_not_merely_local_evidence(band) -> None:
    for index in range(48):
        grid = GEN.generate(12000 + index, index * 7 + 3, difficulty=band)
        positions = _positions_by_color(grid)
        assert any(
            len(points) == 2
            and abs(points[0][0] - points[1][0]) + abs(points[0][1] - points[1][1]) > 1
            for points in positions.values()
        )
        assert sum(len(points) == 1 for points in positions.values()) >= 2
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert witness(grid), name
            for rival_name in GEN.WITNESS_RIVALS[name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("band", BANDS)
def test_declared_rivals_do_not_create_ambiguous_generated_lessons(band) -> None:
    for start in range(8):
        pairs = []
        for offset in range(4):
            grid = GEN.generate(16000 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": _rule_output(grid)})
        for query_index in range(4):
            query = pairs[query_index]
            demos = pairs[:query_index] + pairs[query_index + 1 :]
            assert GEN.lesson_identifiable(demos, query) == []


def test_validator_rejects_malformed_and_semantically_broken_inputs() -> None:
    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 5 for _ in range(5)]):
        assert GEN.self_check(malformed)

    grid = GEN.generate(
        44,
        5,
        grid_h=5,
        grid_w=5,
        n_repeated_colors=2,
        n_singleton_colors=2,
        repeat_pattern="pairs",
    )
    counts = Counter(value for row in grid for value in row if value)
    singleton = next(color for color, count in counts.items() if count == 1)
    broken = deepcopy(grid)
    for row in range(len(broken)):
        for col in range(len(broken[0])):
            if broken[row][col] == singleton:
                broken[row][col] = 0
    assert GEN.self_check(broken)


def test_difficulty_bands_change_pair_separation_without_changing_semantic_profile() -> None:
    grids = {
        band: GEN.generate(24680, 1, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in grids.values()}) == 3
    assert len({tuple(_observed(grid).items()) for grid in grids.values()}) == 1

    distances = {}
    for band, grid in grids.items():
        positions = _positions_by_color(grid)
        pair = next(points for points in positions.values() if len(points) == 2)
        distances[band] = abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1])
        assert GEN.self_check(grid) == []

    h, w = len(grids["hard"]), len(grids["hard"][0])
    assert distances["easy"] == 2
    assert 2 < distances["medium"] < h + w - 2
    assert distances["hard"] == h + w - 2


def test_workspace_distribution_probe_checks_schedule_witnesses_and_rotations() -> None:
    probe_path = HOME / "workspace" / "distribution_probe.py"
    probe_spec = importlib.util.spec_from_file_location("distribution_probe_under_test", probe_path)
    assert probe_spec and probe_spec.loader
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)

    report = probe.build_report(GEN, per_band=8, seed_base=88000)
    assert report["status"] == "pass"
    assert report["generator_id"] == TASK_ID
    assert report["generator_version"] == GEN.VERSION
    assert report["samples_total"] == 32
    assert report["failures"] == []
    for band_report in report["bands"].values():
        assert band_report["samples"] == 8
        assert set(band_report["schedule_profiles"]) == set(GEN.SCHEDULE_PROFILES)
        assert band_report["determinism_failures"] == 0
        assert band_report["validator_failures"] == 0
        assert all(count == 8 for count in band_report["witness_firings"].values())
        assert all(count == 8 for count in band_report["witness_rival_disagreements"].values())
    assert report["rotation_check"]["lessons"] == 16
    assert report["rotation_check"]["rotations"] == 64
    assert report["rotation_check"]["ambiguous_rotations"] == 0
