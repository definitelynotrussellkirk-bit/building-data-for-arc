from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK = "26f02d922ca0"
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
    assert family.MODES == ("all_matches", "match_count_pointer")
    assert adapter.program({"report_mode": "all_matches"}) == _canonical_program()
    assert adapter.program({"report_mode": "match_count_pointer"}) == (
        PARAM / "match-count-pointer.rkt"
    ).read_text(encoding="utf-8")


def test_counts_are_independent_prefix_stable_and_inputs_ignore_setting():
    adapter = _load("adapter", PARAM / "adapter.py")
    small = adapter.generate(17, {"report_mode": "all_matches"}, 4, 1)
    large = adapter.generate(17, {"report_mode": "all_matches"}, 6, 4)
    alternate = adapter.generate(17, {"report_mode": "match_count_pointer"}, 6, 4)
    assert small["train"] == large["train"][:4]
    assert small["test"] == large["test"][:1]
    assert [p["input"] for p in large["train"] + large["test"]] == [
        p["input"] for p in alternate["train"] + alternate["test"]
    ]
    frozen = {
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in large["train"] + large["test"]
    }
    assert len(frozen) == 10


def test_four_demonstrations_identify_each_setting_and_cover_base_semantics():
    family = _load("family", PARAM / "family.py")
    for mode in family.MODES:
        episode = family.generate_episode(23, mode, demos=4, queries=4)
        assert family.teaching_survivors(episode["train"]) == [mode]
        assert family.finite_rival_holes(episode["train"], episode["test"], mode) == []
    bank = family.episode_inputs(23)
    hits = {
        name: any(predicate(grid) for grid in bank["train"][:4])
        for name, predicate in family.BASE.SEMANTIC_WITNESSES.items()
    }
    assert hits and all(hits.values()), hits


def test_match_count_pointer_consumes_match_flags_and_wrong_count_changes_output():
    family = _load("family", PARAM / "family.py")
    episode = family.generate_episode(7, "match_count_pointer", demos=4, queries=4)
    witnesses = []
    for pair in episode["train"] + episode["test"]:
        flags = family.match_flags(pair["input"])
        assert family.pointer_from_flags(flags) == pair["output"]
        if family.pointer_from_nonmatch_count(flags) != pair["output"]:
            witnesses.append(pair)
    assert witnesses


def test_stress_query_is_30_by_30_dense_and_rule_valid():
    family = _load("family", PARAM / "family.py")
    stress = family.episode_inputs(31)["test"][-1]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(cell != 0 for row in stress for cell in row) >= 80
    assert family.BASE.self_check(stress) == []
    flags = family.match_flags(stress)
    assert len(flags) == 4
    assert 0 in flags and 8 in flags
    assert family.solve(stress, "match_count_pointer") != family.solve(stress, "all_matches")


def test_strict_contract_validation_and_minimum_demos():
    adapter = _load("adapter", PARAM / "adapter.py")
    with pytest.raises(ValueError):
        adapter.program({"report_mode": "unknown"})
    with pytest.raises(ValueError):
        adapter.program({"report_mode": "all_matches", "extra": 1})
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(True, {"report_mode": "all_matches"}, 4, 4)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"report_mode": "all_matches"}, 3, 4)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"report_mode": "all_matches"}, 4, 5)
