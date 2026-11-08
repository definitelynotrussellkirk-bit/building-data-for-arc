"""Focused tests for the proposed line-axis parametric prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import find_root  # noqa: E402


TASK_ID = "2a5919c40197"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def _load():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        f"parametric_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _line_counts(grid):
    uniform_rows = sum(len(set(row)) == 1 for row in grid)
    uniform_cols = sum(
        len({grid[r][c] for r in range(len(grid))}) == 1
        for c in range(len(grid[0]))
    )
    return uniform_rows, uniform_cols


def test_parameter_contract_is_strict_and_selected_once_per_episode():
    proto = _load()
    assert proto.PARAMETER_NAME == "line_axis"
    assert proto.PARAMETER_VALUES == ("row", "column")
    assert proto.DEFAULT_PARAMETER == "row"
    assert proto.choose_parameter(0) == "row"
    assert proto.choose_parameter(1) == "column"
    assert proto.choose_parameter(9, "row") == "row"

    for bad in (True, 1.0, "1"):
        with pytest.raises(TypeError):
            proto.choose_parameter(bad)
    with pytest.raises(ValueError):
        proto.choose_parameter(-1)
    for bad in (None, True, 0, "diagonal"):
        with pytest.raises((TypeError, ValueError)):
            proto.validate_parameter(bad)


def test_canonical_default_program_is_byte_exact_and_variant_is_bounded():
    proto = _load()
    canonical = proto.canonical_program(ROOT)
    row_program = proto.racket_program("row", root=ROOT)
    column_program = proto.racket_program("column", root=ROOT)
    assert row_program == canonical
    assert column_program != canonical
    assert column_program == canonical.replace(
        "(unique (row-at g r))", "(unique (col g c))", 1
    )
    assert proto.program_sha256(row_program) != proto.program_sha256(column_program)


def test_controlled_inputs_are_deterministic_lawful_and_axis_distinguishing():
    proto = _load()
    random.seed(3181)
    before = random.getstate()
    first = proto.build_input(17, 2)
    after = random.getstate()
    second = proto.build_input(17, 2)
    assert before == after
    assert first == second and first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert _line_counts(first) == (1, 1)
    assert proto.selected_generator_self_check(first, root=ROOT) == []
    assert proto.apply_rule(first, "row") != proto.apply_rule(first, "column")


def test_each_complete_episode_and_every_rotation_identifies_its_axis():
    proto = _load()
    for seed, expected in ((0, "row"), (1, "column")):
        episode = proto.generate_episode(seed, root=ROOT)
        assert episode["meta"]["line_axis"] == expected
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        pairs = episode["train"] + episode["test"]
        assert all(
            pair["output"] == proto.apply_rule(pair["input"], expected)
            for pair in pairs
        )
        rival = "column" if expected == "row" else "row"
        assert all(
            pair["output"] != proto.apply_rule(pair["input"], rival)
            for pair in pairs
        )
        for query_index in range(len(pairs)):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert proto.surviving_parameter_values(demos) == [expected]


def test_public_challenge_hides_hidden_axis_program_and_query_answers():
    proto = _load()
    episode = proto.generate_episode(1, root=ROOT)
    challenge = proto.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert challenge["train"] == episode["train"]
    assert len(challenge["test"]) == 1
    assert set(challenge["test"][0]) == {"input"}
    serialized = json.dumps(challenge, sort_keys=True)
    assert "line_axis" not in serialized
    assert "program" not in serialized
