"""Focused tests for the native leftmost-ranked band family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog

TASK_ID = "f5e7cf8dc78d"
ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
FAMILY_PATH = PARAMETRIC / "family.py"
AUDIT_PATH = PARAMETRIC / "audit_lessons.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return _load(FAMILY_PATH, "_family_f5e7cf8dc78d")


def _canonical_program() -> str:
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical(family):
    assert family.program({"frame_policy": "all_bands"}) == _canonical_program()
    assert family.program({"frame_policy": "leftmost_ranked"}) != _canonical_program()


@pytest.mark.parametrize(
    "bad",
    [None, {}, {"frame_policy": True}, {"frame_policy": "bad"}, {"x": "all_bands"}],
)
def test_settings_fail_closed(family, bad):
    with pytest.raises(ValueError):
        family.program(bad)


def test_counts_matched_inputs_and_prefix_stability(family):
    canonical = family.generate(17, {"frame_policy": "all_bands"}, 2, 4)
    alternate = family.generate(17, {"frame_policy": "leftmost_ranked"}, 2, 4)
    longer = family.generate(17, {"frame_policy": "all_bands"}, 6, 4)
    fewer_queries = family.generate(17, {"frame_policy": "all_bands"}, 2, 2)

    assert len(canonical["train"]) == 2
    assert len(canonical["test"]) == 4
    assert _inputs(canonical) == _inputs(alternate)
    assert canonical["train"] == longer["train"][:2]
    assert canonical["test"] == longer["test"]
    assert canonical["test"][:2] == fewer_queries["test"]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == 6
    assert [(len(p["input"]), len(p["input"][0])) for p in canonical["test"]] == [
        (15, 17),
        (20, 22),
        (25, 27),
        (30, 30),
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(
            canonical["train"] + canonical["test"],
            alternate["train"] + alternate["test"],
            strict=True,
        )
    )


@pytest.mark.parametrize("mode", ["all_bands", "leftmost_ranked"])
def test_first_two_demos_identify_setting_and_reject_rivals(family, mode):
    episode = family.generate(3, {"frame_policy": mode}, 2, 4)
    check = family.teaching_check(episode, {"frame_policy": mode})
    assert check["survivors"] == [{"frame_policy": mode}]
    assert check["surviving_rivals"] == []
    assert all(
        family.transform(pair["input"], {"frame_policy": mode}) == pair["output"]
        for pair in episode["test"]
    )


def test_stress_query_and_causal_counterfactual(family):
    episode = family.generate(29, {"frame_policy": "leftmost_ranked"}, 3, 4)
    pair = episode["test"][3]
    grid = pair["input"]
    output = pair["output"]
    assert len(grid) == len(grid[0]) == 30
    assert sum(cell != 0 for row in output for cell in row) >= 250
    edges = (
        [(0, c) for c in range(30)],
        [(29, c) for c in range(30)],
        [(r, 0) for r in range(30)],
        [(r, 29) for r in range(30)],
    )
    assert all(any(output[r][c] != 0 for r, c in edge) for edge in edges)
    intermediate = family.leftmost_intermediate(grid)
    wrong_rank = 1 if intermediate["rank"] != 1 else 2
    assert family.apply_ranked(grid, wrong_rank) != output


def test_leftmost_rule_is_not_encoded_by_fixed_profile_or_absolute_column(family):
    episodes = [
        family.generate(seed, {"frame_policy": "leftmost_ranked"}, 2, 4)
        for seed in range(4)
    ]
    stress_ranks = {
        family.leftmost_intermediate(episode["test"][3]["input"])["rank"]
        for episode in episodes
    }
    selected_columns = {
        family.leftmost_intermediate(pair["input"])["marker"][1]
        for episode in episodes
        for split in ("train", "test")
        for pair in episode[split]
    }
    assert len(stress_ranks) > 1
    assert any(column > 1 for column in selected_columns)
    for episode in episodes:
        check = family.teaching_check(episode, {"frame_policy": "leftmost_ranked"})
        assert "profile_rank" in check["rivals_tested"]
        assert "absolute_column_1" in check["rivals_tested"]
        assert "profile_rank" not in check["surviving_rivals"]
        assert "absolute_column_1" not in check["surviving_rivals"]


def test_public_turn_reveals_one_query_without_private_fields(family):
    episode = family.generate(11, {"frame_policy": "leftmost_ranked"}, 3, 4)
    public = family.public_turn(episode, 0)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    dumped = json.dumps(public)
    assert "frame_policy" not in dumped
    assert "program_solution" not in dumped
    assert public == family.public_turn(episode, 0)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 2, 4), (-1, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5)],
)
def test_invalid_requests_are_rejected(family, seed, demos, queries):
    with pytest.raises(ValueError):
        family.generate(seed, {"frame_policy": "all_bands"}, demos, queries)


def test_reusable_audit_covers_counts_shortcuts_and_stress():
    audit = _load(AUDIT_PATH, "_audit_f5e7cf8dc78d")
    report = audit.build_report(seeds=range(4), demo_counts=(2, 3, 6))
    assert report["status"] == "passed"
    assert report["episodes"] == 24
    assert report["harmful_survivors"] == 0
    assert report["exact_30x30_pairs"] == 24
    assert report["public_projection_failures"] == []
