"""Production repair and native parametric regressions for be05cee2806f."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, public_challenge_bytes

TASK = "be05cee2806f"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK
PARAM = HOME / "workspace" / "parametric"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _generator():
    return _load(HOME / "generator.py", "_tested_be05_generator")


def _family():
    return _load(PARAM / "family.py", "_tested_be05_family")


def _adapter():
    return _load(PARAM / "adapter.py", "_tested_be05_adapter")


def test_canonical_inputs_and_repaired_defaults_exercise_both_zero_branches():
    generator = _generator()
    for record in Catalog(ROOT)._variants()[TASK]:
        for split in ("train", "test"):
            for pair in record[split]:
                assert generator.self_check(pair["input"]) == []

    for difficulty in (None, "easy", "medium", "hard"):
        for seed in (0, 17, 431331):
            grid = generator.generate(seed, 2, difficulty=difficulty)
            facts = generator.analyze_zero_components(grid)
            assert generator.self_check(grid, difficulty=difficulty) == []
            assert facts["touching_one_components"] >= 1
            assert facts["isolated_components"] >= 1
            assert facts["palette"] == list(range(10))
            assert generator.observe_overrides(grid) == {
                "grid_h": len(grid),
                "grid_w": len(grid[0]),
            }


def test_production_generator_override_contract_is_exact_and_fail_closed():
    generator = _generator()
    grid = generator.generate(9, 0, difficulty="hard", grid_h=30, grid_w=30)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert generator.observe_overrides(grid) == {"grid_h": 30, "grid_w": 30}
    assert generator.generate(9, 0, difficulty="hard", grid_h=30, grid_w=30) == grid
    assert generator.generate(9, 0, difficulty="hard", grid_h=30, grid_w=30) is not grid
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        generator.generate(0, 0, grid_height=12)
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(0, 0, difficulty="impossible")


@pytest.mark.parametrize("texture", ["no_holes", "all_holes", "single_hole"])
def test_legacy_degenerate_texture_names_remain_supported(texture):
    generator = _generator()
    grid = generator.generate(31, 0, difficulty="easy", grid_h=10, grid_w=11, texture=texture)
    assert (len(grid), len(grid[0])) == (10, 11)
    assert generator.generate(31, 0, difficulty="easy", grid_h=10, grid_w=11, texture=texture) == grid
    if texture == "no_holes":
        assert all(value != 0 for row in grid for value in row)
    elif texture == "all_holes":
        assert all(value == 0 for row in grid for value in row)
    else:
        components = generator.analyze_zero_components(grid)
        assert components["zero_component_count"] == 1
        assert components["touching_one_components"] == 1


def test_python_rule_mirror_recolors_whole_touching_components_only():
    generator = _generator()
    grid = [
        [2, 2, 2, 2, 2, 2],
        [2, 1, 0, 0, 3, 2],
        [2, 4, 4, 0, 3, 2],
        [2, 0, 0, 5, 5, 2],
        [2, 0, 6, 6, 6, 2],
        [2, 2, 2, 2, 2, 2],
    ]
    expected = [
        [2, 2, 2, 2, 2, 2],
        [2, 1, 1, 1, 3, 2],
        [2, 4, 4, 1, 3, 2],
        [2, 0, 0, 5, 5, 2],
        [2, 0, 6, 6, 6, 2],
        [2, 2, 2, 2, 2, 2],
    ]
    assert generator.rule_mirror(grid) == expected


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    adapter = _adapter()
    authority = {v["program_solution"] for v in Catalog(ROOT)._variants()[TASK]}
    assert authority == {adapter.program({"followup": "canonical"})}
    assert adapter.program({"followup": "activated_neighbors"}) not in authority


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_setting_identification_and_query_prefix(demos):
    adapter = _adapter()
    canonical = adapter.generate(17, {"followup": "canonical"}, demos, 4)
    alternate = adapter.generate(17, {"followup": "activated_neighbors"}, demos, 4)
    prefix = adapter.generate(17, {"followup": "canonical"}, demos, 1)
    for split in ("train", "test"):
        assert [p["input"] for p in canonical[split]] == [p["input"] for p in alternate[split]]
    assert canonical["train"] == prefix["train"]
    assert canonical["test"][:1] == prefix["test"]
    pairs = canonical["train"] + canonical["test"]
    assert len({json.dumps(p["input"], separators=(",", ":")) for p in pairs}) == demos + 4
    assert all(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(canonical[split], alternate[split], strict=True)
    )


def test_newly_absorbed_cells_control_stage_b_and_wrong_intermediate_separates():
    family = _family()
    grid = family.scene(9, 0)
    intermediate = family.activation_intermediate(grid)
    stage = family.canonical_absorb(grid)
    solved = family.solve(grid, "activated_neighbors")
    wrong = family.solve_wrong_original_ones(grid)

    assert intermediate["newly_absorbed_cells"]
    assert intermediate["stage_b_targets"]
    assert intermediate["preserved_zero_cells"]
    assert solved != stage
    assert solved != wrong
    assert all(grid[r][c] == 0 and stage[r][c] == 1 for r, c in intermediate["newly_absorbed_cells"])
    assert all(solved[r][c] == 1 for r, c in intermediate["stage_b_targets"])
    assert all(solved[r][c] == 0 for r, c in intermediate["preserved_zero_cells"])


def test_query_bank_contains_substantive_30x30_case_and_public_view_is_clean():
    adapter = _adapter()
    family = _family()
    episode = adapter.generate(23, {"followup": "activated_neighbors"}, 3, 4)
    bank = episode["private_query_bank"]
    assert len(bank) == 4
    assert any(len(p["input"]) == len(p["input"][0]) == 30 for p in bank)
    large = next(p["input"] for p in bank if len(p["input"]) == len(p["input"][0]) == 30)
    assert set(value for row in large for value in row) == set(range(10))
    assert sum(value not in (0, 1) for row in large for value in row) >= 700
    assert sum(
        left != right
        for left_row, right_row in zip(
            family.solve(large, "canonical"), family.solve(large, "activated_neighbors"), strict=True
        )
        for left, right in zip(left_row, right_row, strict=True)
    ) >= 8

    view = adapter.public_view(episode, 0)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1 and set(view["test"][0]) == {"input"}
    public_challenge_bytes(view)
    changed = copy.deepcopy(episode)
    changed["private_query_bank"][0]["output"] = [[9]]
    changed["program_solution"] = "secret"
    changed["settings"] = {"secret": True}
    assert public_challenge_bytes(adapter.public_view(changed, 0)) == public_challenge_bytes(view)


@pytest.mark.parametrize(
    "case",
    [
        dict(seed=True, settings={"followup": "canonical"}, demos=3, queries=4),
        dict(seed=0, settings={}, demos=3, queries=4),
        dict(seed=0, settings={"followup": "bad"}, demos=3, queries=4),
        dict(seed=0, settings={"followup": "canonical"}, demos=1, queries=4),
        dict(seed=0, settings={"followup": "canonical"}, demos=3, queries=5),
    ],
)
def test_invalid_adapter_requests_fail_closed(case):
    with pytest.raises(ValueError):
        _adapter().generate(**case)


def test_reusable_bounded_audit_covers_counts_rivals_and_counterfactuals():
    audit = _load(PARAM / "audit.py", f"_tested_{TASK}_audit")
    report = audit.run_audit([0], protected=False)
    assert report["failures"] == []
    assert report["labeled_pairs"] == 260
    assert report["counterfactual_separations"] == 10
    assert report["plausible_rival_rejections"] == 20
    assert report["coverage"]["max_shape"] == [30, 30]
