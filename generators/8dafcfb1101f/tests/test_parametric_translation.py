from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "8dafcfb1101f"
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
    return _load("translation_parametric_prototype", "prototype.py")


def _canonical_program() -> str:
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _vector(grid):
    src = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1)
    dst = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
    return dst[0] - src[0], dst[1] - src[1]


def test_default_program_is_exact_canonical_and_reverse_is_distinct(proto):
    assert proto.DEFAULT == {"vector_direction": "src_to_dst"}
    assert proto.program(proto.DEFAULT) == _canonical_program()
    reverse = proto.program({"vector_direction": "dst_to_src"})
    assert reverse != _canonical_program()
    assert reverse.strip().startswith("(rule!")


def test_controls_are_strict(proto):
    for bad in ({}, {"vector_direction": "absolute"}, {"vector_direction": 1}, {"vector_direction": "src_to_dst", "x": 1}):
        with pytest.raises(ValueError):
            proto.program(bad)
    good = proto.DEFAULT
    for key, value in (
        ("seed", True), ("seed", -1), ("seed", 2**63),
        ("demos", 2), ("demos", 7), ("demos", 3.0),
        ("queries", 3), ("queries", 5), ("queries", True),
    ):
        kwargs = dict(seed=7, settings=good, demos=3, queries=4)
        kwargs[key] = value
        with pytest.raises((TypeError, ValueError)):
            proto.generate(**kwargs)


def test_inputs_are_setting_neutral_distinct_and_prefix_stable(proto):
    forward = proto.generate(41, proto.DEFAULT, 3, 4)
    reverse = proto.generate(41, {"vector_direction": "dst_to_src"}, 3, 4)
    assert _inputs(forward) == _inputs(reverse)
    assert all(a["output"] != b["output"] for a, b in zip(forward["train"], reverse["train"]))
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(forward)}) == 7

    short = proto.generate(41, proto.DEFAULT, 3, 4)
    long = proto.generate(41, proto.DEFAULT, 6, 4)
    assert short["train"] == long["train"][:3]
    assert short["test"] == long["test"]
    assert short == proto.generate(41, proto.DEFAULT, 3, 4)


def test_minimum_lesson_identifies_each_setting_and_signed_vector_semantics(proto):
    for settings in proto.SETTING_OBJECTS:
        episode = proto.generate(19, settings, 3, 4)
        assert episode["certificate"]["fit_scope"] == "demonstrations_only"
        assert episode["certificate"]["survivors"] == [settings]
        assert episode["certificate"]["shortcut_survivors"] == []
        signs = {
            (-1 if dr < 0 else 1, -1 if dc < 0 else 1)
            for dr, dc in (_vector(pair["input"]) for pair in episode["train"])
        }
        assert len(signs) == 3
        assert any(sr < 0 for sr, _ in signs)
        assert any(sc < 0 for _, sc in signs)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == proto.apply_rule(pair["input"], settings)


def test_four_queries_include_substantive_30x30_boundary_stress(proto):
    episode = proto.generate(73, proto.DEFAULT, 3, 4)
    large = episode["test"][-1]
    grid, output = large["input"], large["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    payload = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1, 2)]
    painted = [(r, c) for r, row in enumerate(output) for c, v in enumerate(row) if v]
    assert len(payload) >= 80
    assert len({grid[r][c] for r, c in payload}) >= 5
    assert {0, 29} & {r for r, _ in painted}
    assert {0, 29} & {c for _, c in painted}


def test_first_turn_projection_hides_private_fields_and_future_queries(proto):
    episode = proto.generate(101, {"vector_direction": "dst_to_src"}, 3, 4)
    visible = {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    body = public_challenge_bytes(visible)
    changed = copy.deepcopy(episode)
    changed["settings"] = proto.DEFAULT
    changed["program_solution"] = "private change"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    changed_visible = {"train": changed["train"], "test": [{"input": changed["test"][0]["input"]}]}
    assert public_challenge_bytes(changed_visible) == body
    assert b"vector_direction" not in body and b"program_solution" not in body


def test_adapter_and_promotion_contract(proto):
    adapter = _load("translation_parametric_adapter", "adapter.py")
    episode = adapter.generate(5, proto.DEFAULT, 6, 4)
    assert (len(episode["train"]), len(episode["test"])) == (6, 4)
    assert episode["program_solution"] == adapter.program(proto.DEFAULT)
    promotion = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["default"] == proto.DEFAULT
    assert promotion["parameters"] == {"vector_direction": ["src_to_dst", "dst_to_src"]}
    assert promotion["limits"] == {"demos": [3, 6], "queries": [4, 4]}


def test_bounded_self_audit_is_replayable_and_covers_both_settings():
    audit = _load("translation_parametric_self_audit", "self_audit.py")
    receipt = audit.run(seeds=(0, 17), demo_counts=(3, 6))
    assert receipt["schema"] == "arcpuzzles-parametric-self-audit-v1"
    assert receipt["task_id"] == TASK
    assert receipt["passed"] is True
    assert receipt["jobs"] == 8
    assert {tuple(sorted(row["settings"].items())) for row in receipt["results"]} == {
        (("vector_direction", "src_to_dst"),),
        (("vector_direction", "dst_to_src"),),
    }
    assert all(row["query_count"] == 4 and row["certificate_ok"] for row in receipt["results"])
