"""Task-local regressions for the repaired column-legend curriculum."""
from __future__ import annotations

from copy import deepcopy
import ast
import itertools
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    RIVALS,
    canonical_pairs,
    load_generator,
    observed,
    rule_output,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "n_legend",
    "body_cells",
    "body_colors",
    "off_legend",
}


def _pair(seed: int, index: int, band: str | None) -> dict:
    grid = GEN.generate(seed, index, difficulty=band)
    return {"input": grid, "output": rule_output(grid)}


def test_axes_metadata_is_a_static_literal_for_repository_lint() -> None:
    tree = ast.parse(Path(GEN.__file__).read_text())
    axes_node = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    parsed = ast.literal_eval(axes_node)
    assert set(parsed) == EXPECTED_AXES


def test_rule_authority_and_public_contract_are_pinned() -> None:
    assert GEN.RULE_HASH == "6f9bcb74d69f"
    assert set(GEN.AXES) == EXPECTED_AXES
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"{pair['split']}-{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair: dict) -> None:
    before = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert pair["input"] == before


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_joint_overrides_are_observable_in_every_band(band: str | None) -> None:
    requested = {
        "grid_h": 10,
        "grid_w": 5,
        "n_legend": 4,
        "body_cells": 4,
        "body_colors": "mixed",
        "off_legend": 4,
    }
    grid = GEN.generate(193, 17, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert observed(grid) == requested
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_advertised_boundary_combination_is_constructive(band: str | None) -> None:
    values = {
        "grid_h": (5, 10),
        "grid_w": (5, 10),
        "n_legend": (2, 4),
        "body_cells": (1, 4),
        "body_colors": ("uniform7", "uniform_other", "mixed"),
        "off_legend": (0, 4),
    }
    for index, combination in enumerate(itertools.product(*values.values())):
        requested = dict(zip(values, combination))
        grid = GEN.generate(12000 + index, 500 + index, difficulty=band, **requested)
        assert GEN.self_check(grid) == [], (band, requested)
        assert observed(grid) == requested
        assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 4},
        {"grid_h": 11},
        {"grid_w": 4},
        {"grid_w": 11},
        {"n_legend": 1},
        {"n_legend": 5},
        {"body_cells": 0},
        {"body_cells": 5},
        {"off_legend": -1},
        {"off_legend": 5},
        {"body_colors": "orange_only"},
        {"grid_h": 5.0},
        {"grid_w": True},
        {"n_legend": "3"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides: dict) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_invalid_difficulty_is_rejected() -> None:
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_has_each_exact_canonical_profile_in_every_band(band: str) -> None:
    grids = [GEN.generate(8801, index, difficulty=band) for index in range(20)]
    profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in grids
    }
    assert {(5, 5, 5), (6, 6, 5), (7, 7, 5)} <= profiles
    assert {GEN.schedule_profile(8801, index, band) for index in range(20)} == set(
        GEN.SCHEDULE_PROFILES
    )
    assert all(GEN.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(12))
def test_every_four_demo_window_refutes_declared_competitors(
    band: str | None, start: int
) -> None:
    demos = [_pair(7331, start + offset, band) for offset in range(GEN.EXAMPLES_NEEDED)]
    query = _pair(7331, start + GEN.EXAMPLES_NEEDED, band)
    assert GEN.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), (
            band,
            start,
            name,
        )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_query_rotation_of_five_linked_pairs_still_refutes_competitors(
    band: str | None, start: int
) -> None:
    pairs = [_pair(8111, start + offset, band) for offset in range(5)]
    for query_index in range(5):
        demos = [deepcopy(pair) for index, pair in enumerate(pairs) if index != query_index]
        query = deepcopy(pairs[query_index])
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                band,
                start,
                query_index,
                name,
            )


def test_declared_shortcuts_really_fit_all_canonical_pairs() -> None:
    pairs = canonical_pairs()
    assert set(GEN.CANONICAL_SHORTCUTS) == set(RIVALS)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in pairs), name


def test_four_profile_schedule_separates_color_and_erasure_factors() -> None:
    expected_profiles = {
        "canonical_anchor",
        "color_counterexample",
        "erasure_counterexample_a",
        "erasure_counterexample_b",
    }
    assert set(GEN.SCHEDULE_PROFILES) == expected_profiles
    assert set(GEN.SEMANTIC_RIVALS) == set(RIVALS)
    for start in range(12):
        grids = [GEN.generate(991, start + offset, difficulty="medium") for offset in range(4)]
        profiles = {GEN.schedule_profile(991, start + offset, "medium") for offset in range(4)}
        assert profiles == expected_profiles
        by_profile = {
            GEN.schedule_profile(991, start + offset, "medium"): grid
            for offset, grid in enumerate(grids)
        }
        anchor = observed(by_profile["canonical_anchor"])
        color_only = observed(by_profile["color_counterexample"])
        assert anchor["body_colors"] == "uniform7" and anchor["off_legend"] == 0
        assert color_only["body_colors"] == "mixed" and color_only["off_legend"] == 0
        for profile in ("erasure_counterexample_a", "erasure_counterexample_b"):
            grid = by_profile[profile]
            row = observed(grid)
            assert row["body_colors"] == "mixed" and row["off_legend"] >= 2
            header = grid[0]
            off_values = {
                value
                for body_row in grid[1:]
                for col, value in enumerate(body_row)
                if header[col] == 0 and value != 0
            }
            assert 7 in off_values
            assert any(value != 7 for value in off_values)


def test_declared_witnesses_are_real_counterexamples() -> None:
    witness_hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    rival_hits = {name: 0 for name in GEN.SEMANTIC_RIVALS}
    for index in range(32):
        grid = GEN.generate(991, index, difficulty="medium")
        truth = rule_output(grid)
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                witness_hits[name] += 1
                for rival_name in GEN.WITNESS_RIVALS[name]:
                    assert GEN.SEMANTIC_RIVALS[rival_name](deepcopy(grid)) != truth
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            assert rival(deepcopy(grid)) == RIVALS[name](grid)
            rival_hits[name] += rival(deepcopy(grid)) != truth
    assert all(witness_hits.values())
    assert all(rival_hits.values())


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(4)] + [[11] * 5],
    ],
)
def test_malformed_or_semantically_empty_grids_are_diagnostic(grid) -> None:
    assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "mutation",
    ["ragged", "duplicate_header", "remove_body", "orphan_header", "invisible_rule"],
)
def test_self_check_rejects_destructive_mutations(mutation: str) -> None:
    grid = GEN.generate(43, 6, grid_h=6, grid_w=6, n_legend=3, body_cells=2)
    legend_cols = [col for col, value in enumerate(grid[0]) if value]
    if mutation == "ragged":
        grid[-1].pop()
    elif mutation == "duplicate_header":
        grid[0][legend_cols[1]] = grid[0][legend_cols[0]]
    elif mutation == "remove_body":
        for row in range(1, len(grid)):
            for col in range(len(grid[0])):
                grid[row][col] = 0
    elif mutation == "orphan_header":
        col = legend_cols[0]
        for row in range(1, len(grid)):
            grid[row][col] = 0
    elif mutation == "invisible_rule":
        for col in legend_cols:
            for row in range(1, len(grid)):
                if grid[row][col] != 0:
                    grid[row][col] = grid[0][col]
    assert GEN.self_check(grid)


def test_replay_is_deterministic_and_call_order_independent() -> None:
    expected = GEN.generate(1201, 17, difficulty="hard")
    for index in range(100):
        GEN.generate(index, index * 7, difficulty="easy")
    assert GEN.generate(1201, 17, difficulty="hard") == expected


def test_keyed_rng_is_independent_of_python_hash_seed() -> None:
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator(sys.argv[2]).generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    script,
                    str(HOME / "workspace"),
                    str(Path(GEN.__file__).resolve()),
                ],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]
