from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK = "bf47583ab6e3"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = find_root(__file__)
PARAM = TASK_DIR / "workspace" / "parametric"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def _load(name: str, path: Path):
    body = path.read_bytes()
    module_name = f"_{TASK}_{name}_{hashlib.sha256(body).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def _canonical_program() -> str:
    from arcpuzzles import Catalog

    record = Catalog(REPO).get(TASK)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_parametric_sources_exist_and_default_program_is_byte_exact():
    family = _load("family", PARAM / "family.py")
    adapter = _load("adapter", PARAM / "adapter.py")
    assert family.MODES == ("plus_union", "component_boxes")
    assert adapter.program({"output_mode": "plus_union"}) == _canonical_program()
    assert adapter.program({"output_mode": "component_boxes"}) == (
        PARAM / "component-boxes.rkt"
    ).read_text(encoding="utf-8")


def test_counts_are_independent_prefix_stable_and_inputs_ignore_setting():
    adapter = _load("adapter", PARAM / "adapter.py")
    small = adapter.generate(17, {"output_mode": "plus_union"}, 2, 1)
    large = adapter.generate(17, {"output_mode": "plus_union"}, 6, 4)
    alternate = adapter.generate(17, {"output_mode": "component_boxes"}, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert [p["input"] for p in large["train"] + large["test"]] == [
        p["input"] for p in alternate["train"] + alternate["test"]
    ]
    frozen = {
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in large["train"] + large["test"]
    }
    assert len(frozen) == 10


def test_two_demonstrations_identify_each_declared_setting_and_refute_shortcuts():
    family = _load("family", PARAM / "family.py")
    for mode in family.MODES:
        episode = family.generate_episode(29, mode, demos=2, queries=4)
        assert family.teaching_survivors(episode["train"]) == [mode]
        assert family.finite_rival_holes(episode["train"], episode["test"], mode) == []


def test_component_boxes_really_consumes_the_grown_component_intermediate():
    family = _load("family", PARAM / "family.py")
    episode = family.generate_episode(3, "component_boxes", demos=2, queries=4)
    pairs = episode["train"] + episode["test"]
    witnesses = [
        pair
        for pair in pairs
        if family.solve_direct_seed_squares(pair["input"]) != pair["output"]
    ]
    assert witnesses
    pair = witnesses[0]
    intermediate = family.grow_plus(pair["input"])
    assert family.box_grown_components(intermediate) == pair["output"]
    assert family.box_seed_components(pair["input"]) != pair["output"]


def test_boundary_bank_contains_substantive_30_by_30_query():
    family = _load("family", PARAM / "family.py")
    bank = family.episode_inputs(31)
    stress = bank["test"][-1]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(cell != 0 for row in stress for cell in row) >= 8
    boxed = family.solve(stress, "component_boxes")
    assert sum(cell != 0 for row in boxed for cell in row) >= 60
    assert boxed != family.solve(stress, "plus_union")


def test_strict_contract_validation_rejects_bool_unknown_and_bad_counts():
    adapter = _load("adapter", PARAM / "adapter.py")
    with pytest.raises(ValueError):
        adapter.program({"output_mode": "unknown"})
    with pytest.raises(ValueError):
        adapter.program({"output_mode": "plus_union", "extra": 1})
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(True, {"output_mode": "plus_union"}, 2, 4)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"output_mode": "plus_union"}, 1, 4)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"output_mode": "plus_union"}, 2, 5)
