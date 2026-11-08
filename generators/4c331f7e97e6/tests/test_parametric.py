"""Source repair and native parametric regressions for 4c331f7e97e6."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, public_challenge_bytes

TASK = "4c331f7e97e6"
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
    return _load(HOME / "generator.py", "_tested_4c331_generator")


def _family():
    return _load(PARAM / "family.py", "_tested_4c331_family")


def _adapter():
    return _load(PARAM / "adapter.py", "_tested_4c331_adapter")


def _wall_box(grid):
    ones = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    assert ones
    top = min(r for r, _ in ones)
    bottom = max(r for r, _ in ones)
    left = min(c for _, c in ones)
    right = max(c for _, c in ones)
    expected = (
        {(top, c) for c in range(left, right + 1)}
        | {(bottom, c) for c in range(left, right + 1)}
        | {(r, left) for r in range(top, bottom + 1)}
        | {(r, right) for r in range(top, bottom + 1)}
    )
    assert ones == expected
    return top, bottom, left, right


def test_production_generator_restores_closed_chamber_domain():
    generator = _generator()
    for difficulty in (None, "medium", "hard"):
        for seed in (0, 17, 431331):
            grid = generator.generate(seed, 0, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            top, bottom, left, right = _wall_box(grid)
            markers = [
                (r, c, value)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if value not in (0, 1)
            ]
            assert len(markers) >= 2
            assert all(top < r < bottom and left < c < right for r, c, _ in markers)


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    adapter = _adapter()
    authority = {v["program_solution"] for v in Catalog(ROOT)._variants()[TASK]}
    assert authority == {adapter.program({"followup": "canonical"})}
    assert adapter.program({"followup": "center_fill"}) not in authority


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_setting_identification_and_query_prefix(demos):
    adapter = _adapter()
    canonical = adapter.generate(17, {"followup": "canonical"}, demos, 4)
    alternate = adapter.generate(17, {"followup": "center_fill"}, demos, 4)
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


def test_stage_created_center_color_controls_fill_and_wrong_intermediate_changes_output():
    family = _family()
    grid = family.scene(9, 0)
    intermediate = family.center_intermediate(grid)
    assert grid[intermediate["center"][0]][intermediate["center"][1]] == 0
    assert intermediate["center_color"] != intermediate["first_marker_color"]
    assert family.solve(grid, "center_fill") != family.solve_wrong_first_marker(grid)
    top, bottom, left, right = intermediate["wall_box"]
    solved = family.solve(grid, "center_fill")
    assert all(solved[r][c] != 0 for r in range(top + 1, bottom) for c in range(left + 1, right))


def test_query_bank_contains_substantive_30x30_case_and_public_view_is_clean():
    adapter = _adapter()
    episode = adapter.generate(23, {"followup": "center_fill"}, 3, 4)
    bank = episode["private_query_bank"]
    assert len(bank) == 4
    assert any(len(p["input"]) == len(p["input"][0]) == 30 for p in bank)
    large = next(p["input"] for p in bank if len(p["input"]) == len(p["input"][0]) == 30)
    assert sum(value != 0 for row in large for value in row) >= 110
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

def test_reusable_bounded_audit_covers_counts_and_counterfactuals():
    audit = _load(PARAM / "audit.py", f"_tested_{TASK}_audit")
    report = audit.run_audit([0], protected=False)
    assert report["failures"] == []
    assert report["labeled_pairs"] == 260
    assert report["counterfactual_separations"] == 10
    assert report["coverage"]["max_shape"] == [30, 30]

def test_preflight_compat_accepts_singleton_test_pair_without_rewriting_catalog():
    compat = _load(PARAM / "preflight_compat.py", f"_tested_{TASK}_preflight_compat")
    pair = {"input": [[0]], "output": [[0]]}
    assert compat._split_pairs({"train": [pair]}, "train") == [pair]
    assert compat._split_pairs({"test": pair}, "test") == [pair]

