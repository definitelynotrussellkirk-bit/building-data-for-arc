"""Focused contract tests for the interior-mask parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root
from arcpuzzles import Catalog

TASK_ID = "3a6ce35e3549"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load(name: str):
    path = PARAMETRIC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    row = Catalog(ROOT).describe(TASK_ID)
    programs = {
        item["program_solution"]
        for item in Catalog(ROOT)._variants()[row.get("rule_task_id", TASK_ID)]
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_default_program_is_exact_canonical_and_contract_is_bounded() -> None:
    adapter = load("adapter")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert adapter.program({"mask": "blob"}) == canonical_program()
    assert contract["parameters"] == {"mask": ["blob", "gaps"]}
    assert contract["default"] == {"mask": "blob"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_matched_inputs_counts_distinctness_and_30x30_stress(seed: int) -> None:
    adapter = load("adapter")
    episodes = {
        mask: adapter.generate(seed, {"mask": mask}, 6, 4)
        for mask in ("blob", "gaps")
    }
    blob_inputs = [p["input"] for p in episodes["blob"]["train"] + episodes["blob"]["test"]]
    gap_inputs = [p["input"] for p in episodes["gaps"]["train"] + episodes["gaps"]["test"]]
    assert blob_inputs == gap_inputs
    assert len({json.dumps(g, separators=(",", ":")) for g in blob_inputs}) == 10
    stress = episodes["blob"]["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(v != 0 for row in stress for v in row) >= 200
    assert episodes["blob"]["test"][-1]["output"] != episodes["gaps"]["test"][-1]["output"]


def test_every_supported_prefix_identifies_the_setting() -> None:
    adapter = load("adapter")
    for seed in range(12):
        for demos in range(2, 7):
            blob = adapter.generate(seed, {"mask": "blob"}, demos, 4)
            gaps = adapter.generate(seed, {"mask": "gaps"}, demos, 4)
            assert [p["input"] for p in blob["train"]] == [p["input"] for p in gaps["train"]]
            assert all(a["output"] != b["output"] for a, b in zip(blob["train"], gaps["train"]))
            assert all(a["output"] != b["output"] for a, b in zip(blob["test"], gaps["test"]))


def test_python_solver_matches_claimed_labels_and_uses_marker_bounds() -> None:
    family = load("family")
    adapter = load("adapter")
    episode = adapter.generate(29, {"mask": "gaps"}, 3, 4)
    for pair in episode["train"] + episode["test"]:
        assert family.solve(pair["input"], "gaps") == pair["output"]
        info = family.intermediate(pair["input"])
        assert info["dot_count"] == 4
        assert info["big_count"] > info["dot_count"]
        assert info["interior_height"] == len(pair["output"])
        assert info["interior_width"] == len(pair["output"][0])


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"mask": "x"}, {"mask": True}, {"mask": "blob", "extra": 1}],
)
def test_invalid_settings_are_rejected(settings: object) -> None:
    with pytest.raises(ValueError):
        load("adapter").program(settings)


@pytest.mark.parametrize(
    "field,bad",
    [("seed", True), ("seed", -1), ("demos", 1), ("demos", 7),
     ("queries", 0), ("queries", 5), ("queries", 2.0)],
)
def test_invalid_counts_and_seed_are_rejected(field: str, bad: object) -> None:
    kwargs = {"seed": 0, "settings": {"mask": "blob"}, "demos": 3, "queries": 4}
    kwargs[field] = bad
    with pytest.raises(ValueError):
        load("adapter").generate(**kwargs)


def test_wrong_bounds_counterfactual_changes_a_stress_label() -> None:
    family = load("family")
    adapter = load("adapter")
    pair = adapter.generate(17, {"mask": "gaps"}, 3, 4)["test"][-1]
    assert family.solve(pair["input"], "gaps") == pair["output"]
    assert family.solve_wrong_shifted_bounds(pair["input"], "gaps") != pair["output"]


def test_bounded_semantic_rivals_are_refuted_by_two_demos() -> None:
    family = load("family")
    adapter = load("adapter")
    for seed in range(16):
        for mask in ("blob", "gaps"):
            episode = adapter.generate(seed, {"mask": mask}, 2, 4)
            survivors = set(family.RIVALS)
            for pair in episode["train"]:
                survivors = {
                    rival for rival in survivors
                    if family.solve_rival(pair["input"], mask, rival) == pair["output"]
                }
            assert not survivors, (seed, mask, survivors)
