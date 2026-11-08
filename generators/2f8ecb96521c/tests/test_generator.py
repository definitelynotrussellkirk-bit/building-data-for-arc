"""Focused authority, override, semantic, and regression tests for 2f8ecb96521c."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    RIVALS,
    canonical_pairs,
    column_projection_rival,
    load_generator,
    observed,
    rule_output,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")
SMALL_SHAPES = ("3x3", "3x4", "4x3")
LARGE_SHAPES = ("3x5", "5x3", "4x4", "5x5")
LAYOUTS = ("stacked", "side_by_side", "diagonal")
ROLES = ("near", "far")
EXPECTED_AXES = {
    "grid_h", "grid_w", "small_shape", "large_shape", "layout", "small_role"
}


def _profile_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:2f8ecb96521c:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_authority_pin_and_public_contract_are_explicit():
    assert GEN.RULE_HASH == "32d5e32db8fe"
    assert GEN.VERSION != "1.3.0"
    assert set(GEN.AXES) == EXPECTED_AXES
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.SCHEDULE_CYCLE == 5
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "stacked:near", "side_by_side:far", "diagonal:near",
    )
    assert tuple(GEN.schedule_profile(0, i) for i in range(5)) == (
        "stacked:near", "side_by_side:far", "stacked:near",
        "side_by_side:far", "diagonal:near",
    )
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.SEMANTIC_RIVALS) == set(RIVALS)
    assert set(GEN.LESSON_COMPETITORS) == set(RIVALS)


@pytest.mark.parametrize("pair", canonical_pairs(), ids=("train0", "train1", "test0"))
def test_all_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    original = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", BANDS)
def test_every_joint_shape_layout_role_combination_is_constructive_and_exact(band):
    for index, values in enumerate(itertools.product(
        SMALL_SHAPES, LARGE_SHAPES, LAYOUTS, ROLES
    )):
        small_shape, large_shape, layout, small_role = values
        requested = {
            "grid_h": 10,
            "grid_w": 10,
            "small_shape": small_shape,
            "large_shape": large_shape,
            "layout": layout,
            "small_role": small_role,
        }
        grid = GEN.generate(17_001, index, difficulty=band, **requested)
        assert GEN.self_check(grid) == []
        assert observed(grid) == requested
        assert GEN.observe_overrides(grid) == requested
        assert grid == GEN.generate(17_001, index, difficulty=band, **requested)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("grid_h,grid_w", ((10, 10), (10, 14), (14, 10), (14, 14)))
def test_dimension_boundaries_are_exact_in_every_band(band, grid_h, grid_w):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "small_shape": "4x3",
        "large_shape": "3x5",
        "layout": "diagonal",
        "small_role": "far",
    }
    grid = GEN.generate(313, 19, difficulty=band, **requested)
    assert observed(grid) == requested
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "args,kwargs",
    (
        ((True, 0), {}), ((1.0, 0), {}), (("1", 0), {}),
        ((1, True), {}), ((1, 1.0), {}), ((1, "1"), {}), ((1, -1), {}),
        ((1, 0), {"typo_axis": 1}),
        ((1, 0), {"grid_h": True}), ((1, 0), {"grid_h": 10.0}),
        ((1, 0), {"grid_h": 9}), ((1, 0), {"grid_w": 15}),
        ((1, 0), {"small_shape": 3}), ((1, 0), {"small_shape": "5x5"}),
        ((1, 0), {"large_shape": None, "layout": 1}),
        ((1, 0), {"layout": "overlap"}), ((1, 0), {"small_role": "first"}),
        ((1, 0), {"difficulty": "expert"}), ((1, 0), {"difficulty": True}),
    ),
)
def test_invalid_calls_fail_loudly(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


def test_default_schedule_is_rotation_safe_for_every_cyclic_start():
    for band in BANDS:
        for start in range(GEN.SCHEDULE_CYCLE):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = GEN.generate(91_003 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": rule_output(grid)})
                assert GEN.schedule_profile(91_003 + start, sample_index, band) == (
                    f"{observed(grid)['layout']}:{observed(grid)['small_role']}"
                )
            profiles = [
                f"{observed(pair['input'])['layout']}:{observed(pair['input'])['small_role']}"
                for pair in pairs
            ]
            assert sum(profile.startswith("stacked:") for profile in profiles) >= 2
            assert sum(profile.startswith("side_by_side:") for profile in profiles) >= 2
            assert sum(profile.endswith(":far") for profile in profiles) >= 2
            for query_index, query in enumerate(pairs):
                demos = pairs[:query_index] + pairs[query_index + 1:]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in RIVALS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band, start, query_index, name, profiles
                    )


def test_retained_column_projection_counterexample_is_now_generated_and_guarded():
    retained = json.loads(next((HOME / "counterexamples").rglob(
        "2f8ecb96521c-counterexample.json"
    )).read_text())
    grid = retained["input"]
    assert GEN.self_check(grid) == []
    assert rule_output(grid) == retained["actual_racket_output"]
    assert column_projection_rival(grid) == retained["rival_output"]
    assert column_projection_rival(grid) != rule_output(grid)

    generated = GEN.generate(
        17, 0, grid_h=10, grid_w=10,
        small_shape="3x3", large_shape="3x5",
        layout="stacked", small_role="near",
    )
    assert observed(generated)["layout"] == "stacked"
    assert column_projection_rival(generated) != rule_output(generated)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_pinned_profile_floor_has_exact_10x10_support_in_every_band(band):
    hits = 0
    for index in range(20):
        seed = _profile_seed(band, index)
        grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
        hits += (len(grid), len(grid[0]), len({v for row in grid for v in row})) == (10, 10, 2)
    assert hits >= 1


def test_default_distribution_covers_every_axis_and_rival_witness_per_band():
    for band in BANDS:
        values = {name: set() for name in EXPECTED_AXES}
        hashes = set()
        disagreements = {name: 0 for name in RIVALS}
        for index in range(150):
            grid = GEN.generate(700_000 + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            stats = observed(grid)
            assert stats == GEN.observe_overrides(grid)
            for name, value in stats.items():
                values[name].add(value)
            expected = rule_output(grid)
            for name, rival in RIVALS.items():
                disagreements[name] += rival(grid) != expected
            hashes.add(json.dumps(grid, separators=(",", ":")))
        assert values["grid_h"] == set(range(10, 15))
        assert values["grid_w"] == set(range(10, 15))
        assert values["small_shape"] == set(SMALL_SHAPES)
        assert values["large_shape"] == set(LARGE_SHAPES)
        assert values["layout"] == set(LAYOUTS)
        assert values["small_role"] == set(ROLES)
        assert all(count > 0 for count in disagreements.values())
        assert len(hashes) >= 140


@pytest.mark.parametrize(
    "grid",
    (
        None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(10)],
        [[0] * 10 for _ in range(10)], [[9] + [0] * 9 for _ in range(10)],
    ),
)
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors


def test_reference_probe_cli_runs_without_preloaded_pythonpath(tmp_path):
    out = tmp_path / "probe.json"
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(HOME / "workspace" / "reference_probe.py"),
         "--draws", "1", "--out", str(out)],
        cwd=HOME, env=env, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(out.read_text())
    assert report["draws_per_band"] == 1
    assert report["canonical_oracle_matches"] == report["canonical_pairs"]


def test_global_rng_purity_determinism_and_fresh_return_values():
    random.seed(120_901)
    before = random.getstate()
    first = GEN.generate(444, 9, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(444, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    original = first[0][0]
    first[0][0] = 9 if original != 9 else 8
    assert first != second
