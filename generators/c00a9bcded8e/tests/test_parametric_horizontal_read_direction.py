"""Contract tests for the proposed horizontal read-direction prototype."""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "c00a9bcded8e"
ROOT = find_root(__file__)
GENERATOR, SELECTED_SOURCE, _SOURCE_SHA256 = load_selected_generator(
    TASK_ID,
    root=ROOT,
)
MANIFEST = ROOT / "RUNTIME_MANIFEST.json"
if MANIFEST.is_file():
    identity = f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    entries = [
        row
        for row in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
        if row.get("library_path") == identity
    ]
    entries.sort(key=lambda row: row.get("runtime_path") == identity)
    assert entries, "portable runtime must retain the parametric prototype"
    PROTOTYPE_PATH = ROOT / entries[0]["runtime_path"]
else:
    PROTOTYPE_PATH = SELECTED_SOURCE.parent / "workspace/parametric/prototype.py"


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "horizontal read-direction prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "c00a9bcded8e_horizontal_read_direction_prototype",
        PROTOTYPE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    matches = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    assert len(matches) == 1
    return matches[0]


def test_parameter_contract_and_canonical_default_are_exact():
    p = prototype()
    assert p.PARAMETER_NAME == "horizontal_read_direction"
    assert p.SETTINGS == ("left_to_right", "right_to_left")
    assert p.DEFAULT_SETTING == "left_to_right"
    assert p.instantiate_rule("left_to_right") == canonical_program()
    alternative = p.instantiate_rule("right_to_left")
    assert alternative != canonical_program()
    assert alternative.count("(reverse (sort-by cur-row second))") == 2
    assert {p.choose_setting(seed) for seed in range(8)} == set(p.SETTINGS)
    with pytest.raises((TypeError, ValueError)):
        p.choose_setting(True)


@pytest.mark.parametrize("setting", ["left_to_right", "right_to_left"])
def test_complete_episode_pins_one_setting_and_every_demo_refutes_the_other(setting):
    p = prototype()
    episode = p.build_episode(20261023, horizontal_read_direction=setting)
    assert episode["parameter"] == {p.PARAMETER_NAME: setting}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert p.episode_errors(episode) == []

    other = next(value for value in p.SETTINGS if value != setting)
    for pair in episode["train"]:
        grid = pair["input"]
        assert GENERATOR.self_check(grid) == []
        assert pair["output"] == p.solve_python(grid, horizontal_read_direction=setting)
        assert pair["output"] != p.solve_python(
            grid,
            horizontal_read_direction=other,
        )
        assert p.solve_python(
            grid,
            horizontal_read_direction="left_to_right",
        ) == GENERATOR.rule_mirror(grid)


def test_same_inputs_are_used_for_both_complete_setting_episodes():
    p = prototype()
    left = p.build_episode(91, horizontal_read_direction="left_to_right")
    right = p.build_episode(91, horizontal_read_direction="right_to_left")
    left_pairs = left["train"] + left["test"]
    right_pairs = right["train"] + right["test"]
    assert [pair["input"] for pair in left_pairs] == [pair["input"] for pair in right_pairs]
    for left_pair, right_pair in zip(left_pairs, right_pairs):
        assert right_pair["output"] == [row[::-1] for row in left_pair["output"]]
        assert right_pair["output"] != left_pair["output"]


def test_public_challenge_hides_parameter_program_and_query_answers():
    p = prototype()
    public = p.public_challenge(
        p.build_episode(5, horizontal_read_direction="right_to_left")
    )
    assert set(public) == {"schema", "train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    assert "horizontal_read_direction" not in serialized
    assert "right_to_left" not in serialized
    assert "program" not in serialized



def test_racket_expression_builder_is_source_tree_portable():
    p = prototype()
    expression = p._rule_application(p.instantiate_rule("left_to_right"), [[1]])
    assert expression.startswith("((lambda (g)")
    assert expression.endswith(" '((1)))")

def test_invalid_settings_are_rejected_without_coercion():
    p = prototype()
    for value in (None, False, True, 0, "rtl", "left-to-right"):
        with pytest.raises((TypeError, ValueError)):
            p.instantiate_rule(value)
