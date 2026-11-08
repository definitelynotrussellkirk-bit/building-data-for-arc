"""Regression tests for the masked-submatrix-then-rotate generator."""
from __future__ import annotations

from copy import deepcopy
import ast
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    canonical_pairs,
    first_three_rival,
    ignore_command_rival,
    load_generator,
    observed,
    racket_outputs,
    rule_output,
    selector_span_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _pair(grid):
    return {"input": grid, "output": rule_output(grid)}



def test_axes_declaration_is_static_literal_for_repository_lint():
    tree = ast.parse((HOME / "generator.py").read_text())
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    literal = ast.literal_eval(assignment.value)
    assert set(literal) == {"scene_profile", "cmd", "n_rows", "n_cols"}


def test_full_exact_override_cross_product_is_constructive_and_valid():
    profiles = ("c5x5", "c5x6", "c6x5", "m6x7", "m7x6", "h7x8", "h8x9", "h9x10")
    for band in (None, "easy", "medium", "hard"):
        for profile, command, n_rows, n_cols in itertools.product(
            profiles, range(1, 5), range(1, 5), range(1, 5)
        ):
            options = {
                "scene_profile": profile,
                "cmd": command,
                "n_rows": n_rows,
                "n_cols": n_cols,
            }
            seed = 19 + command * 7 + n_rows * 11 + n_cols * 13
            grid = gen.generate(seed, 22, difficulty=band, **options)
            assert gen.self_check(grid) == [], (band, options, gen.self_check(grid))
            assert gen.observe_overrides(grid) == options

def test_rule_metadata_and_exact_axes_are_pinned():
    assert gen.RULE_HASH == "c03aadcd616e"
    assert gen.VERSION == "4.0.0"
    assert gen.EXAMPLES_NEEDED == 7
    assert gen.LESSON_SCHEDULE_PERIOD == 8
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"scene_profile", "cmd", "n_rows", "n_cols"}


def test_canonical_pairs_match_independent_oracle_and_validator():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert rule_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_first_three_is_a_real_canonical_fitting_shortcut():
    pairs = canonical_pairs()
    assert all(first_three_rival(pair["input"]) == pair["output"] for pair in pairs)
    assert gen.CANONICAL_SHORTCUTS["first_three_selectors"] is gen.SEMANTIC_RIVALS["first_three_selectors"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"scene_profile": "c5x5", "cmd": 1, "n_rows": 1, "n_cols": 1},
        {"scene_profile": "h9x10", "cmd": 4, "n_rows": 4, "n_cols": 4},
        {"scene_profile": "c5x6", "cmd": 2, "n_rows": 3, "n_cols": 4},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert gen.rule_mirror(grid) == rule_output(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"scene_profile": "unknown"},
        {"scene_profile": 5},
        {"cmd": 0},
        {"cmd": 5},
        {"cmd": True},
        {"cmd": 2.0},
        {"cmd": "2"},
        {"n_rows": 0},
        {"n_rows": 5},
        {"n_rows": False},
        {"n_cols": -1},
        {"n_cols": 4.0},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (0, True, None),
        (0, 1.0, None),
        (0, "1", None),
        (0, -1, None),
        (0, 0, "expert"),
        (0, 0, 0.5),
    ],
)
def test_invalid_scalar_call_arguments_are_rejected(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)


def test_generated_distribution_is_dense_canonical_shaped_and_deterministic():
    canonical_shapes = {(5, 5), (5, 6), (6, 5)}
    for band in (None, "easy", "medium", "hard"):
        shapes = set()
        commands = set()
        selector_counts = set()
        distinct = set()
        for index in range(128):
            grid = gen.generate(5000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(5000 + index, index, difficulty=band)
            assert gen.rule_mirror(grid) == rule_output(grid)
            info = observed(grid)
            shapes.add(info["shape"])
            commands.add(info["cmd"])
            selector_counts.add((info["n_rows"], info["n_cols"]))
            distinct.add(repr(grid))
            interior = [value for row in grid[1:] for value in row[1:]]
            assert sum(value != 0 for value in interior) / len(interior) >= 0.75
        assert shapes & canonical_shapes
        assert commands == {1, 2, 3, 4}
        assert any(rows == 4 or cols == 4 for rows, cols in selector_counts)
        assert len(distinct) >= 120


def test_default_schedule_teaches_every_declared_rival_under_every_query_rotation():
    expected = {"first_three_selectors", "ignore_command", "selector_span"}
    assert set(gen.SEMANTIC_RIVALS) == expected
    assert gen.LESSON_COMPETITORS == gen.SEMANTIC_RIVALS
    assert set(gen.WITNESS_RIVALS) == {
        "more_than_three_selectors",
        "non_identity_command",
        "gapped_selectors",
    }
    for band in (None, "easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            grids = [
                gen.generate(9000 + start, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            pairs = [_pair(grid) for grid in grids]
            for query_index in range(len(pairs)):
                query = pairs[query_index]
                demos = pairs[:query_index] + pairs[query_index + 1 :]
                assert gen.lesson_identifiable(demos, query) == []


def test_generated_witnesses_refute_each_declared_rival():
    grids = [gen.generate(700, index, difficulty="hard") for index in range(8)]
    intended = [rule_output(grid) for grid in grids]
    assert any(out != first_three_rival(grid) for grid, out in zip(grids, intended))
    assert any(out != ignore_command_rival(grid) for grid, out in zip(grids, intended))
    assert any(out != selector_span_rival(grid) for grid, out in zip(grids, intended))
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name


def test_validators_reject_destructive_mutations_without_crashing():
    grid = gen.generate(42, 3)
    bad = {}
    bad["empty"] = []
    bad["ragged"] = deepcopy(grid)
    bad["ragged"][-1].pop()
    bad["bad_color"] = deepcopy(grid)
    bad["bad_color"][1][1] = 10
    bad["bad_command"] = deepcopy(grid)
    bad["bad_command"][0][0] = 9
    bad["illegal_top_header"] = deepcopy(grid)
    bad["illegal_top_header"][0][2] = 7
    bad["no_row_selectors"] = deepcopy(grid)
    for row in range(1, len(grid)):
        bad["no_row_selectors"][row][0] = 0
    bad["sparse_payload"] = deepcopy(grid)
    for row in range(1, len(grid)):
        for col in range(1, len(grid[0])):
            bad["sparse_payload"][row][col] = 0
    for name, corrupt in bad.items():
        errors = gen.self_check(corrupt)
        assert errors, name
        assert all(isinstance(error, str) and error for error in errors)


def test_rule_and_rivals_are_input_pure():
    grid = gen.generate(91, 5)
    original = deepcopy(grid)
    functions = [gen.rule_mirror, *gen.SEMANTIC_RIVALS.values()]
    for function in functions:
        function(grid)
        assert grid == original


def test_python_hash_seed_does_not_change_generation():
    script = f"""
import importlib.util, json, sys
sys.path.insert(0, {str(REPO / 'shared/runtime')!r})
spec=importlib.util.spec_from_file_location('g', {str(HOME / 'generator.py')!r})
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
print(json.dumps(g.generate(123456, 7, difficulty='hard'), separators=(',',':')))
"""
    outputs = []
    for hash_seed in ("0", "1", "123", "random"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        outputs.append(subprocess.check_output([sys.executable, "-B", "-c", script], text=True, env=env))
    assert len(set(outputs)) == 1


def test_real_racket_authority_matches_independent_oracle_on_canonicals_and_generated():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(31415, index, difficulty="hard") for index in range(8))
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]
