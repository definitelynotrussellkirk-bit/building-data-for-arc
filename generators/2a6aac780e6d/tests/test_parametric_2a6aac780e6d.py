"""Native parametric contract regressions for 2a6aac780e6d."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK = "2a6aac780e6d"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK}
    assert len(programs) == 1
    return next(iter(programs))


def _literal_input() -> list[list[int]]:
    # The selector is three positions right of the left key endpoint, so the
    # third qualifying payload row is selected in the alternate setting.
    return [
        [8, 0, 0, 5, 0, 0, 8, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0],
        [0, 0, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 6, 0, 0, 0, 0, 6, 0, 0, 0],
        [0, 7, 0, 9, 0, 7, 0, 0, 0, 0, 0, 0],
        [0, 0, 4, 0, 0, 0, 0, 0, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    ]


def test_contract_and_default_program_are_exact():
    adapter = _load("_test_2a_adapter", "adapter.py")
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {
        "fill_scope": ["all_qualifying", "key_selected"]
    }
    assert contract["default"] == {"fill_scope": "all_qualifying"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert contract["qualification_demos"] == 3
    assert adapter.program(contract["default"]) == _canonical_program()
    assert adapter.program({"fill_scope": "key_selected"}) != _canonical_program()


def test_literal_key_selected_dependency_changes_only_selected_payload():
    family = _load("_test_2a_family", "family.py")
    source = _literal_input()
    canonical = family.apply_scope(source, "all_qualifying")
    selected = family.apply_scope(source, "key_selected")
    analysis = family.analyze(source)
    assert analysis["selector_rank"] == 3
    assert analysis["selected_row"] == analysis["payload_rows"][2]
    assert canonical != selected
    changed_canonical = {
        r for r, (before, after) in enumerate(zip(source, canonical)) if before != after
    }
    changed_selected = {
        r for r, (before, after) in enumerate(zip(source, selected)) if before != after
    }
    assert changed_canonical == set(analysis["payload_rows"])
    assert changed_selected == {analysis["selected_row"]}


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("scope", ["all_qualifying", "key_selected"])
def test_supported_counts_return_exactly_four_distinct_queries(demos, scope):
    adapter = _load("_test_2a_adapter_counts", "adapter.py")
    episode = adapter.generate(700 + demos, {"fill_scope": scope}, demos, 4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    grids = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid) for grid in grids}) == demos + 4
    assert all(len(grid) <= 30 and len(grid[0]) <= 30 for grid in grids)


def test_settings_share_inputs_and_every_visible_demo_distinguishes_them():
    adapter = _load("_test_2a_adapter_matched", "adapter.py")
    all_rows = adapter.generate(17, {"fill_scope": "all_qualifying"}, 3, 4)
    selected = adapter.generate(17, {"fill_scope": "key_selected"}, 3, 4)
    for split in ("train", "test"):
        assert [p["input"] for p in all_rows[split]] == [p["input"] for p in selected[split]]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(all_rows["train"], selected["train"])
    )


def test_schedule_includes_substantive_30_by_30_stress_and_varied_selector_results():
    adapter = _load("_test_2a_adapter_stress", "adapter.py")
    episode = adapter.generate(0, {"fill_scope": "key_selected"}, 6, 4)
    grids = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    stress = next(grid for grid in grids if (len(grid), len(grid[0])) == (30, 30))
    family = _load("_test_2a_family_stress", "family.py")
    info = family.analyze(stress)
    assert len(info["payload_rows"]) >= 8
    assert info["guard_count"] >= 4
    assert sum(cell != 0 for row in stress for cell in row) >= 25
    selected_rows = {family.analyze(grid)["selected_row"] for grid in grids}
    selector_ranks = {family.analyze(grid)["selector_rank"] for grid in grids}
    assert len(selected_rows) >= 4
    assert len(selector_ranks) >= 3


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({"fill_scope": "bad"}, 3, 4),
        ({"fill_scope": "all_qualifying", "extra": 1}, 3, 4),
        ({"fill_scope": "all_qualifying"}, 1, 4),
        ({"fill_scope": "all_qualifying"}, 7, 4),
        ({"fill_scope": "all_qualifying"}, 3, 3),
        ({"fill_scope": "all_qualifying"}, 3, 5),
    ],
)
def test_invalid_contract_requests_fail_loudly(settings, demos, queries):
    adapter = _load("_test_2a_adapter_invalid", "adapter.py")
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(1, settings, demos, queries)
