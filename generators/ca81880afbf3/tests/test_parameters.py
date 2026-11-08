from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TASK_ID = "ca81880afbf3"
ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
FAMILY_PATH = BASE / "family.py"
ADAPTER_PATH = BASE / "adapter.py"


def _load(path: Path, stem: str):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    name = f"_{TASK_ID}_{stem}_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_family_sources_exist_before_import():
    assert FAMILY_PATH.is_file(), "family.py is required"
    assert ADAPTER_PATH.is_file(), "adapter.py is required"
    for name in ("canonical.rkt", "bridge_equal_area.rkt", "wrong_shifted_centers.rkt", "promotion.json"):
        assert (BASE / name).is_file(), name


def test_episode_counts_are_prefix_stable_and_inputs_do_not_depend_on_setting():
    family = _load(FAMILY_PATH, "family")
    for seed in (0, 1, 17, 2**31 + 11):
        short = family.generate(seed, "fill_only", 2, 1)
        full = family.generate(seed, "fill_only", 6, 4)
        relay = family.generate(seed, "bridge_equal_area", 6, 4)
        assert short["train"] == full["train"][:2]
        assert short["test"] == full["test"][:1]
        assert [p["input"] for p in full["train"]] == [p["input"] for p in relay["train"]]
        assert [p["input"] for p in full["test"]] == [p["input"] for p in relay["test"]]
        assert len({json.dumps(p["input"]) for p in full["train"] + full["test"]}) == 10


def test_every_pair_has_square_fills_and_a_real_equal_area_relay():
    family = _load(FAMILY_PATH, "family")
    for seed in range(12):
        episode = family.generate(seed, "fill_only", 6, 4)
        for pair in episode["train"] + episode["test"]:
            info = family.intermediate(pair["input"])
            assert info["square_components"] >= 3
            assert info["nonsquare_components"] >= 1
            assert info["relay_pairs"] >= 1
            fill = family.solve(pair["input"], "fill_only")
            relay = family.solve(pair["input"], "bridge_equal_area")
            assert pair["output"] == fill
            assert fill != relay
            assert family.solve_wrong_shifted_centers(pair["input"]) != relay
            assert any(2 in row for row in fill)
            assert any(4 in row for row in relay)


def test_fourth_query_is_substantive_30_by_30_with_two_independent_relays():
    family = _load(FAMILY_PATH, "family")
    episode = family.generate(20261025, "bridge_equal_area", 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    info = family.intermediate(grid)
    assert info["square_components"] == 5
    assert info["nonsquare_components"] >= 1
    assert info["relay_pairs"] == 2
    assert info["derived_fill_cells"] == 45
    assert info["bridge_cells"] >= 35


def test_adapter_is_strict_and_default_program_is_exact_canonical_bytes():
    adapter = _load(ADAPTER_PATH, "adapter")
    canonical = (BASE / "canonical.rkt").read_text(encoding="utf-8")
    assert adapter.program({"finish_rule": "fill_only"}) == canonical
    assert adapter.program({"finish_rule": "bridge_equal_area"}) == (BASE / "bridge_equal_area.rkt").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        adapter.program({})
    with pytest.raises(ValueError):
        adapter.program({"finish_rule": "fill_only", "extra": 1})
    with pytest.raises(ValueError):
        adapter.generate(True, {"finish_rule": "fill_only"}, 3, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"finish_rule": "fill_only"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"finish_rule": "fill_only"}, 3, 5)


def test_adapter_returns_fresh_claims_and_dependency_contract():
    adapter = _load(ADAPTER_PATH, "adapter")
    first = adapter.generate(31, {"finish_rule": "bridge_equal_area"}, 3, 4)
    second = adapter.generate(31, {"finish_rule": "bridge_equal_area"}, 3, 4)
    assert first == second
    assert first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(31, {"finish_rule": "bridge_equal_area"}, 3, 4) == second
    dependency = adapter.dependency()
    assert set(dependency) == {"step_a", "intermediate", "step_b", "why_b_depends_on_a"}
    assert all(isinstance(value, str) and value.strip() for value in dependency.values())
    assert adapter.counterfactual_program() == (BASE / "wrong_shifted_centers.rkt").read_text(encoding="utf-8")


def test_bounded_audit_checks_counts_prefixes_relays_and_large_queries(tmp_path):
    audit = _load(BASE / "audit.py", "audit")
    report = audit.run_audit(range(4))
    assert report["passed"] is True
    assert report["episodes"] == 8
    assert report["pair_checks"] == 80
    assert report["demo_prefix_checks"] == 160
    assert report["query_prefix_checks"] == 80
    assert report["setting_output_changes"] == 80
    assert report["shifted_center_changes"] == 80
    assert report["large_queries"] == 8
    assert report["failures"] == []
