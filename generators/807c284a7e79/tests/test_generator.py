"""Task-local regression suite for 807c284a7e79.

All expected outputs and structural observations come from the independent
workspace helper rather than production-generator internals.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    bfs_output,
    canonical_pairs,
    components,
    load_generator,
    observed,
    racket_outputs,
    shortcut_all_non_walls,
    shortcut_largest_component,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=[f"canonical_{i}" for i in range(5)])
def test_canonical_pairs_are_accepted_and_match_independent_rule(pair):
    assert gen.self_check(pair["input"]) == []
    assert bfs_output(pair["input"]) == pair["output"]


def test_required_metadata_and_semantic_contract_are_pinned():
    assert gen.GENERATOR_ID == "807c284a7e79"
    assert gen.TASK_ID == "807c284a7e79"
    assert gen.RULE_HASH == "229d8e0a7e30"
    assert set(gen.AXES) == {"grid_h", "grid_w", "scene_profile", "wall_orientation"}
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.SEMANTIC_WITNESSES
    assert gen.SEMANTIC_RIVALS
    assert gen.LESSON_COMPETITORS
    assert gen.CANONICAL_SHORTCUTS


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["connected", "split_seed_small", "split_seed_large"])
@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
@pytest.mark.parametrize("shape", [(8, 10), (12, 14)])
def test_boundary_overrides_are_exact_and_recoverable(band, profile, orientation, shape):
    options = {
        "grid_h": shape[0],
        "grid_w": shape[1],
        "scene_profile": profile,
        "wall_orientation": orientation,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 13),
        ("grid_w", 9),
        ("grid_w", 15),
        ("grid_h", True),
        ("grid_h", 9.5),
        ("grid_w", "11"),
        ("scene_profile", "split"),
        ("scene_profile", 1),
        ("wall_orientation", "diagonal"),
        ("wall_orientation", None),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["trivial", 0.4, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_three_consecutive_examples_identify_the_rule(band):
    for start in range(12):
        demos = []
        for index in range(start, start + 3):
            grid = gen.generate(700 + start, index, difficulty=band)
            demos.append({"input": grid, "output": bfs_output(grid)})
        query_grid = gen.generate(1700 + start, start + 3, difficulty=band)
        query = {"input": query_grid, "output": bfs_output(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for rival in gen.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_exposes_connected_disconnected_and_small_seed_chambers(band):
    profiles = []
    for index in range(6):
        grid = gen.generate(101, index, difficulty=band)
        stats = observed(grid)
        profiles.append(stats["scene_profile"])
        assert gen.self_check(grid) == []
    assert profiles == [
        "connected",
        "split_seed_small",
        "split_seed_large",
        "connected",
        "split_seed_small",
        "split_seed_large",
    ]


def test_split_small_is_a_real_counterexample_to_public_shortcuts():
    grid = gen.generate(
        991,
        1,
        grid_h=10,
        grid_w=12,
        scene_profile="split_seed_small",
        wall_orientation="vertical",
    )
    comps = components(grid)
    seed = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
    seed_comp = next(cells for cells in comps if seed in cells)
    intended = bfs_output(grid)
    assert len(comps) == 2
    assert len(seed_comp) < max(map(len, comps))
    assert shortcut_all_non_walls(grid) != intended
    assert shortcut_largest_component(grid) != intended
    assert gen.SEMANTIC_WITNESSES["unreachable_component_preserved"](grid)
    assert gen.SEMANTIC_WITNESSES["seed_in_smaller_component"](grid)


def test_seed_is_recolored_and_both_seed_parities_are_scheduled():
    grids = [gen.generate(81, i) for i in range(4)]
    parities = set()
    for grid in grids:
        seed = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
        parities.add((seed[0] + seed[1]) % 2)
        assert bfs_output(grid)[seed[0]][seed[1]] == 3
        assert gen.SEMANTIC_RIVALS["leave_seed_unchanged"](grid) != bfs_output(grid)
    assert parities == {0, 1}


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 10 for _ in range(8)],
    ],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize(
    "mutation",
    ["erase_seed", "extra_seed", "break_border", "unknown_color", "remove_interior_wall", "isolate_seed"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(404, 0, grid_h=10, grid_w=12, scene_profile="connected")
    if mutation == "erase_seed":
        r, c = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
        grid[r][c] = 0
    elif mutation == "extra_seed":
        point = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0)
        grid[point[0]][point[1]] = 2
    elif mutation == "break_border":
        grid[0][1] = 0
    elif mutation == "unknown_color":
        grid[1][1] = 9
    elif mutation == "remove_interior_wall":
        for r in range(1, len(grid) - 1):
            for c in range(1, len(grid[0]) - 1):
                if grid[r][c] == 8:
                    grid[r][c] = 0
    elif mutation == "isolate_seed":
        r, c = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            grid[r + dr][c + dc] = 8
    assert gen.self_check(grid)


def test_difficulty_changes_unscheduled_size_distribution():
    easy = gen.generate(8128, 5, difficulty="easy")
    medium = gen.generate(8128, 5, difficulty="medium")
    hard = gen.generate(8128, 5, difficulty="hard")
    assert len({(len(g), len(g[0])) for g in (easy, medium, hard)}) >= 2
    assert len(easy) * len(easy[0]) <= len(hard) * len(hard[0])


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_distribution_is_deterministic_diverse_and_rule_changing(band):
    inputs = set()
    shapes = set()
    profiles = set()
    orientations = set()
    for index in range(120):
        grid = gen.generate(2100 + index, index, difficulty=band)
        assert grid == gen.generate(2100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert bfs_output(grid) != grid
        stats = observed(grid)
        assert stats == gen.observe_overrides(grid)
        shapes.add((len(grid), len(grid[0])))
        profiles.add(stats["scene_profile"])
        orientations.add(stats["wall_orientation"])
        inputs.add(json.dumps(grid, separators=(",", ":")))
    assert len(inputs) >= 105
    # Easy intentionally concentrates on smaller canvases; the canonical-size
    # anchors still preserve six distinct shapes, while other bands cover more.
    assert len(shapes) >= (6 if band == "easy" else 8)
    assert profiles == {"connected", "split_seed_small", "split_seed_large"}
    assert orientations == {"vertical", "horizontal"}


def test_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_rule_mirror_is_pure_and_matches_independent_oracle():
    grid = gen.generate(918, 1, scene_profile="split_seed_small")
    original = deepcopy(grid)
    assert gen.rule_mirror(grid) == bfs_output(grid)
    assert grid == original


def test_real_racket_reference_on_canonical_and_counterexamples():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, i, difficulty="hard") for i in range(12)]
    assert racket_outputs(grids) == [bfs_output(grid) for grid in grids]
