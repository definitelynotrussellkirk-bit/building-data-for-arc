from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


TASK_ID = "677dcb71e2be"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load_adapter():
    path = HOME / "adapter.py"
    spec = importlib.util.spec_from_file_location("parametric_677dcb71e2be", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _exact_grid(value) -> bool:
    return (
        type(value) is list
        and 1 <= len(value) <= 30
        and type(value[0]) is list
        and 1 <= len(value[0]) <= 30
        and all(
            type(row) is list
            and len(row) == len(value[0])
            and all(type(cell) is int and 0 <= cell <= 9 for cell in row)
            for row in value
        )
    )


def test_default_program_is_byte_exact_and_alternate_is_distinct() -> None:
    adapter = _load_adapter()
    canonical = _canonical_program()
    assert adapter.program({"order_mode": "size_desc"}) == canonical
    assert adapter.program({"order_mode": "border_shift"}) != canonical


def test_adapter_supports_two_to_six_demos_and_four_query_bank() -> None:
    adapter = _load_adapter()
    for demos in (2, 3, 6):
        episode = adapter.generate(77, {"order_mode": "border_shift"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode == adapter.generate(77, {"order_mode": "border_shift"}, demos, 4)
        pairs = episode["train"] + episode["test"]
        assert len({json.dumps(pair["input"]) for pair in pairs}) == len(pairs)
        assert all(_exact_grid(pair["input"]) and _exact_grid(pair["output"]) for pair in pairs)
        assert any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30 for pair in episode["test"])


def test_settings_share_inputs_and_query_prefix_is_stable() -> None:
    adapter = _load_adapter()
    canonical = adapter.generate(91, {"order_mode": "size_desc"}, 3, 4)
    shifted = adapter.generate(91, {"order_mode": "border_shift"}, 3, 4)
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in shifted["train"] + shifted["test"]
    ]
    assert any(
        left["output"] != right["output"]
        for left, right in zip(canonical["train"], shifted["train"])
    )
    for query_count in range(1, 5):
        prefix = adapter.generate(91, {"order_mode": "border_shift"}, 3, query_count)
        assert prefix["test"] == shifted["test"][:query_count]


def test_four_query_bank_covers_all_nonzero_rotation_offsets() -> None:
    adapter = _load_adapter()
    episode = adapter.generate(23, {"order_mode": "border_shift"}, 2, 4)
    offsets = {adapter.scene_facts(pair["input"])["rotation_offset"] for pair in episode["test"]}
    assert offsets == {1, 2, 3}


def test_minimum_demos_cross_offset_at_fixed_nuisance_profile() -> None:
    adapter = _load_adapter()
    episode = adapter.generate(23, {"order_mode": "border_shift"}, 2, 1)
    grids = [pair["input"] for pair in episode["train"]]
    facts = [adapter.scene_facts(grid) for grid in grids]

    def border_side(grid, selector):
        r1, c1, r2, c2 = selector["bbox"]
        sides = []
        if r1 == 0:
            sides.append("top")
        if c1 == 0:
            sides.append("left")
        if r2 == len(grid) - 1:
            sides.append("bottom")
        if c2 == len(grid[0]) - 1:
            sides.append("right")
        return tuple(sides)

    selectors = [item["border_components"][0] for item in facts]
    assert {(len(grid), len(grid[0])) for grid in grids} == {(14, 15)}
    assert {item["component_count"] for item in facts} == {4}
    assert {border_side(grid, selector) for grid, selector in zip(grids, selectors)} == {("bottom",)}
    assert {item["rotation_offset"] for item in facts} == {1, 2}
    assert {selector["size"] for selector in selectors} == {5, 6}
    assert {
        tuple(sorted(comp["size"] for comp in item["components"] if comp is not selector))
        for item, selector in zip(facts, selectors)
    } == {(2, 7, 9)}


def test_every_scene_has_one_noncollapsing_border_selector() -> None:
    adapter = _load_adapter()
    offsets = set()
    for seed in range(8):
        episode = adapter.generate(seed, {"order_mode": "border_shift"}, 2, 4)
        for pair in episode["train"] + episode["test"]:
            facts = adapter.scene_facts(pair["input"])
            assert len(facts["border_components"]) == 1
            assert 0 < facts["rotation_offset"] < facts["component_count"]
            offsets.add(facts["rotation_offset"])
            assert pair["output"] == adapter.output_for(pair["input"], "border_shift")
    assert len(offsets) >= 2


def test_two_demo_minimum_kills_declared_shortcuts() -> None:
    adapter = _load_adapter()
    for seed in range(16):
        for mode in ("size_desc", "border_shift"):
            episode = adapter.generate(seed, {"order_mode": mode}, 2, 4)
            assert adapter.lesson_identifiable(episode["train"], episode["test"]) == []


def test_bad_settings_counts_and_scalar_types_reject() -> None:
    adapter = _load_adapter()
    bad_settings = ({}, {"order_mode": "unknown"}, {"order_mode": True}, {"extra": "size_desc"})
    for settings in bad_settings:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
    for args in (
        (True, {"order_mode": "size_desc"}, 2, 4),
        (0, {"order_mode": "size_desc"}, True, 4),
        (0, {"order_mode": "size_desc"}, 2, True),
        (0, {"order_mode": "size_desc"}, 1, 4),
        (0, {"order_mode": "size_desc"}, 7, 4),
        (0, {"order_mode": "size_desc"}, 2, 0),
        (0, {"order_mode": "size_desc"}, 2, 5),
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(*args)
