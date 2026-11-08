"""Focused regressions for the ee5295e1813b review repair."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "ee5295e1813b"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
MODULE_PATH = HOME / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"task_{TASK_ID}_reviewed", MODULE_PATH)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def _labeled_pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _pair(grid):
    return {"input": grid, "output": GEN._apply_rule(grid)}


def test_pins_rule_and_exposes_only_observable_exact_axes():
    assert GEN.RULE_HASH == "ff3c83fdb4d7"
    assert GEN.EXAMPLES_NEEDED == 5
    assert set(GEN.AXES) == {"grid_h", "grid_w", "cross_count", "color_mode", "texture"}
    assert set(GEN.TEXTURES) == {
        "partial_diagonals",
        "mismatched_diagonals",
        "blocked_center",
    }


@pytest.mark.parametrize("pair", _labeled_pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_every_canonical_input_and_matches_every_label(pair):
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN._apply_rule(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("texture", ["partial_diagonals", "mismatched_diagonals", "blocked_center"])
def test_exact_overrides_round_trip_from_returned_pixels(difficulty, texture):
    requested = {
        "grid_h": 12,
        "grid_w": 13,
        "cross_count": 3,
        "color_mode": "shared",
        "texture": texture,
    }
    grid = GEN.generate(71, 19, difficulty=difficulty, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert grid == GEN.generate(71, 19, difficulty=difficulty, **requested)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 6},
        {"grid_w": 18},
        {"cross_count": 1},
        {"cross_count": 4},
        {"grid_h": True},
        {"grid_w": 9.5},
        {"cross_count": "3"},
        {"color_mode": "unique"},
        {"texture": "no_motifs"},
    ],
)
def test_rejects_unknown_mistyped_or_out_of_domain_overrides(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_every_six_pair_episode_survives_every_query_rotation():
    episode_size = GEN.EXAMPLES_NEEDED + 1
    assert episode_size == 6
    for seed in range(8):
        for start in range(6):
            grids = [GEN.generate(seed, start + i, difficulty="medium") for i in range(episode_size)]
            observed = [GEN.observe_overrides(grid) for grid in grids]
            texture_counts = {
                texture: sum(item["texture"] == texture for item in observed)
                for texture in GEN.TEXTURES
            }
            assert texture_counts == {texture: 2 for texture in GEN.TEXTURES}
            assert sum(item["color_mode"] == "shared" for item in observed) == 4
            assert sum(GEN.SEMANTIC_WITNESSES["orthogonal_context_pair"](grid) for grid in grids) == 2
            for query_index in range(episode_size):
                demos = [_pair(grid) for i, grid in enumerate(grids) if i != query_index]
                assert GEN.lesson_identifiable(demos, _pair(grids[query_index])) == []


def test_mismatched_diagonals_refute_ignore_equality_shortcut():
    grid = [
        [1, 0, 2],
        [0, 0, 0],
        [3, 0, 4],
    ]
    intended = GEN._apply_rule(grid)
    rival = GEN.SEMANTIC_RIVALS["ignore_diagonal_color_equality"](grid)
    assert intended == grid
    assert rival[1][1] == 1
    assert rival != intended


def test_repeated_color_scene_refutes_exactly_four_occurrences_shortcut():
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
    assert GEN.SEMANTIC_RIVALS["fill_colors_occurring_exactly_four_times"](grid) != GEN._apply_rule(grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)]],
)
def test_malformed_grids_return_diagnostics_instead_of_raising(grid):
    assert GEN.self_check(grid)


def test_portable_workspace_probe_runs_and_reports_canonical_and_schedule_checks():
    probe = HOME / "workspace" / "reference_probe.py"
    assert probe.is_file(), "review repair must retain a reusable source-local probe"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [sys.executable, str(probe), "--quick"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert report["task_id"] == TASK_ID
    assert report["canonical"]["failed"] == 0
    assert report["generated"]["failed"] == 0
    assert report["lessons"]["failed"] == 0
    assert set(report["generated"]["textures"]) == set(GEN.TEXTURES)


def test_retained_exact_four_counterexample_replays_from_source():
    path = HOME / "counterexamples" / "fill_colors_occurring_exactly_four_times.json"
    record = json.loads(path.read_text())
    grid = GEN.generate(
        record["seed"],
        record["sample_index"],
        difficulty=record["difficulty"],
    )
    assert grid == record["input"]
    assert GEN.observe_overrides(grid) == record["observed"]
    assert GEN._apply_rule(grid) == record["intended_output"]
    assert (
        GEN.SEMANTIC_RIVALS[record["rival"]](grid)
        == record["rival_output"]
    )
    assert record["intended_output"] != record["rival_output"]
    assert record["authority_verification"]["matches_intended_output"] is True
    assert record["authority_verification"]["differs_from_rival_output"] is True
