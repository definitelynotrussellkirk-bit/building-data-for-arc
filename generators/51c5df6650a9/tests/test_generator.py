"""Task-local regressions for the Legend-Ordered Pack generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest
from reviewer_support import find_root

TASK_ID = "51c5df6650a9"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    body_scan_order_rival,
    canonical_pairs,
    fixed_columns_rival,
    intended_output,
    legend,
)


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs()
PROFILES = {
    "h10_w13": (10, 13),
    "h11_w14": (11, 14),
    "h10_w12": (10, 12),
    "h12_w14": (12, 14),
    "h11_w13": (11, 13),
}


def _episode(seed: int, start: int, band: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, start + offset, difficulty=band)
        demos.append({"input": grid, "output": intended_output(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    return demos, {"input": query_grid, "output": intended_output(query_grid)}


def test_rule_pin_and_all_canonical_pairs_match_independent_mirror():
    assert gen.RULE_HASH == "4ec427a9d6d9"
    assert len(PAIRS) == 5
    for pair in PAIRS:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.reference_output(pair["input"]) == pair["output"]
        assert intended_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_seed20_rule_crash_reproducer_has_a_blank_separator_row():
    grid = gen.generate(20, 20, difficulty="easy")
    assert all(value == 0 for value in grid[1])
    for column, color in enumerate(grid[0]):
        if color:
            assert grid[1][column] != color
    assert gen.self_check(grid) == []
    assert gen.reference_output(grid) == intended_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile,dims", PROFILES.items())
@pytest.mark.parametrize("n_legend", [2, 3, 4])
@pytest.mark.parametrize("layout", ["contiguous", "shifted", "canonical"])
def test_exact_overrides_are_honored_and_observable(profile, dims, n_legend, layout, band):
    requested = {"profile": profile, "n_legend": n_legend, "legend_layout": layout}
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert (len(grid), len(grid[0])) == dims
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert gen.reference_output(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("profile", "h9_w9"),
        ("profile", 10),
        ("n_legend", 1),
        ("n_legend", 5),
        ("n_legend", True),
        ("legend_layout", "random"),
        ("legend_layout", 3),
    ],
)
def test_invalid_or_unknown_overrides_raise(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["invalid", 0, True])
def test_invalid_difficulty_raises(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_diverse_and_answer_relevant(band):
    profiles = set()
    counts = set()
    layouts = set()
    distinct = set()
    for index in range(60):
        grid = gen.generate(10_000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert all(value == 0 for value in grid[1])
        assert gen.reference_output(grid) == intended_output(grid)
        assert body_scan_order_rival(grid) != intended_output(grid)
        assert fixed_columns_rival(grid) != intended_output(grid)
        facts = gen.observe_overrides(grid)
        profiles.add(facts["profile"])
        counts.add(facts["n_legend"])
        layouts.add(facts["legend_layout"])
        distinct.add(json.dumps(grid, separators=(",", ":")))
    assert profiles == set(PROFILES)
    assert counts == {2, 3, 4}
    assert layouts == {"contiguous", "shifted"}
    assert len(distinct) >= 58


def test_fixed_column_shortcut_fits_every_canonical_pair():
    assert "fixed_columns_0_2_4" in gen.CANONICAL_SHORTCUTS
    rival = gen.CANONICAL_SHORTCUTS["fixed_columns_0_2_4"]
    for pair in PAIRS:
        assert rival(pair["input"]) == pair["output"]
        assert fixed_columns_rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sliding_lesson_refutes_declared_competitors(band):
    for start in range(20):
        demos, query = _episode(91_000 + start, start, band)
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(grid), name


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(10)]])
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(51_665)
    state = random.getstate()
    first = gen.generate(412, 111, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(412, 111, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0 if first[0][0] else 1
    assert first != second
    assert second != gen.generate(413, 111, difficulty="hard")
    assert second != gen.generate(412, 112, difficulty="hard")
