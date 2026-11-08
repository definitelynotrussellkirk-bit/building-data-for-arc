"""Regression tests for the vertical guide-bar reflection sampler.

The Python oracle below is intentionally independent of generator internals.  The
selected Racket program remains the label authority; these tests protect its
observable input contract and the sampler's teaching distribution.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "4a9e2bc51201"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("reviewed_4a9e2bc51201", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def oracle(grid):
    """Apply the published empty-target mirror rule from original input cells."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not dividers:
        return out
    div = dividers[0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5) or c == div:
                continue
            mc = 2 * div - c
            if 0 <= mc < w and out[r][mc] == 0:
                out[r][mc] = value
    return out


def profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=ROOT),
    ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}",
)
def test_canonical_inputs_are_owned_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]


def test_conflicting_occupied_mirror_pair_is_preserved_not_rejected():
    # The official test contains 6|5|3.  Both mirror cells are occupied and the
    # canonical rule deliberately preserves them rather than overwriting either.
    pair = next(
        p for p in canonical_pairs(TASK, root=ROOT)
        if p["split"] == "test"
    )
    grid = pair["input"]
    assert grid[2][2] == 6 and grid[2][6] == 3
    assert gen.self_check(grid) == []
    assert oracle(grid)[2][2] == 6
    assert oracle(grid)[2][6] == 3


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=6, grid_w=7, divider_bias="left", n_open_pairs=4,
             n_occupied_pairs=0, open_side="left", n_distinct_colors=1),
        dict(grid_h=11, grid_w=11, divider_bias="right", n_open_pairs=8,
             n_occupied_pairs=3, open_side="right", n_distinct_colors=4),
        dict(grid_h=8, grid_w=10, divider_bias="center", n_open_pairs=7,
             n_occupied_pairs=2, open_side="mixed", n_distinct_colors=3),
    ],
)
def test_every_advertised_override_is_exact_and_observable(band, options):
    grid = gen.generate(317, 29, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert oracle(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 5), ("grid_h", 12), ("grid_h", True), ("grid_h", 7.5),
        ("grid_w", 6), ("grid_w", 12), ("grid_w", "9"),
        ("divider_bias", "diagonal"),
        ("n_open_pairs", 3), ("n_open_pairs", 9), ("n_open_pairs", 4.0),
        ("n_occupied_pairs", -1), ("n_occupied_pairs", 4),
        ("open_side", "both"),
        ("n_distinct_colors", 0), ("n_distinct_colors", 5),
    ],
)
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_lawful_and_shortcut_resistant(band):
    shapes = set()
    divider_biases = set()
    exact_profiles = set()
    canonical_profiles = {
        profile(p["input"]) for p in canonical_pairs(TASK, root=ROOT)
    }
    for index in range(96):
        seed = 10_000 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert oracle(grid) != grid

        observed = gen.observe_overrides(grid)
        shapes.add((observed["grid_h"], observed["grid_w"]))
        divider_biases.add(observed["divider_bias"])
        if profile(grid) in canonical_profiles:
            exact_profiles.add(profile(grid))

        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), name
        intended = oracle(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(deepcopy(grid)) != intended, name

    assert len(shapes) >= 8
    assert divider_biases == {"left", "center", "right"}
    assert exact_profiles, "every band needs exact canonical-profile support"


def test_declared_lesson_contract_rejects_query_changing_survivors():
    pairs = []
    for index in range(4):
        grid = gen.generate(901, index, difficulty="medium")
        pairs.append({"input": grid, "output": oracle(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []

    # A fabricated one-sided lesson leaves the opposite-direction shortcut alive.
    demos = []
    for index in range(3):
        grid = gen.generate(
            902, index, difficulty="medium", open_side="left",
            n_occupied_pairs=0, n_distinct_colors=2,
        )
        demos.append({"input": grid, "output": oracle(grid)})
    query_grid = gen.generate(
        903, 7, difficulty="medium", open_side="right",
        n_occupied_pairs=0, n_distinct_colors=2,
    )
    reasons = gen.lesson_identifiable(
        demos, {"input": query_grid, "output": oracle(query_grid)}
    )
    assert any("left_to_right_only" in reason for reason in reasons)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 5, 0]],
        [[0, 5, 10]],
    ],
)
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_missing_or_extra_guide_and_identity_inputs():
    grid = gen.generate(55, 9)

    no_guide = deepcopy(grid)
    div = next(c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid))
    for row in no_guide:
        row[div] = 0
    assert gen.self_check(no_guide)

    extra_five = deepcopy(grid)
    extra_five[0][0] = 5
    assert gen.self_check(extra_five)

    symmetric = [[0] * 7 for _ in range(6)]
    for row in symmetric:
        row[3] = 5
    symmetric[2][1] = symmetric[2][5] = 4
    assert gen.self_check(symmetric)


def test_generation_does_not_mutate_global_random_state():
    random.seed(418)
    before = random.getstate()
    gen.generate(77, 12, difficulty="hard")
    assert random.getstate() == before


def test_workspace_probe_replays_core_contract():
    probe_path = HOME / "workspace" / "reflection_audit.py"
    spec = importlib.util.spec_from_file_location("reflection_audit_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.run_audit(count=8, bands=("easy",))
    assert report["status"] == "pass"
    assert report["canonical"]["accepted"] == 5
    assert report["per_band"]["easy"]["samples"] == 8
    assert report["per_band"]["easy"]["self_check_errors"] == 0
    assert report["per_band"]["easy"]["rival_disagreement_samples"] == {
        name: 8 for name in sorted(gen.SEMANTIC_RIVALS)
    }
