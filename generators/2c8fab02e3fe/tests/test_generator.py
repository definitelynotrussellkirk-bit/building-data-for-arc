"""Regression and semantic-contract tests for 2c8fab02e3fe."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import itertools
import hashlib
import json
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "2c8fab02e3fe"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def independent_rule(grid):
    counts = Counter(value for row in grid for value in row)
    keys = [color for color, count in counts.items() if color not in (0, 8) and count == 1]
    if len(keys) != 1:
        raise ValueError(f"expected one singleton key, found {keys}")
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not cells:
        raise ValueError("missing frame color")
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    bottom = max(r for r, _ in cells)
    right = max(c for _, c in cells)
    output = [list(row) for row in grid]
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            output[row][col] = keys[0]
    return output


def _pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def _corner_dot_impostor():
    grid = [[0] * 8 for _ in range(7)]
    for point in ((1, 1), (1, 5), (4, 1), (4, 5)):
        grid[point[0]][point[1]] = 8
    grid[6][7] = 4
    return grid


def test_rule_pin_and_canonical_pairs_match_authority():
    assert GEN.RULE_HASH == "716ceab8f6ca"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert independent_rule(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_joint_override_boundaries_are_constructive_and_observable():
    cases = itertools.product(
        (8, 16),
        (10, 18),
        (4, 7),
        (4, 9),
        (1, 9),
        ("top", "right", "bottom", "left"),
        ("clean", "outside_pair", "inside_pair", "split_pair"),
    )
    for index, (h, w, fh, fw, key, side, mode) in enumerate(cases):
        requested = {
            "grid_h": h,
            "grid_w": w,
            "frame_h": fh,
            "frame_w": fw,
            "key_color": key,
            "key_side": side,
            "decoy_mode": mode,
        }
        grid = GEN.generate(991, index, difficulty=("easy", "medium", "hard")[index % 3], **requested)
        assert GEN.self_check(grid) == [], requested
        assert GEN.observe_overrides(grid) == requested
        assert GEN.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 7},
        {"grid_w": 19},
        {"frame_h": 3},
        {"frame_w": 10},
        {"key_color": 8},
        {"key_side": "diagonal"},
        {"decoy_mode": "singleton_decoy"},
        {"grid_h": True},
        {"frame_w": "9"},
        {"key_color": 4.0},
        {"key_side": 3},
        {"unknown_axis": 1},
        {"difficulty": "extreme"},
    ],
)
def test_invalid_controls_reject_loudly(kwargs):
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


def test_self_check_rejects_the_retained_validator_counterexample_and_near_misses():
    assert GEN.self_check(_corner_dot_impostor())

    good = GEN.generate(
        71,
        2,
        grid_h=10,
        grid_w=12,
        frame_h=6,
        frame_w=8,
        key_color=6,
        key_side="right",
        decoy_mode="split_pair",
    )
    assert GEN.self_check(good) == []

    frame_cells = [(r, c) for r, row in enumerate(good) for c, value in enumerate(row) if value == 8]
    broken = deepcopy(good)
    r, c = frame_cells[0]
    broken[r][c] = 0
    assert GEN.self_check(broken)

    analysis = GEN.analyze_grid(good)
    key_inside = deepcopy(good)
    kr, kc = analysis["key_position"]
    key_inside[kr][kc] = 0
    key_inside[analysis["top"] + 1][analysis["left"] + 1] = analysis["key_color"]
    assert GEN.self_check(key_inside)

    extra_key = deepcopy(good)
    extra_key[0][0] = analysis["key_color"]
    assert GEN.self_check(extra_key)


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "most_frequent_nonframe_color",
        "preserve_existing_interior",
    }
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_four_pair_window_and_query_rotation_is_identifiable(band):
    for start in range(12):
        pairs = [_pair(GEN.generate(1207 + start, start + offset, difficulty=band)) for offset in range(4)]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_covers_roles_profiles_and_high_input_diversity(band):
    grids = [GEN.generate(314159, index, difficulty=band) for index in range(120)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert {item["key_side"] for item in observed} == {"top", "right", "bottom", "left"}
    assert {item["decoy_mode"] for item in observed} == {
        "clean",
        "outside_pair",
        "inside_pair",
        "split_pair",
    }
    assert {item["key_color"] for item in observed} >= {4, 5, 6, 7}
    assert any(item["grid_h"] == 8 and item["grid_w"] == 10 for item in observed)
    assert any(item["frame_h"] != item["frame_w"] for item in observed)
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 116


def test_semantic_witnesses_are_live_and_map_to_real_disagreements():
    expected = {
        "repeated_color_distractor": "most_frequent_nonframe_color",
        "interior_overwrite": "preserve_existing_interior",
        "non_five_key": "constant_five",
        "non_square_frame": "square_only",
        "key_not_below": "below_only",
        "side_color_decoupled": "old_side_color_lookup",
    }
    assert {name: rivals[0] for name, rivals in GEN.WITNESS_RIVALS.items()} == expected
    grids = [GEN.generate(8080, index, difficulty="medium") for index in range(8)]
    for witness_name, rival_name in expected.items():
        hits = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert hits, witness_name
        assert all(GEN.SEMANTIC_RIVALS[rival_name](grid) != independent_rule(grid) for grid in hits)


def test_generation_and_semantic_helpers_are_deterministic_fresh_and_pure():
    random.seed(123456)
    global_state = random.getstate()
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert random.getstate() == global_state
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
                assert first == original
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == original


def test_workspace_probe_reports_joint_boundaries_and_rotation_safe_lessons(tmp_path):
    probe_path = HOME / "workspace" / "probe_curriculum.py"
    spec = importlib.util.spec_from_file_location("probe_curriculum_2c8fab02e3fe", probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.run_probe(starts=4)
    assert report["task_id"] == TASK_ID
    assert report["generator_sha256"]
    assert report["boundary_cases"] == 512
    assert report["boundary_failures"] == []
    assert report["lesson_windows"] == 12
    assert report["query_rotations"] == 48
    assert report["lesson_failures"] == []
    assert report["canonical_shortcuts_checked"] == 2


def test_retained_counterexample_files_reproduce_validator_and_rival_findings():
    counterexamples = HOME / "counterexamples"
    validator = json.loads(
        (counterexamples / "review-dcabda7bc8743208-validator-corner-dots.json").read_text()
    )
    assert GEN.self_check(validator["input"]) == validator["repaired_self_check"]
    assert GEN.self_check(validator["input"])

    rival = json.loads(
        (counterexamples / "review-dcabda7bc8743208-rival-witness.json").read_text()
    )
    generator_path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    assert hashlib.sha256(generator_path.read_bytes()).hexdigest() == rival["generator_sha256"]
    assert GEN.self_check(rival["input"]) == rival["validator_result"] == []
    assert GEN.rule_mirror(rival["input"]) == rival["racket_output"]
    for name, expected in rival["rival_outputs"].items():
        assert GEN.SEMANTIC_RIVALS[name](rival["input"]) == expected
        assert expected != rival["racket_output"]


def test_default_schedule_decouples_key_color_from_side_and_geometry():
    colors_by_side = {side: set() for side in GEN.KEY_SIDES}
    modes_by_side = {side: set() for side in GEN.KEY_SIDES}
    colors_by_geometry = {}
    for seed in range(32):
        for sample_index in range(8):
            grid = GEN.generate(seed, sample_index, difficulty="medium")
            observed = GEN.observe_overrides(grid)
            side = observed["key_side"]
            colors_by_side[side].add(observed["key_color"])
            modes_by_side[side].add(observed["decoy_mode"])
            geometry = (
                observed["grid_h"],
                observed["grid_w"],
                observed["frame_h"],
                observed["frame_w"],
            )
            colors_by_geometry.setdefault(geometry, set()).add(observed["key_color"])

    assert all(colors == set(GEN.KEY_COLORS) for colors in colors_by_side.values())
    assert all(len(modes) == len(GEN.DECOY_MODES) for modes in modes_by_side.values())
    assert all(len(colors) >= 4 for colors in colors_by_geometry.values())
    assert "old_side_color_lookup" in GEN.SEMANTIC_RIVALS
    assert "side_color_decoupled" in GEN.SEMANTIC_WITNESSES


def test_default_schedule_keeps_at_least_quarter_canonical_profile_support():
    """Pinned profile census stays green after role deconfounding."""
    profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({cell for row in pair["input"] for cell in row}))
        for pair in canonical_pairs(TASK_ID, root=find_root(__file__))
    }
    exact_by_band = {}
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({cell for row in grid for cell in row}))
            exact += profile in profiles
        exact_by_band[band] = exact

    assert all(count > 0 for count in exact_by_band.values()), exact_by_band
    assert sum(exact_by_band.values()) >= 15, exact_by_band
