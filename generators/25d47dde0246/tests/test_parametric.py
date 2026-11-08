"""Native parametric regressions for 25d47dde0246."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, public_challenge_bytes

TASK = "25d47dde0246"
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


def _family():
    return _load(PARAM / "family.py", "_tested_25d47_family")


def _adapter():
    return _load(PARAM / "adapter.py", "_tested_25d47_adapter")


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    adapter = _adapter()
    authority = {v["program_solution"] for v in Catalog(ROOT)._variants()[TASK]}
    assert authority == {adapter.program({"followup": "canonical"})}
    assert adapter.program({"followup": "boundary_fill"}) not in authority


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_setting_identification_and_query_prefix(demos):
    adapter = _adapter()
    canonical = adapter.generate(17, {"followup": "canonical"}, demos, 4)
    alternate = adapter.generate(17, {"followup": "boundary_fill"}, demos, 4)
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


def test_crop_boundary_mask_controls_fill_and_wrong_order_changes_output():
    family = _family()
    grid = family.scene(9, 0)
    intermediate = family.boundary_intermediate(grid)
    stage = family.canonical_crop(grid)
    solved = family.solve(grid, "boundary_fill")
    wrong = family.solve_wrong_order(grid)

    assert intermediate["boundary_zero_cells"]
    assert intermediate["enclosed_zero_cells"]
    assert solved != stage
    assert solved != wrong
    assert all(solved[r][c] == 8 for r, c in intermediate["boundary_zero_cells"])
    assert all(solved[r][c] == 0 for r, c in intermediate["enclosed_zero_cells"])
    assert len(wrong) == len(grid) and len(wrong[0]) == len(grid[0])


def test_query_bank_contains_substantive_30x30_case_and_public_view_is_clean():
    adapter = _adapter()
    episode = adapter.generate(23, {"followup": "boundary_fill"}, 3, 4)
    bank = episode["private_query_bank"]
    assert len(bank) == 4
    assert any(len(p["input"]) == len(p["input"][0]) == 30 for p in bank)
    large = next(p["input"] for p in bank if len(p["input"]) == len(p["input"][0]) == 30)
    stage = _family().canonical_crop(large)
    assert sum(value != 0 for row in large for value in row) >= 100
    assert sum(value == 8 for row in _family().solve(large, "boundary_fill") for value in row) >= 100
    assert len(stage) >= 24 and len(stage[0]) >= 24

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
    assert report["plausible_rival_rejections"] == 20
    assert report["coverage"]["max_shape"] == [30, 30]
