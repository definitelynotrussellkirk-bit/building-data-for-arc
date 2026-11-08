"""Task-local regression tests for ee602abaa45a."""
from copy import deepcopy
import ast
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    frames,
    load_generator,
    observed,
    racket_outputs,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=["train0", "train1", "train2", "train3", "test0"],
)
def test_canonical_inputs_are_lawful_and_oracle_matches(pair):
    assert reference_output(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_generation_restores_answer_bearing_selection(band):
    for index in range(32):
        grid = gen.generate(2000 + index, index, difficulty=band)
        parsed = frames(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert len(parsed) == 2
        assert {frame["selector"] for frame in parsed} == {1, 2}
        assert all(frame["candidates"][1] and frame["candidates"][2] for frame in parsed)
        expected = reference_output(grid)
        assert expected != reference_output(grid, selector_override=1)
        assert expected != reference_output(grid, selector_override=2)
        assert expected != reference_output(grid, ignore_transform=True)
        assert len(grid) in (14, 15)
        assert len(grid[0]) in (22, 23, 24)
        assert len({value for row in grid for value in row}) == 7


def test_exact_override_contract_is_pixel_observable():
    options = {
        "grid_h": 15,
        "grid_w": 24,
        "selector_first": 2,
        "transform_pair": "4-5",
        "layout_order": "right_first",
    }
    for band in (None, "easy", "medium", "hard"):
        grid = gen.generate(71, 9, difficulty=band, **options)
        assert gen.self_check(grid) == []
        assert observed(grid) == options
        assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 13),
        ("grid_h", True),
        ("grid_w", 25),
        ("selector_first", 0),
        ("selector_first", 1.0),
        ("transform_pair", "3-3"),
        ("transform_pair", 34),
        ("layout_order", "diagonal"),
    ],
)
def test_invalid_or_unknown_overrides_fail_closed(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_three_example_windows_refute_declared_rivals():
    rivals = gen.LESSON_COMPETITORS
    grids = [gen.generate(918, index, difficulty="hard") for index in range(20)]
    for start in range(len(grids) - gen.EXAMPLES_NEEDED + 1):
        demos = grids[start : start + gen.EXAMPLES_NEEDED]
        for name, rival in rivals.items():
            assert any(rival(grid) != reference_output(grid) for grid in demos), (
                start,
                name,
            )


def test_right_first_schedule_refutes_left_to_right_and_top_alignment_occurs():
    left_order_counterexamples = 0
    top_alignment_counterexamples = 0
    for index in range(32):
        grid = gen.generate(44, index)
        expected = reference_output(grid)
        left_order_counterexamples += expected != reference_output(grid, order="left_to_right")
        top_alignment_counterexamples += expected != reference_output(grid, alignment="top")
    assert left_order_counterexamples >= 8
    assert top_alignment_counterexamples >= 8


@pytest.mark.parametrize(
    "mutation",
    ["erase_border", "remove_candidate", "bad_selector", "bad_transform", "outside_noise"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(8, 0)
    parsed = frames(grid)
    r0, c0, r1, c1 = parsed[0]["bbox"]
    if mutation == "erase_border":
        grid[r0][c0] = 0
    elif mutation == "remove_candidate":
        for r, c in parsed[0]["candidates"][1]:
            grid[r][c] = 0
    elif mutation == "bad_selector":
        grid[r1 - 1][c0 + 1] = 6
    elif mutation == "bad_transform":
        grid[r1 - 1][c0 + 2] = 2
    elif mutation == "outside_noise":
        grid[-1][-1] = 3
    assert gen.self_check(grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 22 for _ in range(14)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_generation_is_deterministic_and_input_is_not_mutated_by_oracle():
    for index in range(64):
        grid = gen.generate(314, index, difficulty="medium")
        assert grid == gen.generate(314, index, difficulty="medium")
        before = deepcopy(grid)
        reference_output(grid)
        assert grid == before


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
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


def test_real_racket_authority_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(501, index) for index in range(24))
    assert racket_outputs(grids) == [reference_output(grid) for grid in grids]


def test_declared_witnesses_are_real_counterexamples():
    for index in range(24):
        grid = gen.generate(712, index)
        authoritative = reference_output(grid)
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            if witness(grid):
                for rival_name in gen.WITNESS_RIVALS[witness_name]:
                    assert gen.SEMANTIC_RIVALS[rival_name](grid) != authoritative


def test_axes_contract_is_ast_literal_for_portable_linting():
    source = Path(gen.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    parsed = ast.literal_eval(assignment.value)
    assert parsed == gen.AXES


def test_difficulty_bands_are_live_and_schedule_consistent():
    bands = ("easy", "medium", "hard")
    grids = [gen.generate(991, 7, difficulty=band) for band in bands]
    assert len({repr(grid) for grid in grids}) == len(bands)
    profiles = [gen.schedule_profile(991, 7, difficulty=band) for band in bands]
    assert len(set(profiles)) == len(bands)
