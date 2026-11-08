"""Native parametric contract regressions for 2e0d26e28a50."""
from __future__ import annotations

import importlib.util
import json

import pytest

from reviewer_support import canonical_path, find_root

TASK = "2e0d26e28a50"
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
    grid = [[0] * 13 for _ in range(11)]
    for r, c in [(2, 2), (2, 3), (3, 2), (4, 2), (4, 3)]:
        grid[r][c] = 2
    grid[7][8] = 1
    for r, c in [(1, 9), (1, 10)]:
        grid[r][c] = 3  # two cells -> top-right corner
    grid[9][1] = 6
    grid[9][2] = 6
    return grid


def test_contract_and_default_program_are_exact():
    adapter = _load("_test_2e_adapter", "adapter.py")
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {
        "anchor_policy": ["bottom_right", "key_count_corner"]
    }
    assert contract["default"] == {"anchor_policy": "bottom_right"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert contract["qualification_demos"] == 3
    assert adapter.program(contract["default"]) == _canonical_program()
    assert adapter.program({"anchor_policy": "key_count_corner"}) != _canonical_program()


def test_literal_key_count_selects_corner_consumed_by_stamp():
    family = _load("_test_2e_family", "family.py")
    source = _literal_input()
    canonical = family.apply_policy(source, "bottom_right")
    selected = family.apply_policy(source, "key_count_corner")
    info = family.analyze(source)
    assert info["key_count"] == 2
    assert info["selected_corner"] == "top_right"
    assert canonical != selected
    assert sum(cell == 8 for row in canonical for cell in row) == info["motif_size"]
    assert sum(cell == 8 for row in selected for cell in row) == info["motif_size"]


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("policy", ["bottom_right", "key_count_corner"])
def test_supported_counts_return_exactly_four_distinct_queries(demos, policy):
    adapter = _load("_test_2e_adapter_counts", "adapter.py")
    episode = adapter.generate(400 + demos, {"anchor_policy": policy}, demos, 4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    grids = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid) for grid in grids}) == demos + 4
    assert all(len(grid) <= 30 and len(grid[0]) <= 30 for grid in grids)


def test_settings_share_inputs_and_minimum_demos_distinguish_them():
    adapter = _load("_test_2e_adapter_matched", "adapter.py")
    canonical = adapter.generate(17, {"anchor_policy": "bottom_right"}, 2, 4)
    selected = adapter.generate(17, {"anchor_policy": "key_count_corner"}, 2, 4)
    for split in ("train", "test"):
        assert [p["input"] for p in canonical[split]] == [p["input"] for p in selected[split]]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(canonical["train"], selected["train"])
    )


def test_schedule_covers_all_corners_and_substantive_30_by_30_stress():
    adapter = _load("_test_2e_adapter_stress", "adapter.py")
    episode = adapter.generate(0, {"anchor_policy": "key_count_corner"}, 6, 4)
    family = _load("_test_2e_family_stress", "family.py")
    grids = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    infos = [family.analyze(grid) for grid in grids]
    assert {info["selected_corner"] for info in infos} == {
        "top_left", "top_right", "bottom_left", "bottom_right"
    }
    stress = next(grid for grid in grids if (len(grid), len(grid[0])) == (30, 30))
    stress_info = family.analyze(stress)
    assert stress_info["motif_size"] >= 12
    assert stress_info["distractor_cells"] >= 20
    assert sum(cell != 0 for row in stress for cell in row) >= 35


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({"anchor_policy": "bad"}, 3, 4),
        ({"anchor_policy": "bottom_right", "extra": 1}, 3, 4),
        ({"anchor_policy": "bottom_right"}, 1, 4),
        ({"anchor_policy": "bottom_right"}, 7, 4),
        ({"anchor_policy": "bottom_right"}, 3, 3),
        ({"anchor_policy": "bottom_right"}, 3, 5),
    ],
)
def test_invalid_contract_requests_fail_loudly(settings, demos, queries):
    adapter = _load("_test_2e_adapter_invalid", "adapter.py")
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(1, settings, demos, queries)
