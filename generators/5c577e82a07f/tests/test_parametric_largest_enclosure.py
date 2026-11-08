"""Focused native-parametric checks for the largest-enclosure composition."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_DIR = Path(__file__).resolve().parents[1]
PARAM_DIR = TASK_DIR / "workspace" / "parametric"


def _rule_application(source, grid):
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"({wrap_rule(source)} '({rows}))"


def _load(filename: str, name: str):
    path = PARAM_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load("prototype.py", "task_5c577e82a07f_enclosure_prototype")


def _adapter():
    return _load("adapter.py", "task_5c577e82a07f_enclosure_adapter")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_default_program_is_exact_canonical_and_settings_are_strict():
    adapter = _adapter()
    canonical = (PARAM_DIR / "canonical.rkt").read_text(encoding="utf-8")
    assert adapter.program({"enclosure_policy": "borders_only"}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "486ca16c83e15864e35f8c366a80e1370c46ef77022e9d549af3cf4268193553"
    )
    alternate = adapter.program({"enclosure_policy": "largest_enclosure"})
    assert alternate != canonical
    for bad in (
        {},
        {"enclosure_policy": "largest"},
        {"enclosure_policy": True},
        {"enclosure_policy": "borders_only", "extra": 1},
        None,
    ):
        with pytest.raises(ValueError, match="enclosure_policy"):
            adapter.program(bad)


def test_episode_counts_matched_inputs_prefixes_and_public_turns():
    adapter = _adapter()
    for seed in (0, 17, 41):
        full = {}
        for policy in adapter.POLICIES:
            full[policy] = adapter.generate(
                seed, {"enclosure_policy": policy}, demos=6, queries=4
            )
            episode = full[policy]
            assert len(episode["train"]) == 6
            assert len(episode["test"]) == 4
            assert len({_grid_key(g) for g in _inputs(episode)}) == 10
            for grid in _inputs(episode):
                assert 1 <= len(grid) <= 30
                assert 1 <= len(grid[0]) <= 30
                assert all(
                    type(value) is int and 0 <= value <= 9
                    for row in grid
                    for value in row
                )
            first = adapter.generate(
                seed, {"enclosure_policy": policy}, demos=2, queries=1
            )
            assert first["train"] == episode["train"][:2]
            assert first["test"] == episode["test"][:1]
            public = adapter.public_turn(episode, 2)
            assert set(public) == {"train", "test"}
            assert len(public["test"]) == 1
            assert set(public["test"][0]) == {"input"}
            assert public["test"][0]["input"] == episode["test"][2]["input"]
            frozen = copy.deepcopy(episode)
            public["train"][0]["input"][0][0] = 9
            assert episode == frozen
        assert _inputs(full["borders_only"]) == _inputs(full["largest_enclosure"])


def test_first_two_demonstrations_reject_declared_shortcuts_for_each_setting():
    prototype = _prototype()
    adapter = _adapter()
    for seed in (0, 17, 41):
        for policy in adapter.POLICIES:
            episode = adapter.generate(
                seed, {"enclosure_policy": policy}, demos=2, queries=4
            )
            assert prototype.surviving_rivals(episode["train"], policy) == []
            assert all(
                prototype.solve(pair["input"], policy) == pair["output"]
                for pair in episode["train"] + episode["test"]
            )


def test_nested_scenes_make_the_intermediate_topological_and_unique():
    prototype = _prototype()
    adapter = _adapter()
    episode = adapter.generate(
        17, {"enclosure_policy": "largest_enclosure"}, demos=2, queries=4
    )
    analyses = [prototype.analyze_after_borders(pair["input"]) for pair in episode["train"]]
    assert all(item["unique_largest"] for item in analyses)
    assert all(len(item["enclosed_regions"]) >= 2 for item in analyses)
    # At least one winning region is a non-rectangular annulus created only
    # after nested borders are completed, not a direct original rectangle fill.
    assert any(
        len(item["winner"]) < item["winner_bbox_area"]
        for item in analyses
    )
    assert all(
        prototype.skip_completion(pair["input"])
        != prototype.solve(pair["input"], "largest_enclosure")
        for pair in episode["train"]
    )


def test_four_query_bank_contains_a_substantive_30_by_30_topology_case():
    prototype = _prototype()
    adapter = _adapter()
    episode = adapter.generate(
        0, {"enclosure_policy": "largest_enclosure"}, demos=3, queries=4
    )
    large = [pair for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
    assert len(large) == 1
    grid = large[0]["input"]
    colored = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert any(r == 0 for r, _ in colored)
    assert any(r == 29 for r, _ in colored)
    assert any(c == 0 for _, c in colored)
    assert any(c == 29 for _, c in colored)
    quadrants = {
        ("top" if r < 15 else "bottom", "left" if c < 15 else "right")
        for r, c in colored
    }
    assert len(quadrants) == 4
    analysis = prototype.analyze_after_borders(grid)
    assert analysis["unique_largest"]
    assert len(analysis["enclosed_regions"]) == 3
    assert len(analysis["winner"]) >= 200


def test_python_claims_match_both_protected_racket_programs():
    adapter = _adapter()
    with RacketBridge(timeout=20, startup_timeout=60) as bridge:
        for policy in adapter.POLICIES:
            episode = adapter.generate(
                0, {"enclosure_policy": policy}, demos=2, queries=4
            )
            program = adapter.program({"enclosure_policy": policy})
            for pair in episode["train"] + episode["test"]:
                observed = bridge.eval_text(_rule_application(program, pair["input"]))
                assert observed == pair["output"]


def test_reusable_audit_sweeps_count_prefix_and_rival_surfaces():
    audit = _load("audit.py", "task_5c577e82a07f_enclosure_audit")
    report = audit.run_python_sweep(
        seeds=range(3), demo_counts=(2, 6), query_counts=(1, 4)
    )
    assert report["episodes"] == 24
    assert report["pairs"] == 156
    assert report["matched_input_comparisons"] == 12
    assert report["prefix_checks"] == 12
    assert report["rival_failures"] == []
    assert report["generation_failures"] == []
