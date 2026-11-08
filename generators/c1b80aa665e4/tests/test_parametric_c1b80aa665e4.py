"""Native parametric regressions for c1b80aa665e4."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "c1b80aa665e4"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _modules():
    return _load("prototype", "prototype.py"), _load("adapter", "adapter.py")


def _setting(policy: str) -> dict[str, str]:
    return {"isolation_policy": policy}


def _inputs(episode: dict) -> list:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_settings_are_strict():
    prototype, adapter = _modules()
    canonical = (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8")
    alternate = (PARAMETRIC / "largest_cluster_color.rkt").read_text(encoding="utf-8")
    assert adapter.program(_setting("all_isolated")) == canonical
    assert adapter.program(_setting("largest_cluster_color")) == alternate
    assert canonical != alternate
    assert prototype.POLICIES == ("all_isolated", "largest_cluster_color")
    for bad in ({}, {"isolation_policy": "unknown"}, {"isolation_policy": "all_isolated", "x": 1}, None):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_generation_is_deterministic_prefix_stable_matched_and_copy_isolated():
    prototype, adapter = _modules()
    for seed in (0, 17, 991):
        canonical = adapter.generate(seed, _setting("all_isolated"), 6, 4)
        alternate = adapter.generate(seed, _setting("largest_cluster_color"), 6, 4)
        assert _inputs(canonical) == _inputs(alternate)
        assert canonical == adapter.generate(seed, _setting("all_isolated"), 6, 4)
        assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == 10
        for demos in range(2, 7):
            short = adapter.generate(seed, _setting("all_isolated"), demos, 1)
            assert short["train"] == canonical["train"][:demos]
            assert short["test"] == canonical["test"][:1]
        for queries in range(1, 5):
            short = adapter.generate(seed, _setting("all_isolated"), 3, queries)
            assert short["train"] == canonical["train"][:3]
            assert short["test"] == canonical["test"][:queries]
        pristine = copy.deepcopy(canonical)
        canonical["train"][0]["input"][0][0] = 8
        assert adapter.generate(seed, _setting("all_isolated"), 6, 4) == pristine


def test_two_demos_identify_setting_and_all_claims_match_mirror():
    prototype, adapter = _modules()
    for seed in range(24):
        episodes = {policy: adapter.generate(seed, _setting(policy), 2, 4) for policy in prototype.POLICIES}
        assert [p["input"] for p in episodes["all_isolated"]["train"]] == [
            p["input"] for p in episodes["largest_cluster_color"]["train"]
        ]
        descriptions = [prototype.describe_case(pair["input"]) for pair in episodes["largest_cluster_color"]["train"]]
        assert descriptions[0]["anchor_color"] != descriptions[1]["anchor_color"]
        assert descriptions[0]["largest_component_unique"]
        assert descriptions[1]["largest_component_unique"]
        assert descriptions[0]["first_cluster_color"] != descriptions[0]["anchor_color"]
        assert descriptions[1]["last_cluster_color"] != descriptions[1]["anchor_color"]
        for chosen, episode in episodes.items():
            survivors = [
                rival for rival in prototype.POLICIES
                if all(prototype.solve(pair["input"], rival) == pair["output"] for pair in episode["train"])
            ]
            assert survivors == [chosen]
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.solve(pair["input"], chosen)


def test_minimum_lesson_refutes_declared_shortcuts():
    prototype, adapter = _modules()
    for seed in range(64):
        for policy in prototype.POLICIES:
            episode = adapter.generate(seed, _setting(policy), 2, 4)
            labels = [pair["output"] for pair in episode["train"]]
            for name, rival in prototype.rivals_for(policy).items():
                predictions = [rival(pair["input"]) for pair in episode["train"]]
                assert predictions != labels, (seed, policy, name)


def test_fourth_query_is_substantive_30x30_and_exposes_causal_dependency():
    prototype, adapter = _modules()
    episode = adapter.generate(17, _setting("largest_cluster_color"), 3, 4)
    pair = episode["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 45
    assert len({r for r, _ in nonzero}) >= 24
    assert len({c for _, c in nonzero}) >= 24
    assert any(r in (0, 29) or c in (0, 29) for r, c in nonzero)
    description = prototype.describe_case(grid)
    assert description["anchor_color"] != description["smallest_cluster_color"]
    intended = prototype.solve(grid, "largest_cluster_color")
    wrong = prototype.solve_with_smallest_cluster_color(grid)
    assert intended != wrong
    assert intended == pair["output"]


def test_public_turn_hides_private_fields_and_first_turn_matches_single_query_use():
    prototype, adapter = _modules()
    full = adapter.generate(33, _setting("largest_cluster_color"), 3, 4)
    single = adapter.generate(33, _setting("largest_cluster_color"), 3, 1)
    first_full = prototype.public_turn(full, 0)
    first_single = prototype.public_turn(single, 0)
    assert first_full == first_single
    assert set(first_full) == {"train", "test"}
    assert len(first_full["test"]) == 1
    assert set(first_full["test"][0]) == {"input"}
    raw = public_challenge_bytes(first_full)
    assert json.loads(raw) == first_full
    assert public_challenge_id(first_full) == hashlib.sha256(raw).hexdigest()
    altered = copy.deepcopy(full)
    altered["program_solution"] = "private-change"
    altered["test"][0]["output"] = [[9]]
    assert prototype.public_turn(altered, 0) == first_full


def test_bounded_self_audit_refutes_declared_shortcuts():
    audit = _load("self_audit", "self_audit.py")
    report = audit.structural_audit(range(32))
    assert report["status"] == "pass"
    assert report["episodes"] == 64
    assert report["lesson_prefixes"] == 320
    assert report["teaching_gaps"] == []
    assert report["rival_errors"] == []
    assert report["stress_30x30"] == 64
    assert report["causal_cases"] == 32


def test_invalid_counts_seeds_and_query_indices_are_rejected():
    prototype, adapter = _modules()
    for seed, demos, queries in ((-1, 3, 4), (True, 3, 4), (0, 1, 4), (0, 7, 4), (0, 3, 0), (0, 3, 5), (0, True, 4)):
        with pytest.raises(ValueError):
            adapter.generate(seed, _setting("all_isolated"), demos, queries)
    episode = adapter.generate(0, _setting("all_isolated"), 2, 1)
    for index in (-1, 1, True):
        with pytest.raises(ValueError):
            prototype.public_turn(episode, index)
