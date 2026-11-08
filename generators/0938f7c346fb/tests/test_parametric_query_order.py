"""Behavioral contract for the native query-operand-order family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "0938f7c346fb"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
SELF_AUDIT_PATH = PARAMETRIC / "self_audit.py"
OPS = ("intersection-eq", "xor", "left-minus", "conflict-merge")


def _load(name: str, path: Path):
    if not path.is_file():
        pytest.skip(f"source not implemented yet: {path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module




def test_native_parametric_sources_exist():
    missing = [path.relative_to(ROOT).as_posix() for path in (PROTOTYPE_PATH, ADAPTER_PATH, PROMOTION_PATH) if not path.is_file()]
    assert not missing, f"missing native parametric sources: {missing}"


@pytest.fixture(scope="module")
def prototype():
    return _load("test_0938_query_order_prototype", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("test_0938_query_order_adapter", ADAPTER_PATH)


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        programs = {
            row["program_solution"]
            for line in handle
            if (row := json.loads(line)).get("task_id") == TASK_ID
        }
    assert len(programs) == 1
    return next(iter(programs))


def _split(grid: list[list[int]]) -> list[list[list[int]]]:
    panel_width = (len(grid[0]) - 4) // 5
    return [
        [
            row[index * (panel_width + 1):index * (panel_width + 1) + panel_width]
            for row in grid
        ]
        for index in range(5)
    ]


def _apply(name: str, left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    output = [[0 for _ in row] for row in left]
    for r, row in enumerate(left):
        for c, x in enumerate(row):
            y = right[r][c]
            if name == "intersection-eq":
                output[r][c] = x if x != 0 and x == y else 0
            elif name == "xor":
                output[r][c] = x if x != 0 and y == 0 else y if x == 0 and y != 0 else 0
            elif name == "left-minus":
                output[r][c] = x if x != 0 and y == 0 else 0
            elif x == 0:
                output[r][c] = y
            elif y == 0 or x == y:
                output[r][c] = x
            else:
                output[r][c] = 9
    return output


def _infer(grid: list[list[int]]) -> tuple[str, list[list[list[int]]]]:
    panels = _split(grid)
    matches = tuple(name for name in OPS if _apply(name, panels[0], panels[1]) == panels[2])
    assert len(matches) == 1
    return matches[0], panels


def _all_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def test_programs_preserve_exact_canonical_default_and_add_one_real_alternative(prototype):
    canonical = _canonical_program()
    xy = prototype.program_for("xy")
    yx = prototype.program_for("yx")
    assert xy == canonical
    assert yx != canonical
    assert prototype.program_for("xy") == xy
    assert prototype.program_for("yx") == yx


def test_requested_demo_counts_and_four_distinct_queries_are_supported(prototype):
    for demos in range(2, 7):
        episode = prototype.generate_episode(41, "xy", demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = _all_inputs(episode)
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
        assert episode["program_solution"] == _canonical_program()


def test_same_seed_uses_matched_inputs_but_directional_demo_labels_identify_order(prototype):
    xy = prototype.generate_episode(1729, "xy", 3, 4)
    yx = prototype.generate_episode(1729, "yx", 3, 4)
    assert _all_inputs(xy) == _all_inputs(yx)

    operation, panels = _infer(xy["train"][0]["input"])
    assert operation == "left-minus"
    expected_xy = _apply("left-minus", panels[3], panels[4])
    expected_yx = _apply("left-minus", panels[4], panels[3])
    assert expected_xy != expected_yx
    assert xy["train"][0]["output"] == expected_xy
    assert yx["train"][0]["output"] == expected_yx
    assert xy["train"][0]["output"] != yx["train"][0]["output"]


def test_lessons_keep_multiple_inferred_operations_in_view(prototype):
    episode = prototype.generate_episode(7, "xy", 3, 4)
    demo_operations = [_infer(pair["input"])[0] for pair in episode["train"]]
    query_operations = [_infer(pair["input"])[0] for pair in episode["test"]]
    assert demo_operations[0] == "left-minus"
    assert len(set(demo_operations)) >= 2
    assert set(query_operations) == set(OPS)


def test_final_query_is_substantive_max_canvas_stress(prototype):
    for order in ("xy", "yx"):
        pair = prototype.generate_episode(5, order, 3, 4)["test"][-1]
        assert len(pair["input"]) == 30
        assert len(pair["input"][0]) == 29
        assert len(pair["output"]) == 30
        assert len(pair["output"][0]) == 5
        assert sum(value != 0 for row in pair["input"] for value in row) > 150
        assert sum(value != 0 for row in pair["output"] for value in row) > 10


def test_generation_is_deterministic_fresh_and_strictly_validated(prototype):
    first = prototype.generate_episode(99, "yx", 6, 4)
    second = prototype.generate_episode(99, "yx", 6, 4)
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
    assert first != second

    for bad_seed in (True, -1, 2**63):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(bad_seed, "xy", 3, 4)
    for bad_order in ("", "YX", 1, None):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(1, bad_order, 3, 4)
    for bad_demos in (True, 1, 7):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(1, "xy", bad_demos, 4)
    for bad_queries in (True, 1, 3, 5):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(1, "xy", 3, bad_queries)


def test_adapter_and_contract_expose_only_the_declared_setting(adapter):
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"query_operand_order": ["xy", "yx"]},
        "default": {"query_operand_order": "xy"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    settings = {"query_operand_order": "yx"}
    assert adapter.program(copy.deepcopy(settings)) != _canonical_program()
    episode = adapter.generate(13, copy.deepcopy(settings), 2, 4)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    for invalid in ({}, {"query_operand_order": "bad"}, {"query_operand_order": "xy", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(invalid)


def test_bounded_self_audit_refutes_declared_shortcuts_from_demos_only():
    assert SELF_AUDIT_PATH.is_file(), "bounded self-audit implementation is missing"
    audit = _load("test_0938_query_order_self_audit", SELF_AUDIT_PATH)
    report = audit.audit_family(seeds=(0, 17), demo_counts=(2, 3, 6), queries=4)
    assert report["schema"] == "arcpuzzles-query-order-self-audit-v1"
    assert report["status"] == "passed"
    assert report["limits"] == {
        "seeds": [0, 17],
        "demo_counts": [2, 3, 6],
        "queries": 4,
        "candidate_family": "declared order plus fixed-operation/copy/zero shortcuts",
    }
    assert len(report["cases"]) == 12
    for case in report["cases"]:
        selected = f"order:{case['settings']['query_operand_order']}"
        assert case["demo_survivors"] == [selected]
        assert case["ambiguous_query_rivals"] == []
        assert case["rival_count"] >= 11
        assert set(case["refutations"]) == set(case["rivals"]) - {selected}
        for row in case["refutations"].values():
            assert 0 <= row["first_failing_demo"] < case["demos"]
            assert row["reason"] == "label mismatch"


def test_self_audit_rejects_invalid_limits_and_is_deterministic():
    assert SELF_AUDIT_PATH.is_file(), "bounded self-audit implementation is missing"
    audit = _load("test_0938_query_order_self_audit_validation", SELF_AUDIT_PATH)
    first = audit.audit_family(seeds=(41,), demo_counts=(2,), queries=4)
    second = audit.audit_family(seeds=(41,), demo_counts=(2,), queries=4)
    assert first == second
    for seeds, demo_counts, queries in (((), (2,), 4), ((0,), (), 4), ((0,), (1,), 4), ((0,), (2,), 3)):
        with pytest.raises((TypeError, ValueError)):
            audit.audit_family(seeds=seeds, demo_counts=demo_counts, queries=queries)
