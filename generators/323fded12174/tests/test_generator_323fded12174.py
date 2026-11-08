from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "323fded12174"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__))
CANONICAL_PROFILES = {
    (7, 9, 5),
    (5, 8, 5),
    (7, 8, 4),
    (5, 8, 4),
    (6, 10, 3),
}


def _occupancy(row: list[int]) -> int:
    return sum(value != 0 for value in row)


def _intended(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in sorted(grid, key=_occupancy, reverse=True)]




def _dominant_count(row: list[int]) -> int:
    counts: dict[int, int] = {}
    for value in row:
        if value != 0:
            counts[value] = counts.get(value, 0) + 1
    return max(counts.values(), default=0)


def _color_count(row: list[int]) -> int:
    return len({value for value in row if value != 0})


def _mixed_then_dominant(grid: list[list[int]]) -> list[list[int]]:
    return [
        list(row)
        for row in sorted(
            grid,
            key=lambda row: (_color_count(row) > 1, _dominant_count(row)),
            reverse=True,
        )
    ]


def _color_count_then_dominant(grid: list[list[int]]) -> list[list[int]]:
    return [
        list(row)
        for row in sorted(
            grid,
            key=lambda row: (_color_count(row), _dominant_count(row)),
            reverse=True,
        )
    ]

def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    colors = {value for row in grid for value in row if value != 0}
    return len(grid), len(grid[0]), len(colors)


def _disagreement_grid() -> list[list[int]]:
    # Occupancy order is A(7), B(6), C(5), D(4), E(3).  The mixed A row
    # has dominant-color count 2, so a canonical-fitting dominant-count
    # shortcut instead orders B, C, D, E, A.
    a = [1, 2, 3, 4, 1, 2, 3, 0]
    b = [1, 1, 1, 2, 3, 4, 0, 0]
    c = [2, 2, 2, 2, 2, 0, 0, 0]
    d = [3, 3, 3, 3, 0, 0, 0, 0]
    e = [4, 4, 4, 0, 0, 0, 0, 0]
    return [c, a, e, b, d]


def test_authority_pin_and_truthful_axes():
    assert GEN.RULE_HASH == "d6c95e66f9b7"
    assert set(GEN.AXES) == {"profile", "cell_layout"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_all_canonical_inputs_are_accepted_and_strict():
    assert len(CANONICAL) == 5
    for pair in CANONICAL:
        grid = copy.deepcopy(pair["input"])
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert _intended(grid) == pair["output"]


def test_default_distribution_is_lawful_profile_anchored_and_adversarial():
    for band in ("easy", "medium", "hard"):
        seen_profiles: set[tuple[int, int, int]] = set()
        seen_inputs: set[tuple[tuple[int, ...], ...]] = set()
        for index in range(120):
            grid = GEN.generate(1009 + index * 17, index * 11 + 3, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert GEN.SEMANTIC_WITNESSES["top_pair_refutes_color_priority"](grid)
            assert all(
                rival(grid) != _intended(grid)
                for rival in GEN.SEMANTIC_RIVALS.values()
            )
            counts = [_occupancy(row) for row in grid]
            assert len(set(counts)) == len(counts)
            assert counts != sorted(counts, reverse=True)
            seen_profiles.add(_profile(grid))
            seen_inputs.add(tuple(tuple(row) for row in grid))
        assert seen_profiles == CANONICAL_PROFILES
        assert len(seen_inputs) >= 100


def test_exact_overrides_are_observable_and_unknown_or_invalid_values_reject():
    cases = (
        {"profile": "5x8x4", "cell_layout": "runs"},
        {"profile": "7x9x5", "cell_layout": "scattered"},
        {"profile": "6x10x3"},
        {"cell_layout": "runs"},
        {"cell_layout": "scattered"},
    )
    for overrides in cases:
        grid = GEN.generate(17, 4, difficulty="hard", **overrides)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        for axis, requested in overrides.items():
            assert observed[axis] == requested

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(17, 4, typo_axis=3)
    for bad in (
        {"profile": "5x8x3"},
        {"profile": True},
        {"cell_layout": "diagonal"},
        {"cell_layout": 1},
    ):
        with pytest.raises(ValueError):
            GEN.generate(17, 4, **bad)


def test_self_check_rejects_targeted_rule_hiding_impostors():
    valid = _disagreement_grid()
    assert GEN.self_check(valid) == []

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    already_sorted = _intended(valid)
    tied_counts = copy.deepcopy(valid)
    tied_counts[-1] = [4, 4, 4, 4, 4, 0, 0, 0]
    zero_row = copy.deepcopy(valid)
    zero_row[-1] = [0] * 8
    too_few_colors = [[1 if value else 0 for value in row] for row in valid]
    bad_cell = copy.deepcopy(valid)
    bad_cell[0][0] = 10
    too_short = valid[:4]

    for impostor in (
        ragged,
        already_sorted,
        tied_counts,
        zero_row,
        too_few_colors,
        bad_cell,
        too_short,
    ):
        assert GEN.self_check(impostor), impostor


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(23, 11, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(23, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert GEN.generate(23, 11, difficulty="medium") == second


def test_dominant_count_shortcut_fits_canonical_but_exact_witness_refutes_it():
    rival = GEN.CANONICAL_SHORTCUTS["dominant_color_count"]
    for pair in CANONICAL:
        assert rival(pair["input"]) == pair["output"]

    grid = _disagreement_grid()
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.SEMANTIC_WITNESSES["top_pair_refutes_color_priority"](grid)
    assert _intended(grid) == [grid[1], grid[3], grid[0], grid[4], grid[2]]
    assert rival(grid) == [grid[0], grid[4], grid[2], grid[3], grid[1]]
    assert rival(grid) != _intended(grid)


def test_lesson_identifiability_and_negative_recombination():
    grids = [GEN.generate(31, index, difficulty="medium") for index in range(3)]
    demos = [{"input": grid, "output": _intended(grid)} for grid in grids[:2]]
    assert GEN.lesson_identifiable(demos, {"input": grids[2]}) == []

    assert GEN.lesson_identifiable(demos[:1], {"input": grids[2]})

    bad_demos = copy.deepcopy(demos)
    bad_demos[0]["output"] = GEN.SEMANTIC_RIVALS["dominant_color_count"](
        bad_demos[0]["input"]
    )
    reasons = GEN.lesson_identifiable(bad_demos, {"input": grids[2]})
    assert any("authoritative occupancy sort" in reason for reason in reasons)

    malformed_query = copy.deepcopy(grids[2])
    malformed_query[-1] = [0] * len(malformed_query[-1])
    reasons = GEN.lesson_identifiable(demos, {"input": malformed_query})
    assert any("query input" in reason for reason in reasons)



def test_mixed_row_priority_shortcuts_fit_canonical_but_not_generated_lessons():
    rivals = {
        "mixed_first_then_dominant": _mixed_then_dominant,
        "color_count_then_dominant": _color_count_then_dominant,
    }
    for rival in rivals.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL)

    assert set(rivals) <= set(GEN.CANONICAL_SHORTCUTS)
    for band in ("easy", "medium", "hard"):
        for index in range(40):
            grid = GEN.generate(7001 + index * 31, index + 101, difficulty=band)
            expected = _intended(grid)
            for name, rival in rivals.items():
                assert rival(grid) != expected, (band, index, name, grid)
                assert GEN.CANONICAL_SHORTCUTS[name](grid) == rival(grid)

def test_workspace_rival_probe_tracks_declarations_and_all_cyclic_lessons():
    import importlib.util
    from pathlib import Path

    probe_path = Path(__file__).resolve().parents[1] / "workspace" / "rival_probe.py"
    spec = importlib.util.spec_from_file_location("rival_probe_323fded12174", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(samples_per_band=4, seed_base=12345)
    import hashlib

    expected_sha = hashlib.sha256(Path(GEN.__file__).read_bytes()).hexdigest()
    assert report["generator_sha256"] == expected_sha
    assert set(report["canonical_shortcuts"]) == set(GEN.CANONICAL_SHORTCUTS)
    assert all(row["fits_all_canonical"] for row in report["canonical_shortcuts"].values())
    assert report["generated"]["invalid_inputs"] == []
    assert report["generated"]["rival_agreements"] == []
    assert report["lessons"]["unidentifiable_windows"] == []
    assert report["lessons"]["windows_checked"] == 12
