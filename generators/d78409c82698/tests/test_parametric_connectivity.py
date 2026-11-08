from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "d78409c82698"
HERE = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = HERE / filename
    assert path.is_file(), f"missing parametric artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load("connectivity_parametric_prototype", "prototype.py")


def _canonical_program() -> str:
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_and_eight_neighbor_is_distinct(proto):
    assert proto.DEFAULT == {"connectivity": 4}
    assert proto.program(proto.DEFAULT) == _canonical_program()
    alternate = proto.program({"connectivity": 8})
    assert alternate != _canonical_program()
    assert alternate.strip().startswith("(rule!")


def test_controls_are_strict(proto):
    for bad in ({}, {"connectivity": 6}, {"connectivity": "4"}, {"connectivity": 4, "x": 1}):
        with pytest.raises(ValueError):
            proto.program(bad)
    for key, value in (
        ("seed", True), ("seed", -1), ("seed", 2**63),
        ("demos", 2), ("demos", 7), ("demos", 3.0),
        ("queries", 3), ("queries", 5), ("queries", True),
    ):
        kwargs = dict(seed=7, settings=proto.DEFAULT, demos=3, queries=4)
        kwargs[key] = value
        with pytest.raises((TypeError, ValueError)):
            proto.generate(**kwargs)


def test_inputs_are_setting_neutral_distinct_and_prefix_stable(proto):
    four = proto.generate(29, {"connectivity": 4}, 3, 4)
    eight = proto.generate(29, {"connectivity": 8}, 3, 4)
    assert _inputs(four) == _inputs(eight)
    assert all(a["output"] != b["output"] for a, b in zip(four["train"], eight["train"]))
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(four)}) == 7
    long = proto.generate(29, {"connectivity": 4}, 6, 4)
    assert four["train"] == long["train"][:3]
    assert four["test"] == long["test"]
    assert four == proto.generate(29, {"connectivity": 4}, 3, 4)


def test_minimum_lesson_identifies_connectivity_and_contains_all_semantic_roles(proto):
    for settings in proto.SETTING_OBJECTS:
        episode = proto.generate(31, settings, 3, 4)
        assert episode["certificate"]["fit_scope"] == "demonstrations_only"
        assert episode["certificate"]["survivors"] == [settings]
        assert episode["certificate"]["shortcut_survivors"] == []
        for pair in episode["train"]:
            analysis = proto.analyze(pair["input"])
            assert analysis["isolated_both"]
            assert analysis["diagonal_only_groups"]
            assert analysis["cardinal_components"]
            assert analysis["non_red_distractors"]
            assert pair["output"] == proto.apply_rule(pair["input"], settings)


def test_non_red_cells_are_preserved_under_both_rules(proto):
    episode = proto.generate(37, proto.DEFAULT, 3, 4)
    grid = episode["train"][0]["input"]
    for settings in proto.SETTING_OBJECTS:
        output = proto.apply_rule(grid, settings)
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value != 2:
                    assert output[r][c] == value


def test_four_queries_include_substantive_30x30_boundary_stress(proto):
    episode = proto.generate(43, {"connectivity": 8}, 3, 4)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    distractors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 2)]
    assert len(red) >= 55
    assert len(distractors) >= 25
    assert {0, 29} & {r for r, _ in red}
    assert {0, 29} & {c for _, c in red}
    analysis = proto.analyze(grid)
    assert len(analysis["diagonal_only_groups"]) >= 4
    assert len(analysis["cardinal_components"]) >= 4


def test_first_turn_projection_hides_private_fields_and_future_queries(proto):
    episode = proto.generate(59, {"connectivity": 8}, 3, 4)
    visible = {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    body = public_challenge_bytes(visible)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"connectivity": 4}
    changed["program_solution"] = "private change"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    changed_visible = {"train": changed["train"], "test": [{"input": changed["test"][0]["input"]}]}
    assert public_challenge_bytes(changed_visible) == body
    assert b"connectivity" not in body and b"program_solution" not in body


def test_adapter_and_promotion_contract(proto):
    adapter = _load("connectivity_parametric_adapter", "adapter.py")
    episode = adapter.generate(5, proto.DEFAULT, 6, 4)
    assert (len(episode["train"]), len(episode["test"])) == (6, 4)
    assert episode["program_solution"] == adapter.program(proto.DEFAULT)
    promotion = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["default"] == proto.DEFAULT
    assert promotion["parameters"] == {"connectivity": [4, 8]}
    assert promotion["limits"] == {"demos": [3, 6], "queries": [4, 4]}


def test_bounded_self_audit_is_replayable_and_covers_both_settings():
    audit = _load("connectivity_parametric_self_audit", "self_audit.py")
    receipt = audit.run(seeds=(0, 17), demo_counts=(3, 6))
    assert receipt["schema"] == "arcpuzzles-parametric-self-audit-v1"
    assert receipt["task_id"] == TASK
    assert receipt["passed"] is True
    assert receipt["jobs"] == 8
    assert {tuple(sorted(row["settings"].items())) for row in receipt["results"]} == {
        (("connectivity", 4),),
        (("connectivity", 8),),
    }
    assert all(row["query_count"] == 4 and row["certificate_ok"] for row in receipt["results"])
