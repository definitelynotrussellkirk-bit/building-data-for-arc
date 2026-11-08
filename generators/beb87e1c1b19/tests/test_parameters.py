from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TASK_ID = "beb87e1c1b19"
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
    for name in ("canonical.rkt", "xor.rkt", "wrong_identity_intermediate.rkt", "promotion.json"):
        assert (BASE / name).is_file(), name


def test_episode_counts_are_prefix_stable_and_inputs_do_not_depend_on_setting():
    family = _load(FAMILY_PATH, "family")
    for seed in (0, 1, 17, 2**31 + 9):
        union_short = family.generate(seed, "union", 2, 1)
        union_full = family.generate(seed, "union", 6, 4)
        xor_full = family.generate(seed, "xor", 6, 4)
        assert union_short["train"] == union_full["train"][:2]
        assert union_short["test"] == union_full["test"][:1]
        assert [p["input"] for p in union_full["train"]] == [p["input"] for p in xor_full["train"]]
        assert [p["input"] for p in union_full["test"]] == [p["input"] for p in xor_full["test"]]
        assert len({json.dumps(p["input"]) for p in union_full["train"] + union_full["test"]}) == 10


def test_every_generated_pair_has_unique_transform_and_distinguishes_union_from_xor():
    family = _load(FAMILY_PATH, "family")
    for seed in range(12):
        episode = family.generate(seed, "union", 6, 4)
        for pair in episode["train"] + episode["test"]:
            info = family.intermediate(pair["input"])
            assert info["transform"] in family.TRANSFORMS[1:]
            assert info["transform_matches"] == 1
            union = family.solve(pair["input"], "union")
            xor = family.solve(pair["input"], "xor")
            assert pair["output"] == union
            assert union != xor
            assert family.solve_wrong_identity(pair["input"], "xor") != xor


def test_fourth_query_is_a_substantive_30_by_30_input():
    family = _load(FAMILY_PATH, "family")
    episode = family.generate(20261025, "xor", 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    info = family.intermediate(grid)
    assert info["panel_shapes"] == [[30, 9], [30, 9], [30, 10]]
    assert info["c_support"] >= 18
    assert info["overlap_support"] >= 2
    assert info["exclusive_support"] >= 2


def test_adapter_is_strict_and_default_program_is_exact_canonical_bytes():
    adapter = _load(ADAPTER_PATH, "adapter")
    canonical = (BASE / "canonical.rkt").read_text(encoding="utf-8")
    assert adapter.program({"composition": "union"}) == canonical
    assert adapter.program({"composition": "xor"}) == (BASE / "xor.rkt").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        adapter.program({})
    with pytest.raises(ValueError):
        adapter.program({"composition": "union", "extra": True})
    with pytest.raises(ValueError):
        adapter.generate(True, {"composition": "union"}, 3, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"composition": "union"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"composition": "union"}, 3, 5)


def test_adapter_returns_fresh_claims_and_dependency_contract():
    adapter = _load(ADAPTER_PATH, "adapter")
    first = adapter.generate(31, {"composition": "xor"}, 3, 4)
    second = adapter.generate(31, {"composition": "xor"}, 3, 4)
    assert first == second
    assert first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(31, {"composition": "xor"}, 3, 4) == second
    dependency = adapter.dependency()
    assert set(dependency) == {"step_a", "intermediate", "step_b", "why_b_depends_on_a"}
    assert all(isinstance(value, str) and value.strip() for value in dependency.values())
    assert adapter.counterfactual_program() == (BASE / "wrong_identity_intermediate.rkt").read_text(encoding="utf-8")


def test_bounded_audit_covers_counts_and_rejects_identity_intermediate():
    audit = _load(BASE / "audit.py", "audit")
    report = audit.run_bounded_audit(seeds=range(4))
    assert report["status"] == "passed"
    assert report["failures"] == []
    assert report["episodes"] == 8
    assert report["pair_checks"] == 80
    assert report["prefix_checks"] == 160
    assert report["identity_ablation_changes"] == 80
    assert report["setting_output_changes"] == 80
    assert report["large_queries"] == 8
