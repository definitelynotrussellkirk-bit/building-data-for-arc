"""Base repair and native parametric tests for 37ef814e99dd."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator

TASK_ID = "37ef814e99dd"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load_parametric(name: str):
    path = PARAMETRIC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def generator():
    module, _path, _sha = load_selected_generator(TASK_ID, root=ROOT)
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


def test_base_generator_covers_nonrectangular_boundary_semantics() -> None:
    gen = generator()
    profiles = set()
    nonrectangular = 0
    for difficulty in (None, "medium", "hard"):
        for index in range(24):
            grid = gen.generate(37_000 + index, index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            info = gen.analyze_scene(grid)
            profiles.add(info["scene_profile"])
            nonrectangular += sum(not obj["solid_bbox"] for obj in info["objects"])
            assert gen.rule_mirror(grid) != grid
    assert {"rectangles", "notched", "mixed"} <= profiles
    assert nonrectangular > 0


def test_base_validator_rejects_old_degenerate_domains() -> None:
    gen = generator()
    for texture in ("no_blobs", "all_2x2", "already_outline"):
        grid = gen.generate(0, 0, texture=texture)
        assert gen.self_check(grid), texture


def test_bbox_perimeter_shortcut_is_broken_by_production() -> None:
    gen = generator()
    witnesses = []
    for index in range(64):
        grid = gen.generate(90_000 + index, index, scene_profile="notched")
        if gen.rule_mirror(grid) != gen.bbox_outline_rival(grid):
            witnesses.append(grid)
    assert witnesses


def test_default_program_exact_and_contract_bounded() -> None:
    adapter = load_parametric("adapter")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert adapter.program({"scope": "all_objects"}) == canonical_program()
    assert contract["parameters"] == {"scope": ["all_objects", "largest_only"]}
    assert contract["default"] == {"scope": "all_objects"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_matched_inputs_unique_largest_distinct_queries_and_30x30(seed: int) -> None:
    adapter = load_parametric("adapter")
    family = load_parametric("family")
    episodes = {
        scope: adapter.generate(seed, {"scope": scope}, 6, 4)
        for scope in ("all_objects", "largest_only")
    }
    inputs = {
        scope: [p["input"] for p in episode["train"] + episode["test"]]
        for scope, episode in episodes.items()
    }
    assert inputs["all_objects"] == inputs["largest_only"]
    assert len({json.dumps(g, separators=(",", ":")) for g in inputs["all_objects"]}) == 10
    for grid in inputs["all_objects"]:
        info = family.intermediate(grid)
        sizes = [obj["size"] for obj in info["objects"]]
        assert sizes.count(max(sizes)) == 1
        assert any(not obj["solid_bbox"] for obj in info["objects"])
    stress = episodes["all_objects"]["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(v != 0 for row in stress for v in row) >= 180
    assert episodes["all_objects"]["test"][-1]["output"] != episodes["largest_only"]["test"][-1]["output"]


def test_every_supported_prefix_identifies_scope_and_refutes_rivals() -> None:
    adapter = load_parametric("adapter")
    family = load_parametric("family")
    for seed in range(16):
        for demos in range(2, 7):
            for scope in ("all_objects", "largest_only"):
                episode = adapter.generate(seed, {"scope": scope}, demos, 4)
                opposite = adapter.generate(
                    seed,
                    {"scope": "largest_only" if scope == "all_objects" else "all_objects"},
                    demos,
                    4,
                )
                assert [p["input"] for p in episode["train"]] == [p["input"] for p in opposite["train"]]
                assert all(a["output"] != b["output"] for a, b in zip(episode["train"], opposite["train"]))
                survivors = set(family.RIVALS)
                for pair in episode["train"]:
                    survivors = {
                        rival for rival in survivors
                        if family.solve_rival(pair["input"], scope, rival) == pair["output"]
                    }
                assert not survivors, (seed, demos, scope, survivors)


def test_claimed_labels_match_python_and_smallest_counterfactual_changes() -> None:
    adapter = load_parametric("adapter")
    family = load_parametric("family")
    episode = adapter.generate(29, {"scope": "largest_only"}, 3, 4)
    for pair in episode["train"] + episode["test"]:
        assert family.solve(pair["input"], "largest_only") == pair["output"]
        assert family.solve_smallest_only(pair["input"]) != pair["output"]


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"scope": "x"}, {"scope": True}, {"scope": "all_objects", "x": 1}],
)
def test_invalid_settings_rejected(settings: object) -> None:
    with pytest.raises(ValueError):
        load_parametric("adapter").program(settings)


@pytest.mark.parametrize(
    "field,bad",
    [("seed", True), ("seed", -1), ("demos", 1), ("demos", 7),
     ("queries", 0), ("queries", 5), ("queries", 2.0)],
)
def test_invalid_counts_rejected(field: str, bad: object) -> None:
    kwargs = {"seed": 0, "settings": {"scope": "all_objects"}, "demos": 3, "queries": 4}
    kwargs[field] = bad
    with pytest.raises(ValueError):
        load_parametric("adapter").generate(**kwargs)
