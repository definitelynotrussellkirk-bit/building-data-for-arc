"""Source-bound regression tests for the 9f74cf8633e5 review repair."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "9f74cf8633e5"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
EXPECTED_RIVALS = {
    "first_center_only",
    "one_center_per_color",
    "fill_colors_occurring_exactly_four_times",
    "ignore_diagonal_color_equality",
    "three_of_four_diagonals",
    "overwrite_nonzero_center",
    "require_blank_orthogonals",
    "reuse_only_with_mismatched_distractor",
    "reuse_only_with_partial_distractor",
    "reuse_only_with_blocked_distractor",
}


def _diag_values(grid, row, col):
    return tuple(grid[row + dr][col + dc] for dr, dc in DIAGONALS)


def independent_rule(grid):
    out = [row[:] for row in grid]
    for row in range(1, len(grid) - 1):
        for col in range(1, len(grid[0]) - 1):
            values = _diag_values(grid, row, col)
            if grid[row][col] == 0 and values[0] != 0 and len(set(values)) == 1:
                out[row][col] = values[0]
    return out


def _pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_contract_pins_authority_and_keeps_a_small_exact_axis_surface():
    assert GEN.RULE_HASH == "3de95ecac741"
    assert GEN.EXAMPLES_NEEDED == 5
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.AXES) == {"grid_h", "grid_w", "cross_count", "color_mode", "texture"}
    assert GEN.TEXTURES == (
        "mismatched_diagonals",
        "partial_diagonals",
        "blocked_center",
    )
    assert GEN.COLOR_MODES == ("distinct", "shared")
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_canonical_inputs_are_accepted_and_python_rule_matches_all_labels():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_declared_canonical_shortcut_really_fits_the_canonical_demos():
    pairs = [pair for pair in canonical_pairs(TASK_ID, root=find_root(__file__)) if pair["split"] == "train"]
    assert set(GEN.CANONICAL_SHORTCUTS) == EXPECTED_RIVALS
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(7, 7), (9, 12), (17, 17)])
@pytest.mark.parametrize("cross_count", [2, 3])
@pytest.mark.parametrize("color_mode", ["distinct", "shared"])
@pytest.mark.parametrize("texture", [
    "mismatched_diagonals",
    "partial_diagonals",
    "blocked_center",
])
def test_exact_overrides_are_constructive_observable_and_lawful(
    band, height, width, cross_count, color_mode, texture
):
    grid = GEN.generate(
        407,
        11,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        cross_count=cross_count,
        color_mode=color_mode,
        texture=texture,
    )
    assert GEN.self_check(grid) == []
    assert GEN._generated_errors(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "cross_count": cross_count,
        "color_mode": color_mode,
        "texture": texture,
    }
    assert GEN.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 6},
        {"grid_h": 18},
        {"grid_w": 6},
        {"grid_w": 18},
        {"cross_count": 1},
        {"cross_count": 4},
        {"grid_h": True},
        {"grid_w": 9.5},
        {"cross_count": "2"},
        {"color_mode": "mixed"},
        {"texture": "none"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_six_pair_block_survives_every_five_demo_query_rotation(band):
    for seed in range(4):
        for start in range(6):
            pairs = [_pair(GEN.generate(seed, start + offset, difficulty=band)) for offset in range(6)]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(item["input"]) != item["output"] for item in demos), (
                        band,
                        seed,
                        start,
                        query_index,
                        name,
                    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_hits_every_teaching_factor_and_moves_centers(band):
    grids = [GEN.generate(911, index, difficulty=band) for index in range(90)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert {item["texture"] for item in observed} == set(GEN.TEXTURES)
    assert {item["color_mode"] for item in observed} == set(GEN.COLOR_MODES)
    assert {item["cross_count"] for item in observed} == {2, 3} if band != "easy" else {2}
    assert any(GEN.SEMANTIC_WITNESSES["orthogonal_context_pair"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["repeated_color_multiple_centers"](grid) for grid in grids)
    positions = {
        (row, col)
        for grid in grids
        for row, col, _color in GEN._classify_centers(grid)["active"]
    }
    residues = {(row % 3, col % 3) for row, col in positions}
    assert len(positions) >= 30
    assert len(residues) >= 7



def test_shared_positive_color_refutes_the_exactly_four_occurrences_shortcut():
    grid = GEN.generate(
        9,
        4,
        grid_h=12,
        grid_w=13,
        cross_count=3,
        color_mode="shared",
        texture="mismatched_diagonals",
    )
    assert GEN.SEMANTIC_WITNESSES["repeated_color_multiple_centers"](grid)
    truth = independent_rule(grid)
    rival = GEN.CANONICAL_SHORTCUTS["fill_colors_occurring_exactly_four_times"](grid)
    assert rival != truth

def test_mismatched_counterexample_disagrees_with_the_strongest_shortcut():
    grid = [[0 for _ in range(7)] for _ in range(7)]
    grid[2][2] = 1
    grid[2][4] = 2
    grid[4][2] = 1
    grid[4][4] = 2
    truth = independent_rule(grid)
    rival = GEN.CANONICAL_SHORTCUTS["ignore_diagonal_color_equality"](grid)
    assert truth[3][3] == 0
    assert rival[3][3] != 0
    assert truth != rival


def test_generation_helpers_and_rivals_are_deterministic_fresh_and_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(18):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            assert GEN.self_check(first) == []
            assert GEN._generated_errors(first) == []
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
                assert first == original
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == original


def test_reference_probe_is_portable_and_reads_live_rival_registries(tmp_path):
    import json
    import subprocess
    import sys

    probe = HOME / "workspace" / "reference_probe.py"
    completed = subprocess.run(
        [sys.executable, str(probe), "--quick"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["ok"] is True
    assert report["task_id"] == TASK_ID
    assert report["source_sha256"]
    assert report["canonical"]["failed"] == 0
    assert report["generated"]["failed"] == 0
    assert report["lessons"]["failed"] == 0
    assert report["lessons"]["rivals"] == sorted(GEN.LESSON_COMPETITORS)
