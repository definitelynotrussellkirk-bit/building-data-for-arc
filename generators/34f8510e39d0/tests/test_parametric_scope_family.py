"""Native parametric scope-family tests for 34f8510e39d0."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK_ID = "34f8510e39d0"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load_parametric(name: str):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing parametric source: {path}"
    module_name = f"_{TASK_ID}_{name}_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK_ID)
    programs = {
        item["program_solution"]
        for item in catalog._variants()[row.get("rule_task_id", TASK_ID)]
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_default_program_is_exact_canonical_and_contract_is_bounded() -> None:
    adapter = load_parametric("adapter")
    contract_path = PARAMETRIC / "promotion.json"
    assert contract_path.is_file()
    contract = json.loads(contract_path.read_text())
    assert adapter.program({"scope": "all_green"}) == canonical_program()
    assert contract["parameters"] == {"scope": ["all_green", "largest_only"]}
    assert contract["default"] == {"scope": "all_green"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_matched_inputs_have_input_dependent_selection_and_30x30(seed: int) -> None:
    adapter = load_parametric("adapter")
    family = load_parametric("family")
    episodes = {
        scope: adapter.generate(seed, {"scope": scope}, 6, 4)
        for scope in ("all_green", "largest_only")
    }
    all_inputs = {
        scope: [pair["input"] for pair in episode["train"] + episode["test"]]
        for scope, episode in episodes.items()
    }
    assert all_inputs["all_green"] == all_inputs["largest_only"]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs["all_green"]}) == 10
    for grid in all_inputs["all_green"]:
        info = family.intermediate(grid)
        areas = [obj["area"] for obj in info["green_rectangles"]]
        assert len(areas) >= 2
        assert areas.count(max(areas)) == 1
        assert info["size_matched_distractor"] is True
        assert family.solve(grid, "all_green") != family.solve(grid, "largest_only")
    stress = episodes["all_green"]["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(value != 0 for row in stress for value in row) >= 220
    assert episodes["all_green"]["private_query_bank"] == episodes["all_green"]["test"]


def test_every_supported_prefix_identifies_scope_and_refutes_rivals() -> None:
    adapter = load_parametric("adapter")
    family = load_parametric("family")
    for seed in range(16):
        for demos in range(2, 7):
            for scope in ("all_green", "largest_only"):
                episode = adapter.generate(seed, {"scope": scope}, demos, 4)
                opposite = adapter.generate(
                    seed,
                    {"scope": "largest_only" if scope == "all_green" else "all_green"},
                    demos,
                    4,
                )
                assert [p["input"] for p in episode["train"]] == [p["input"] for p in opposite["train"]]
                assert all(a["output"] != b["output"] for a, b in zip(episode["train"], opposite["train"]))
                survivors = set(family.RIVALS)
                for pair in episode["train"]:
                    survivors = {
                        rival
                        for rival in survivors
                        if family.solve_rival(pair["input"], scope, rival) == pair["output"]
                    }
                assert not survivors, (seed, demos, scope, survivors)


def test_claimed_labels_match_solver_and_smallest_counterfactual_changes() -> None:
    adapter = load_parametric("adapter")
    family = load_parametric("family")
    episode = adapter.generate(29, {"scope": "largest_only"}, 3, 4)
    for pair in episode["train"] + episode["test"]:
        assert family.solve(pair["input"], "largest_only") == pair["output"]
        assert family.solve_smallest_only(pair["input"]) != pair["output"]


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"scope": "x"}, {"scope": True}, {"scope": "all_green", "x": 1}],
)
def test_invalid_settings_are_rejected(settings: object) -> None:
    with pytest.raises(ValueError):
        load_parametric("adapter").program(settings)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("seed", True),
        ("seed", -1),
        ("demos", 1),
        ("demos", 7),
        ("queries", 0),
        ("queries", 5),
        ("queries", 2.0),
    ],
)
def test_invalid_counts_are_rejected(field: str, bad: object) -> None:
    kwargs = {
        "seed": 0,
        "settings": {"scope": "all_green"},
        "demos": 3,
        "queries": 4,
    }
    kwargs[field] = bad
    with pytest.raises(ValueError):
        load_parametric("adapter").generate(**kwargs)
