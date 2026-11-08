"""Focused regression suite for generator 7c2b3290ba62."""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "7c2b3290ba62"
HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate).resolve() if candidate else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("review_7c2b3290ba62", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _colors(grid):
    return {value for row in grid for value in row}


def test_rule_binding_and_all_canonical_pairs():
    assert gen.RULE_HASH == "8518d3e47ce6"
    assert gen.VERSION == "3.1.0"
    assert set(gen.AXES) == {"panel_h", "panel_w", "n_cands"}
    assert len(PAIRS) == 3
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"panel_h": 3, "panel_w": 2, "n_cands": 7},
        {"panel_h": 6, "panel_w": 3, "n_cands": 5},
        {"panel_h": 4, "panel_w": 4, "n_cands": 4},
        {"panel_h": 5, "panel_w": 4, "n_cands": 3},
    ],
)
def test_compatible_exact_overrides_are_honored_in_every_band(band, overrides):
    grid = gen.generate(173, 29, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "kwargs",
    [
        {"invented_axis": 1},
        {"panel_h": 2},
        {"panel_h": 7},
        {"panel_w": True},
        {"panel_w": 2.5},
        {"n_cands": "4"},
        {"n_cands": 8},
        {"panel_w": 4, "n_cands": 5},
        {"panel_w": 4, "n_cands": 6},
        {"panel_w": 3, "n_cands": 6},
    ],
)
def test_invalid_unknown_and_incompatible_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(1, 2, **kwargs)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261007)
    state = random.getstate()
    first = gen.generate(111, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(111, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    frozen = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert gen.generate(111, 17, difficulty="hard") == frozen


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_draws_are_lawful_and_refute_named_rivals(band):
    for index in range(32):
        grid = gen.generate(50000 + index, index, difficulty=band)
        truth = gen.rule_mirror(grid)
        assert gen.self_check(grid) == []
        assert 8 not in _colors(grid), "cyan 8 is the output marker and must be absent from inputs"
        observed = gen.observe_overrides(grid)
        assert 3 <= observed["panel_h"] <= 6
        assert 2 <= observed["panel_w"] <= 4
        assert 3 <= observed["n_cands"] <= 7
        assert len(truth) == 1
        assert len(truth[0]) == observed["n_cands"]
        assert truth[0].count(8) == 2
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), (band, index, name)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != truth, (band, index, name)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_hits_exact_canonical_profile_in_every_band(band):
    hits = []
    for index in range(8):
        grid = gen.generate(700, index, difficulty=band)
        if gen.strict_canonical_like(grid) == []:
            hits.append(grid)
    assert hits
    assert all((len(grid), len(grid[0]), len(_colors(grid))) == (4, 29, 7) for grid in hits)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sliding_lesson_is_identifiable_against_declared_competitors(band):
    for start in range(12):
        pairs = [
            _pair(gen.generate(9000 + start, start + offset, difficulty=band))
            for offset in range(gen.EXAMPLES_NEEDED + 1)
        ]
        assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:-1]), name


def test_lint_horizon_covers_the_complete_finite_output_codomain():
    signatures = set()
    # Mirror lint_generator.py's diversity horizon exactly: 24 episodes,
    # six sequential examples each, and episode seeds spaced by 101.
    for episode in range(24):
        seed = episode * 101
        for index in range(6):
            output = gen.rule_mirror(gen.generate(seed, index))[0]
            signatures.add((len(output), tuple(i for i, value in enumerate(output) if value == 8)))
    assert gen.EXPECTED_OUTPUT_CODOMAIN == sum(n * (n - 1) // 2 for n in range(3, 8))
    assert len(signatures) == gen.EXPECTED_OUTPUT_CODOMAIN


def test_self_check_rejects_separator_damage_and_ambiguous_pair():
    grid = gen.generate(404, 3, panel_h=4, panel_w=4, n_cands=4)
    assert gen.self_check(grid) == []

    broken_separator = copy.deepcopy(grid)
    separator_col = 4
    broken_separator[0][separator_col] = 0
    assert gen.self_check(broken_separator)

    panels = gen._split_panels(grid)
    truth = gen.rule_mirror(grid)[0]
    good = [index for index, value in enumerate(truth) if value == 8]
    bad = next(index for index in range(4) if index not in good)
    ambiguous = copy.deepcopy(grid)
    # Replace one distractor panel with one of the true candidate panels. This
    # creates a second completing pair while keeping panel geometry intact.
    pw = 4
    dst_start = (2 + bad) * (pw + 1)
    src_start = (2 + good[0]) * (pw + 1)
    for row in range(4):
        ambiguous[row][dst_start : dst_start + pw] = ambiguous[row][src_start : src_start + pw]
    assert gen.self_check(ambiguous)
