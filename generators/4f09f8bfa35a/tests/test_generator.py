"""Regression tests authored against the unchanged 2.1.0 baseline."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    CANONICAL_PROFILES,
    canonical_pairs,
    components,
    load_generator,
    observed,
    oracle_output,
    profile,
    semantic_counterexample,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_hash_is_pinned_to_selected_authority():
    assert getattr(gen, "RULE_HASH", None) == "8710221699c5"


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_canonical_inputs_are_accepted_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert oracle_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(8)], [[10] * 12 for _ in range(8)]])
def test_malformed_grids_return_reasons_instead_of_raising(bad):
    try:
        reasons = gen.self_check(bad)
    except Exception as exc:  # pragma: no cover - the assertion reports the crash
        pytest.fail(f"self_check crashed: {exc}")
    assert reasons


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("n_commands", True), ("n_commands", 0), ("n_commands", 6), ("n_commands", 2.5),
        ("shape_size", True), ("shape_size", 1), ("shape_size", 13), ("shape_size", "8"),
        ("n_distractors", True), ("n_distractors", -1), ("n_distractors", 4),
        ("shape_color", True), ("shape_color", 0), ("shape_color", 10),
    ],
)
def test_invalid_or_unknown_exact_controls_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("n_commands", [1, 3, 5])
@pytest.mark.parametrize("shape_size", [2, 8, 12])
@pytest.mark.parametrize("n_distractors", [0, 1, 2, 3])
@pytest.mark.parametrize("shape_color", [1, 5, 9])
def test_exact_control_cross_product(band, n_commands, shape_size, n_distractors, shape_color):
    controls = {
        "n_commands": n_commands,
        "shape_size": shape_size,
        "n_distractors": n_distractors,
        "shape_color": shape_color,
    }
    grid = gen.generate(7123, n_commands * 1000 + shape_size * 100 + n_distractors * 10 + shape_color,
                        difficulty=band, **controls)
    assert gen.self_check(grid, difficulty=band) == []
    assert observed(grid) == controls
    assert gen.observe_overrides(grid) == controls
    assert len(oracle_output(grid)) <= 30
    assert len(oracle_output(grid)[0]) <= 30


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("index", range(48))
def test_default_distribution_is_lawful_deterministic_and_canonical_profiled(band, index):
    grid = gen.generate(1200 + index, index * 17, difficulty=band)
    assert grid == gen.generate(1200 + index, index * 17, difficulty=band)
    assert gen.self_check(grid, difficulty=band) == []
    assert profile(grid) in CANONICAL_PROFILES
    output = oracle_output(grid)
    assert len(output) <= 30 and len(output[0]) <= 30


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("index", range(24))
def test_every_default_pair_refutes_every_declared_rival(band, index):
    grid = gen.generate(8100 + index, index, difficulty=band)
    expected = oracle_output(grid)
    assert getattr(gen, "SEMANTIC_RIVALS", {})
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert rival(grid) != expected, name
        assert gen.SEMANTIC_WITNESSES[name](grid), name
        assert name in gen.WITNESS_RIVALS[name]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(12))
def test_five_pair_windows_and_all_query_rotations_are_identifiable(band, start):
    pairs = []
    for offset in range(5):
        grid = gen.generate(991, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": oracle_output(grid)})
    for query_index in range(5):
        demos = [pair for i, pair in enumerate(pairs) if i != query_index]
        query = pairs[query_index]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert not all(rival(pair["input"]) == pair["output"] for pair in demos), name


def test_canonical_shortcuts_really_fit_every_canonical_pair():
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    assert shortcuts
    for name, rival in shortcuts.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name


def test_retained_counterexample_refutes_selection_crop_and_command_shortcuts():
    grid = semantic_counterexample()
    assert gen.self_check(grid) == []
    expected = oracle_output(grid)
    assert len(components(grid)) == 4
    for name in (
        "first_component",
        "reverse_largest_tie",
        "component_cells_only",
        "identity_commands",
        "reverse_command_order",
        "sorted_command_order",
        "swap_quarter_turns",
        "pack_without_gaps",
        "monochrome_template",
    ):
        assert gen.SEMANTIC_RIVALS[name](grid) != expected


def test_oracle_and_generation_do_not_mutate_inputs_or_cache_pixels():
    grid = gen.generate(44, 9, difficulty="hard")
    saved = deepcopy(grid)
    _ = oracle_output(grid)
    assert grid == saved
    grid[0][0] = 9
    assert gen.generate(44, 9, difficulty="hard") == saved


def test_generation_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "s=importlib.util.spec_from_file_location('g',sys.argv[1]);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(88,13,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "987"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output([sys.executable, "-B", "-c", script, str(HOME / "generator.py")], env=env, text=True))
    assert results[0] == results[1]


def test_default_outputs_have_training_scale_diversity():
    outputs = []
    for band in ("easy", "medium", "hard"):
        for index in range(32):
            grid = gen.generate(22000 + index, index * 11, difficulty=band)
            outputs.append(repr(oracle_output(grid)))
    assert len(set(outputs)) >= 72


def _same_color_component_count(grid):
    seen = set()
    total = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 or (r, c) in seen:
                continue
            total += 1
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                            and (nr, nc) not in seen and grid[nr][nc] == value):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return total


def test_default_distribution_reaches_canonical_object_count_envelope():
    counts = [
        _same_color_component_count(gen.generate(31000 + i, i, difficulty=band))
        for band in ("easy", "medium", "hard")
        for i in range(12)
    ]
    assert min(counts) <= 8


def test_solid_2x2_minimal_impostor_is_rejected():
    grid = [[0] * 12 for _ in range(8)]
    for r in range(2):
        for c in range(2):
            grid[r][c] = 2
    assert gen.self_check(grid)
