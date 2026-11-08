"""Native parametric contract tests for the diamond-center relay family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "ee5295e1813b"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAM = HOME / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAM / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task row not found")


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_contract_and_default_program_are_exact():
    adapter = _load("relay_adapter_contract", "adapter.py")
    contract = json.loads((PARAM / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"composition": ["fill_centers", "connect_equal_centers"]},
        "default": {"composition": "fill_centers"},
        "qualification_demos": 2,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/connect-equal-centers.rkt",
            f"generators/{TASK_ID}/workspace/parametric/wrong-intermediate.rkt",
        ],
    }
    assert adapter.program({"composition": "fill_centers"}) == _canonical_program()
    assert adapter.program({"composition": "connect_equal_centers"}) != _canonical_program()


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_counts_setting_independent_inputs_and_real_divergence(demos: int, queries: int):
    adapter = _load(f"relay_adapter_{demos}_{queries}", "adapter.py")
    family = _load(f"relay_family_{demos}_{queries}", "family.py")
    plain = adapter.generate(161803, {"composition": "fill_centers"}, demos, queries)
    connected = adapter.generate(
        161803, {"composition": "connect_equal_centers"}, demos, queries
    )
    assert len(plain["train"]) == len(connected["train"]) == demos
    assert len(plain["test"]) == len(connected["test"]) == queries
    assert _inputs(plain) == _inputs(connected)
    assert len({json.dumps(grid) for grid in _inputs(plain)}) == demos + queries
    for split in ("train", "test"):
        for plain_pair, connected_pair in zip(plain[split], connected[split]):
            grid = plain_pair["input"]
            assert plain_pair["output"] == family.transform(grid, "fill_centers")
            assert connected_pair["output"] == family.transform(
                grid, "connect_equal_centers"
            )
            assert plain_pair["output"] != connected_pair["output"]


def test_streams_are_prefix_stable_and_fourth_query_is_substantive_30x30():
    adapter = _load("relay_adapter_prefix", "adapter.py")
    short = adapter.generate(57721, {"composition": "connect_equal_centers"}, 2, 1)
    long = adapter.generate(57721, {"composition": "connect_equal_centers"}, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    large = long["test"][3]["input"]
    assert (len(large), len(large[0])) == (30, 30)
    assert sum(cell != 0 for row in large for cell in row) >= 70


def test_derived_centers_are_causally_used_as_connection_anchors():
    family = _load("relay_family_causal", "family.py")
    grid = family.build_input(123, "test", 3)
    anchors = family.center_intermediate(grid)
    assert len(anchors) >= 4
    assert any(
        a[2] == b[2] and (a[0] == b[0] or a[1] == b[1])
        for index, a in enumerate(anchors)
        for b in anchors[index + 1 :]
    )
    correct = family.transform(grid, "connect_equal_centers")
    wrong = family.transform_wrong_intermediate(grid)
    assert correct != family.transform(grid, "fill_centers")
    assert correct != wrong


@pytest.mark.parametrize(
    "settings,demos,queries,error",
    [
        ({}, 2, 1, ValueError),
        ({"composition": "invented"}, 2, 1, ValueError),
        ({"composition": "fill_centers", "extra": 1}, 2, 1, ValueError),
        ({"composition": "fill_centers"}, True, 1, TypeError),
        ({"composition": "fill_centers"}, 1, 1, ValueError),
        ({"composition": "fill_centers"}, 2, 5, ValueError),
    ],
)
def test_invalid_contract_inputs_fail_loudly(settings, demos, queries, error):
    adapter = _load("relay_adapter_invalid", "adapter.py")
    with pytest.raises(error):
        adapter.generate(1, settings, demos, queries)


def test_preflight_compat_normalizes_single_query_canonical_record():
    compat = _load("relay_preflight_compat", "preflight_compat.py")
    pair = {"input": [[0]], "output": [[0]]}
    assert compat.normalized_pairs({"test": pair}, "test") == [pair]
    assert compat.normalized_pairs({"train": [pair]}, "train") == [pair]


def test_racket_wrong_intermediate_preserves_step_a_center_fills():
    family = _load("relay_family_racket_counterfactual", "family.py")
    grid = family.build_input(123, "test", 0)
    anchors = family.center_intermediate(grid)
    program = (PARAM / "wrong-intermediate.rkt").read_text(encoding="utf-8")

    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        actual = bridge.eval_text(f"({wrap_rule(program)} {literal})")

    assert all(actual[row][column] == color for row, column, color in anchors)
    assert actual != family.transform(grid, "connect_equal_centers")
