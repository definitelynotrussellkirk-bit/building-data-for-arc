"""Semantic schedule regressions; these tests execute no reference labels."""
from __future__ import annotations

from collections import Counter
import importlib.util
import sys

import pytest
from reviewer_support import find_root

TASK_ID = "57488f2a7c15"
ROOT = find_root(__file__)
PERIOD = 18
BANDS = ("easy", "medium", "hard")


def load_module(name, source):
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    candidates = (ROOT / "generators" / TASK_ID / "generator.py",
                  ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py")
    source = next(path for path in candidates if path.is_file())
    return load_module("symmetry_schedule_test_generator", source)


@pytest.fixture(scope="module")
def contract():
    source = ROOT / "generators" / TASK_ID / "workspace" / "schedule_contract.py"
    return load_module("symmetry_schedule_contract", source)


def observed_profile(grid):
    """Recover semantics without using generator observers or witness hooks."""
    n = len(grid)
    lower = upper = False
    incomplete_colors = set()
    off_colors = set()
    for r in range(n):
        for c in range(r + 1, n):
            a, b = grid[r][c], grid[c][r]
            assert not (a and b and a != b), "contradictory orbit"
            off_colors.update(value for value in (a, b) if value)
            if a and not b:
                upper = True
                incomplete_colors.add(a)
            elif b and not a:
                lower = True
                incomplete_colors.add(b)
    assert upper or lower, "a profile requires an incomplete source"
    triangle = "mixed" if upper and lower else "upper" if upper else "lower"
    diagonal_colors = {grid[r][r] for r in range(n) if grid[r][r]}
    if not diagonal_colors:
        context = "none"
    elif diagonal_colors & off_colors:
        assert diagonal_colors & incomplete_colors, "sharing only a completed pair is not a copying witness"
        context = "shared"
    else:
        context = "unique"
    return f"{triangle}:{context}"


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", (0, 17))
def test_ordered_profile_windows_cover_context_rivals(generator, contract, band, seed):
    report = contract.analyze_schedule(generator, seed=seed, difficulty=band, period=PERIOD)
    assert report["status"] == "production_profile_pass", report
    assert report["starts_checked"] == PERIOD
    assert report["independent_joint_frequencies"]
    assert not any(report["production_ambiguities"].values())
    # These are the semantic profile weights, not a prescribed tuple ordering.
    expected = {f"{triangle}:{context}": count
                for triangle, count in (("lower", 1), ("upper", 1), ("mixed", 4))
                for context in ("shared", "unique", "none")}
    assert report["joint_profile_counts"] == expected
    assert report["rotation_status"] == "diagnostic_ambiguity_found"
    assert report["first_rotation_counterexamples"], "do not present unsupported universal rotation safety"


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", (0, 17))
def test_generated_draws_realize_all_cyclic_production_windows(generator, contract, band, seed):
    # The extra five draws cover the final start's real continuation rather
    # than reusing grids from the beginning of the period.
    observed = []
    for index in range(PERIOD + generator.EXAMPLES_NEEDED):
        grid = generator.generate(seed, index, difficulty=band)
        actual = observed_profile(grid)
        declared = generator.schedule_profile(seed, index, difficulty=band)
        assert actual == declared, (band, seed, index, declared, actual, grid)
        observed.append(actual)
    assert set(Counter(observed[:PERIOD])) == {
        f"{triangle}:{context}" for triangle in ("lower", "mixed", "upper")
        for context in ("shared", "unique", "none")
    }
    for start in range(PERIOD):
        demos = observed[start:start + generator.EXAMPLES_NEEDED]
        query = observed[start + generator.EXAMPLES_NEEDED]
        for name in contract.RIVAL_NAMES:
            assert (not contract.rival_disagrees(name, query) or
                    any(contract.rival_disagrees(name, profile) for profile in demos)), (
                        band, seed, start, name, demos, query)


def test_superseded_three_demo_proposal_exposes_conditional_shortcut(contract):
    report = contract.rejected_period12_proposal()
    name = "full_only_in_shared"
    assert report["production_ambiguities"][name] > 0
    counterexample = report["first_production_counterexamples"][name]
    assert all(not contract.rival_disagrees(name, profile) for profile in counterexample["demonstrations"])
    assert contract.rival_disagrees(name, counterexample["query"])
