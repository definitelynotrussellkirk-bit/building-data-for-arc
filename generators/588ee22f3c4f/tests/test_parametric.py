"""Source repair and native parametric regressions for 588ee22f3c4f."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, public_challenge_bytes

TASK = "588ee22f3c4f"
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
    return _load(HOME / "generator.py", "_tested_588ee_generator")


def _family():
    return _load(PARAM / "family.py", "_tested_588ee_family")


def _adapter():
    return _load(PARAM / "adapter.py", "_tested_588ee_adapter")


def test_production_generator_places_motif_on_canonical_reflection_side():
    generator = _generator()
    for axis in (0, 1):
        for seed in (0, 17, 43):
            grid = generator.generate(seed, 0, difficulty="medium", axis=axis)
            assert generator.self_check(grid, difficulty="medium") == []
            h, w = len(grid), len(grid[0])
            guides = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
            motif = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
            assert len(guides) == 2 and motif
            if axis == 0:
                assert guides[0][0] == guides[1][0]
                assert all(r < (h - 1 - r) and grid[h - 1 - r][c] == 0 for r, c in motif)
            else:
                assert guides[0][1] == guides[1][1]
                assert all(c < (w - 1 - c) and grid[r][w - 1 - c] == 0 for r, c in motif)


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    adapter = _adapter()
    authority = {v["program_solution"] for v in Catalog(ROOT)._variants()[TASK]}
    assert authority == {adapter.program({"followup": "canonical"})}
    assert adapter.program({"followup": "mirror_bridge"}) not in authority


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_setting_identification_and_query_prefix(demos):
    adapter = _adapter()
    canonical = adapter.generate(17, {"followup": "canonical"}, demos, 4)
    alternate = adapter.generate(17, {"followup": "mirror_bridge"}, demos, 4)
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


def test_stage_created_mirror_partner_controls_bridge_and_wrong_length_changes_output():
    family = _family()
    grid = family.scene(9, 0)
    intermediate = family.bridge_intermediate(grid)
    assert intermediate["spans"]
    first = intermediate["spans"][0]
    assert grid[first["mirror"][0]][first["mirror"][1]] == 0
    assert family.solve(grid, "mirror_bridge") != family.solve_wrong_one_step(grid)


def test_query_bank_contains_substantive_30x30_case_and_public_view_is_clean():
    adapter = _adapter()
    episode = adapter.generate(23, {"followup": "mirror_bridge"}, 3, 4)
    bank = episode["private_query_bank"]
    assert len(bank) == 4
    assert any(len(p["input"]) == len(p["input"][0]) == 30 for p in bank)
    large = next(p["input"] for p in bank if len(p["input"]) == len(p["input"][0]) == 30)
    assert sum(value != 0 for row in large for value in row) >= 10
    solved = _family().solve(large, "mirror_bridge")
    assert sum(value != 0 for row in solved for value in row) >= 80
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

