from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.666934e5ac80.generator"
)
TASK_ID = "666934e5ac80"


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _blank(h=8, w=9):
    return [[0 for _ in range(w)] for _ in range(h)]


def _paint(grid, color, cells):
    for row, col in cells:
        grid[row][col] = color
    return grid


def _valid_hand_scene():
    grid = _blank()
    _paint(grid, 1, [(1, 1), (1, 2), (2, 1), (2, 2)])
    _paint(grid, 1, [(6, 1)])
    _paint(grid, 2, [(5, 7)])
    return grid


def test_rule_hash_and_task_local_base_target_match_canonical():
    row = _canonical_row()
    canonical = row["program_solution"]
    assert MODULE.RULE_HASH == _normalized_hash(canonical) == "821bfb26a1d2"
    files = sorted((ROOT / "data/base/solutions").rglob(f"*{TASK_ID}.json"))
    assert len(files) == 1
    target = json.loads(files[0].read_text())["racket_target"]["target_code"]
    assert " ".join(target.split()) == " ".join(canonical.split())


def test_version_and_control_surface_are_intentionally_repaired():
    assert MODULE.VERSION == "2.0.0"
    assert set(MODULE.AXES) == {
        "grid_h",
        "grid_w",
        "palette_family",
        "n_colors",
        "n_decoy_components",
    }


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_draws_are_structurally_lawful_and_non_identity(difficulty):
    for seed in range(40):
        grid = MODULE.generate(seed, seed * 19 + 7, difficulty=difficulty)
        assert MODULE.self_check(grid, difficulty=difficulty) == []
        analysis = MODULE._analysis(grid)["facts"]
        assert analysis["multi_colors"]
        assert analysis["singleton_colors"]
        assert 1 <= analysis["n_decoy_components"] <= 3
        assert min(
            analysis["survivor_sizes"][color]
            for color in analysis["singleton_colors"]
        ) <= max(analysis["decoy_sizes"])
        assert MODULE.rule_mirror(grid) != grid
        if difficulty in ("medium", "hard"):
            assert max(analysis["decoy_sizes"]) >= 2


def test_all_boundary_override_combinations_are_exact_and_self_checked():
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (8, 14):
            for grid_w in (9, 16):
                for palette_family in MODULE.PALETTE_FAMILIES:
                    for n_colors in (2, 3):
                        for n_decoy_components in (1, 3):
                            overrides = {
                                "grid_h": grid_h,
                                "grid_w": grid_w,
                                "palette_family": palette_family,
                                "n_colors": n_colors,
                                "n_decoy_components": n_decoy_components,
                            }
                            grid = MODULE.generate(
                                1701,
                                grid_h * 1000 + grid_w * 10 + n_colors,
                                difficulty=difficulty,
                                **overrides,
                            )
                            assert (len(grid), len(grid[0])) == (grid_h, grid_w)
                            observed = MODULE.observe_overrides(grid)
                            for axis in (
                                "palette_family",
                                "n_colors",
                                "n_decoy_components",
                            ):
                                assert observed[axis] == overrides[axis]
                            assert MODULE.self_check(
                                grid,
                                difficulty=difficulty,
                                meta={"overrides": overrides},
                            ) == []


def test_unknown_and_out_of_range_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(0, 0, bogus_axis=1)
    with pytest.raises(ValueError, match="outside"):
        MODULE.generate(0, 0, grid_h=7)
    with pytest.raises(ValueError, match="not in options"):
        MODULE.generate(0, 0, palette_family="varied")


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(1234567)
    before = random.getstate()
    first = MODULE.generate(33, 44, difficulty="hard")
    after = random.getstate()
    second = MODULE.generate(33, 44, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_python_rule_mirror_matches_hand_scene_semantics():
    grid = _valid_hand_scene()
    assert MODULE.self_check(grid) == []
    expected = copy.deepcopy(grid)
    expected[6][1] = 0
    assert MODULE.rule_mirror(grid) == expected


def test_self_check_rejects_targeted_impostors():
    impostors = {}

    impostors["all_background"] = _blank()

    one_color = _blank()
    _paint(one_color, 1, [(1, 1), (1, 2), (2, 1), (6, 1)])
    impostors["one_color"] = one_color

    all_single = _blank()
    _paint(all_single, 1, [(1, 1), (1, 2)])
    _paint(all_single, 2, [(6, 7)])
    impostors["identity_all_single"] = all_single

    tied = _blank()
    _paint(tied, 1, [(1, 1), (1, 2), (5, 1), (5, 2)])
    _paint(tied, 2, [(6, 7)])
    impostors["tied_largest"] = tied

    no_singleton_branch = _blank()
    _paint(no_singleton_branch, 1, [(1, 1), (1, 2), (2, 1), (6, 1)])
    _paint(no_singleton_branch, 2, [(1, 7), (1, 8), (2, 8), (6, 7)])
    impostors["no_singleton_branch"] = no_singleton_branch

    touching_colors = _valid_hand_scene()
    touching_colors[2][3] = 2
    impostors["different_colors_touch"] = touching_colors

    threshold_shortcut = _blank()
    _paint(threshold_shortcut, 1, [(1, 1), (1, 2), (2, 1), (2, 2), (6, 1)])
    _paint(threshold_shortcut, 2, [(5, 6), (5, 7)])
    impostors["global_threshold_shortcut"] = threshold_shortcut

    results = {name: MODULE.self_check(grid) for name, grid in impostors.items()}
    assert len(results) >= 4
    assert all(messages for messages in results.values()), results


def test_color_permutation_does_not_change_component_decisions():
    grid = MODULE.generate(991, 17, difficulty="hard", palette_family="low")
    mapping = {0: 0, 1: 7, 2: 8, 3: 9}
    permuted = [[mapping[value] for value in row] for row in grid]
    mapped_output = [[mapping[value] for value in row] for row in MODULE.rule_mirror(grid)]
    assert MODULE.rule_mirror(permuted) == mapped_output


def test_band_census_has_linked_branch_stability_and_variation():
    signatures = {}
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(seed + 4000, seed * 23 + 5, difficulty=difficulty) for seed in range(50)]
        assert all(MODULE.generate(seed + 4000, seed * 23 + 5, difficulty=difficulty) == grid for seed, grid in enumerate(grids))
        analyses = [MODULE._analysis(grid)["facts"] for grid in grids]
        assert all(facts["multi_colors"] and facts["singleton_colors"] for facts in analyses)
        assert all(facts["decoy_sizes"] for facts in analyses)
        assert all(
            min(facts["survivor_sizes"][c] for c in facts["singleton_colors"])
            <= max(facts["decoy_sizes"])
            for facts in analyses
        )
        assert len({json.dumps(grid) for grid in grids}) == 50
        assert len({json.dumps(MODULE.rule_mirror(grid)) for grid in grids}) == 50
        assert len({(len(grid), len(grid[0])) for grid in grids}) >= 3
        signatures[difficulty] = {
            (
                len(facts["colors"]),
                facts["n_decoy_components"],
                tuple(sorted(facts["survivor_sizes"].values())),
                tuple(facts["decoy_sizes"]),
            )
            for facts in analyses
        }
        assert len(signatures[difficulty]) >= 10
    assert signatures["easy"] != signatures["hard"]
