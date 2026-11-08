"""Task-local regression suite for 148cea0afb09.

The geometry and canonical loading helpers live in workspace/review_probe.py and
are independent of the production generator implementation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from review_probe import (  # noqa: E402
    bbox_area,
    canonical_pairs,
    components,
    load_generator,
    observed,
    racket_outputs,
    solve_by_bbox,
    solve_by_size,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize(
    "pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"]
)
def test_canonical_pairs_are_accepted_and_match_independent_solver(pair):
    assert gen.self_check(pair["input"]) == []
    assert solve_by_size(pair["input"]) == pair["output"]


def test_bbox_area_shortcut_fits_every_canonical_pair():
    assert all(solve_by_bbox(pair["input"]) == pair["output"] for pair in canonical_pairs())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    options = {
        "grid_h": 10,
        "grid_w": 13,
        "n_components": 2,
        "rank": 2,
        "component_color": 9,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert solve_by_size(grid) != solve_by_bbox(grid)


@pytest.mark.parametrize(
    "options",
    [
        {"typo": 1},
        {"grid_h": 9},
        {"grid_w": 14},
        {"n_components": 1},
        {"n_components": 4},
        {"rank": 0},
        {"rank": 4},
        {"component_color": 3},
        {"component_color": 10},
        {"grid_h": True},
        {"rank": 2.5},
        {"component_color": "6"},
        {"n_components": 2, "rank": 3},
    ],
)
def test_invalid_or_incompatible_overrides_fail_loudly(options):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **options)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_domain_is_deterministic_lawful_and_refutes_bbox_rival(band):
    profiles = set()
    ranks = set()
    component_counts = set()
    colors = set()
    inputs = set()
    for index in range(96):
        seed = 1009 + index
        sample_index = index * 7 + 3
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert grid == gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        obs = observed(grid)
        assert gen.observe_overrides(grid) == obs
        assert solve_by_size(grid) != solve_by_bbox(grid)
        comps = components(grid)
        assert len({len(cells) for cells in comps}) == len(comps)
        assert len({bbox_area(cells) for cells in comps}) == len(comps)
        profiles.add((obs["grid_h"], obs["grid_w"]))
        ranks.add(obs["rank"])
        component_counts.add(obs["n_components"])
        colors.add(obs["component_color"])
        inputs.add(json.dumps(grid, separators=(",", ":")))
    assert len(inputs) >= 90
    assert len(profiles) >= 4
    assert {1, 2, 3} <= ranks
    assert component_counts == {2, 3}
    assert len(colors) >= 5


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[10, 0], [0, 0]],
    ],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_minimal_impostors_and_structural_mutations():
    assert gen.self_check([[1, 0], [0, 4]])  # only one component
    assert gen.self_check([[1, 4], [0, 0]])  # rank touches/merges with object

    grid = gen.generate(41, 6, n_components=3, rank=2, component_color=8)
    comps = components(grid)

    tied = [row[:] for row in grid]
    smallest = sorted(comps, key=len)[0]
    second = sorted(comps, key=len)[1]
    # Remove one non-articulation candidate if possible to create an equal size;
    # otherwise duplicate one isolated-safe boundary cell next to the smallest.
    target_size = len(smallest)
    for r, c in second:
        trial = [row[:] for row in tied]
        trial[r][c] = 0
        sizes = sorted(map(len, components(trial)))
        if sizes.count(target_size) >= 2:
            tied = trial
            break
    assert gen.self_check(tied)

    mixed = [row[:] for row in grid]
    r, c = comps[0][0]
    mixed[r][c] = 7 if grid[r][c] != 7 else 8
    assert gen.self_check(mixed)

    out_of_range = [row[:] for row in grid]
    out_of_range[0][0] = 4
    assert gen.self_check(out_of_range)


def test_semantic_contract_has_real_bbox_counterexample():
    assert gen.MIN_STRICT_FRAC == 1.0
    assert gen.strict_canonical_like(gen.generate(7, 2)) == []
    assert "bbox_area_rank" in gen.SEMANTIC_RIVALS
    assert "bbox_area_counterexample" in gen.SEMANTIC_WITNESSES
    for index in range(48):
        grid = gen.generate(712, index)
        assert gen.SEMANTIC_WITNESSES["bbox_area_counterexample"](grid)
        assert gen.SEMANTIC_RIVALS["bbox_area_rank"](grid) == solve_by_bbox(grid)
        assert gen.SEMANTIC_RIVALS["bbox_area_rank"](grid) != solve_by_size(grid)


def test_lesson_hook_rejects_ambiguous_demo_set_and_accepts_generated_lesson():
    canonical = canonical_pairs()
    query_grid = gen.generate(803, 17)
    query = {"input": query_grid, "output": solve_by_size(query_grid)}
    # The bbox shortcut fits all canonical examples but changes this query.
    assert gen.lesson_identifiable(canonical, query)

    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(803, index)
        demos.append({"input": grid, "output": solve_by_size(grid)})
    assert gen.lesson_identifiable(demos, query) == []


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from review_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_matches_independent_solver_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(319, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(36))
    assert racket_outputs(grids) == [solve_by_size(grid) for grid in grids]


def test_difficulty_bands_change_default_canvas_schedule():
    triples = [
        tuple(
            json.dumps(gen.generate(seed, seed, difficulty=band), separators=(",", ":"))
            for band in ("easy", "medium", "hard")
        )
        for seed in range(1, 21)
    ]
    assert all(len(set(outputs)) > 1 for outputs in triples)


def test_rank_cannot_be_replaced_by_an_absolute_size_lookup():
    """Generated lessons must vary the size profile behind every legal rank case."""
    for n_components in (2, 3):
        for rank in range(1, n_components + 1):
            selected_sizes = set()
            size_profiles = set()
            selected_bbox_ranks = set()
            for index in range(128):
                grid = gen.generate(
                    88000 + 1000 * n_components + 100 * rank + index,
                    index * 11 + 5,
                    n_components=n_components,
                    rank=rank,
                )
                comps = components(grid)
                by_size = sorted(comps, key=len)
                target = by_size[rank - 1]
                selected_sizes.add(len(target))
                size_profiles.add(tuple(sorted(len(cells) for cells in comps)))
                by_bbox = sorted(comps, key=bbox_area)
                selected_bbox_ranks.add(by_bbox.index(target) + 1)

            min_selected_sizes = 2 if (n_components, rank) == (3, 1) else 3
            min_profiles = 4 if (n_components, rank) == (3, 1) else 6
            assert len(selected_sizes) >= min_selected_sizes
            assert len(size_profiles) >= min_profiles
            if n_components == 3:
                assert len(selected_bbox_ranks) >= 2
