"""Regression tests for the Nested Palette Fill generator repair."""
from __future__ import annotations

import copy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    nested_palette_output,
    observed,
    output_profile,
    load_generator,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_contract_surface_pins_rule_and_only_observable_axes():
    assert GEN.RULE_HASH == "5f1e925f80ea"
    assert GEN.VERSION == "3.1.0"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "palette_size", "scene_kind"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert callable(getattr(GEN, "observe_overrides", None))
    assert callable(getattr(GEN, "rule_mirror", None))


def test_all_canonical_pairs_are_accepted_and_match_independent_rule():
    for pair in canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert nested_palette_output(source) == pair["output"]
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"], "validation/oracles must not mutate input"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 11, "grid_w": 13, "palette_size": 2, "scene_kind": "two_clean"},
        {"grid_h": 15, "grid_w": 17, "palette_size": 3, "scene_kind": "malformed_inner"},
        {"grid_h": 11, "grid_w": 13, "palette_size": 2, "scene_kind": "three_clean"},
        {"grid_h": 15, "grid_w": 17, "palette_size": 3, "scene_kind": "warped_inner"},
    ],
)
def test_exact_override_boundaries_are_realized_in_every_band(band, overrides):
    grid = GEN.generate(911, 7, difficulty=band, **overrides)
    assert GEN.self_check(grid) == []
    assert observed(grid) == overrides
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.rule_mirror(grid) == nested_palette_output(grid)
    assert GEN.generate(911, 7, difficulty=band, **overrides) == grid


@pytest.mark.parametrize(
    "override",
    [
        {"unknown_axis": 1},
        {"grid_h": 10},
        {"grid_h": 16},
        {"grid_w": 12},
        {"grid_w": 18},
        {"palette_size": 1},
        {"palette_size": 4},
        {"scene_kind": "single_frame"},
        {"grid_h": True},
        {"grid_w": 13.0},
        {"palette_size": "2"},
        {"scene_kind": 2},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(override):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **override)


def test_each_scene_refutes_its_plausible_wrong_rule():
    two = GEN.generate(
        101, 1, grid_h=14, grid_w=15, palette_size=2, scene_kind="two_clean"
    )
    malformed = GEN.generate(
        102, 2, grid_h=14, grid_w=15, palette_size=3,
        scene_kind="malformed_inner",
    )
    exhausted = GEN.generate(
        103, 3, grid_h=14, grid_w=15, palette_size=2, scene_kind="three_clean"
    )

    intended_two = nested_palette_output(two)
    assert GEN.SEMANTIC_WITNESSES["nested_depth"](two)
    assert GEN.SEMANTIC_RIVALS["outermost_only"](two) != intended_two

    intended_malformed = nested_palette_output(malformed)
    assert GEN.SEMANTIC_WITNESSES["malformed_object_filter"](malformed)
    assert GEN.SEMANTIC_RIVALS["all_color8_bboxes"](malformed) != intended_malformed

    intended_exhausted = nested_palette_output(exhausted)
    assert GEN.SEMANTIC_WITNESSES["palette_exhaustion"](exhausted)
    assert GEN.SEMANTIC_RIVALS["clamp_palette"](exhausted) != intended_exhausted
    assert GEN.CANONICAL_SHORTCUTS["clamp_palette"](exhausted) != intended_exhausted


def test_size_equals_perimeter_branch_refutes_exact_perimeter_shortcut():
    assert "exact_perimeter_only" in GEN.CANONICAL_SHORTCUTS
    assert "exact_perimeter_only" in GEN.SEMANTIC_RIVALS

    grid = GEN.generate(104, 4, grid_h=14, grid_w=15, palette_size=3,
                        scene_kind="warped_inner")
    intended = nested_palette_output(grid)

    assert GEN.self_check(grid) == []
    assert observed(grid)["scene_kind"] == "warped_inner"
    assert GEN.observe_overrides(grid)["scene_kind"] == "warped_inner"
    assert GEN.SEMANTIC_WITNESSES["size_equals_perimeter"](grid)
    assert GEN.SEMANTIC_RIVALS["exact_perimeter_only"](grid) != intended
    assert all(
        GEN.CANONICAL_SHORTCUTS["exact_perimeter_only"](pair["input"])
        == pair["output"]
        for pair in canonical_pairs()
    )


def test_warped_inner_varies_swap_location_without_changing_predicate():
    signatures = set()
    for seed in range(64):
        grid = GEN.generate(seed, 4, grid_h=14, grid_w=15, palette_size=3,
                            scene_kind="warped_inner")
        assert GEN.self_check(grid) == []
        warped = [
            component
            for component in GEN._color8_components(grid)
            if GEN._authority_frame(component) and not GEN._clean_frame(component)
        ]
        assert len(warped) == 1
        component = warped[0]
        box = GEN._bbox(component)
        perimeter = GEN._perimeter(box)
        missing = next(iter(perimeter - component))
        added = next(iter(component - perimeter))
        signatures.add((missing[0] - box[0], missing[1] - box[1],
                        added[0] - box[0], added[1] - box[1]))

    assert len(signatures) >= 4


def test_declared_canonical_shortcut_really_fits_every_canonical_pair():
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(
            shortcut(pair["input"]) == pair["output"]
            for pair in canonical_pairs()
        ), name


def test_pinned_profile_census_has_exact_support_in_every_band():
    import hashlib

    def pinned_seed(task_id, band, index):
        digest = hashlib.sha256(
            f"profile-floor:v1:{task_id}:{band}:{index}".encode()
        ).hexdigest()
        return int(digest[:12], 16)

    canonical_profiles = {output_profile(pair["input"]) for pair in canonical_pairs()}
    for band in ("easy", "medium", "hard"):
        profiles = set()
        for index in range(20):
            seed = pinned_seed(GEN.TASK_ID, band, index)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            assert GEN.self_check(grid) == []
            profiles.add(output_profile(grid))
        assert profiles & canonical_profiles, (band, profiles, canonical_profiles)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 13 for _ in range(11)]],
)
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "mutation",
    ["palette_gap", "palette_duplicate", "gap_column", "broken_frame", "unknown_color"],
)
def test_self_check_rejects_structural_impostors(mutation):
    grid = GEN.generate(
        301, 5, grid_h=14, grid_w=15, palette_size=3, scene_kind="two_clean"
    )
    if mutation == "palette_gap":
        grid[1][0], grid[4][0] = 0, grid[1][0]
    elif mutation == "palette_duplicate":
        grid[1][0] = grid[0][0]
    elif mutation == "gap_column":
        grid[0][1] = 8
    elif mutation == "broken_frame":
        point = next(
            (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == 8
        )
        grid[point[0]][point[1]] = 0
    elif mutation == "unknown_color":
        palette = {row[0] for row in grid if row[0] not in (0, 8)}
        grid[-1][-1] = next(color for color in range(1, 10)
                            if color != 8 and color not in palette)
    assert GEN.self_check(grid)


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(41,13,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "991"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]

@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_three_demo_window_refutes_all_declared_lesson_competitors(band):
    assert set(GEN.SCHEDULE_PROFILES) == {
        "nested_depth", "malformed_object_filter", "palette_exhaustion"
    }
    expected_witnesses = set(GEN.SEMANTIC_WITNESSES)
    expected_rivals = set(GEN.LESSON_COMPETITORS)
    for start in range(6):
        grids = [GEN.generate(7001 + start, start + offset, difficulty=band)
                 for offset in range(3)]
        witnesses = {
            name for name, predicate in GEN.SEMANTIC_WITNESSES.items()
            if any(predicate(grid) for grid in grids)
        }
        assert witnesses == expected_witnesses
        refuted = {
            name for name, rival in GEN.LESSON_COMPETITORS.items()
            if any(rival(grid) != nested_palette_output(grid) for grid in grids)
        }
        assert refuted == expected_rivals
        assert {
            GEN.schedule_profile(7001 + start, start + offset, difficulty=band)
            for offset in range(3)
        } == set(GEN.SCHEDULE_PROFILES)


def test_lesson_identifiable_reports_only_demo_survivors_that_change_query():
    grids = [GEN.generate(8123, index, difficulty="medium") for index in range(4)]
    pairs = [
        {"input": grid, "output": nested_palette_output(grid)}
        for grid in grids
    ]
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []

    reasons = GEN.lesson_identifiable(pairs[:2], pairs[2])
    assert reasons == [
        "clamp_palette survives every demonstration and changes the query answer"
    ]


def test_reference_probe_runs_standalone_from_an_arbitrary_directory(tmp_path):
    report = tmp_path / "probe.json"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("GENERATOR_UNDER_TEST", None)
    result = subprocess.run(
        [
            sys.executable,
            str(HOME / "workspace" / "reference_probe.py"),
            "--count",
            "1",
            "--out",
            str(report),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = __import__("json").loads(report.read_text())
    assert payload["counts"]["samples"] == 4


def test_lesson_probe_cli_is_portable(tmp_path):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(HOME / "workspace" / "lesson_probe.py"), "--help"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "--lessons-per-band" in result.stdout


def test_shortcut_probe_cli_is_portable(tmp_path):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(HOME / "workspace" / "shortcut_probe.py"), "--help"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "--max-draws" in result.stdout


def test_audit_probe_cli_is_portable(tmp_path):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(HOME / "workspace" / "audit_probe.py"), "--help"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "--out-dir" in result.stdout
