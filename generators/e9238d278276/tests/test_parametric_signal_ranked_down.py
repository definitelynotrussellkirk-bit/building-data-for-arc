"""Focused tests for the native signal-ranked mixed-gravity family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog

TASK_ID = "e9238d278276"
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
    return _load(FAMILY_PATH, "_family_e9238d278276")


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
    assert family.program({"gravity_policy": "all_up"}) == _canonical_program()
    assert family.program({"gravity_policy": "signal_ranked_down"}) != _canonical_program()


@pytest.mark.parametrize(
    "bad",
    [None, {}, {"gravity_policy": True}, {"gravity_policy": "bad"}, {"x": "all_up"}],
)
def test_settings_fail_closed(family, bad):
    with pytest.raises(ValueError):
        family.program(bad)


def test_counts_matched_inputs_and_prefix_stability(family):
    canonical = family.generate(17, {"gravity_policy": "all_up"}, 2, 4)
    alternate = family.generate(17, {"gravity_policy": "signal_ranked_down"}, 2, 4)
    longer = family.generate(17, {"gravity_policy": "all_up"}, 6, 4)
    fewer_queries = family.generate(17, {"gravity_policy": "all_up"}, 2, 2)

    assert len(canonical["train"]) == 2
    assert len(canonical["test"]) == 4
    assert _inputs(canonical) == _inputs(alternate)
    assert canonical["train"] == longer["train"][:2]
    assert canonical["test"] == longer["test"]
    assert canonical["test"][:2] == fewer_queries["test"]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == 6
    assert [(len(p["input"]), len(p["input"][0])) for p in canonical["test"]] == [
        (14, 16),
        (19, 21),
        (24, 27),
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


@pytest.mark.parametrize("mode", ["all_up", "signal_ranked_down"])
def test_first_two_demos_identify_setting_and_reject_rivals(family, mode):
    episode = family.generate(3, {"gravity_policy": mode}, 2, 4)
    check = family.teaching_check(episode, {"gravity_policy": mode})
    assert check["survivors"] == [{"gravity_policy": mode}]
    assert check["surviving_rivals"] == []
    assert all(
        family.transform(pair["input"], {"gravity_policy": mode}) == pair["output"]
        for pair in episode["test"]
    )


def test_stress_query_and_causal_counterfactual(family):
    episode = family.generate(29, {"gravity_policy": "signal_ranked_down"}, 3, 4)
    pair = episode["test"][3]
    grid = pair["input"]
    assert len(grid) == len(grid[0]) == 30
    assert sum(cell != 0 for row in grid for cell in row) >= 100
    assert any(grid[0][column] != 0 for column in range(30))
    assert any(grid[29][column] != 0 for column in range(30))
    assert any(grid[row][0] != 0 for row in range(30))
    assert any(grid[row][29] != 0 for row in range(30))
    intermediate = family.signal_intermediate(grid)
    wrong_rank = 1 if intermediate["rank"] != 1 else 2
    assert family.apply_ranked_down(grid, wrong_rank) != pair["output"]


def test_public_turn_reveals_one_query_without_private_fields(family):
    episode = family.generate(11, {"gravity_policy": "signal_ranked_down"}, 3, 4)
    public = family.public_turn(episode, 0)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert "settings" not in json.dumps(public)
    assert public == family.public_turn(episode, 0)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 2, 4), (-1, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5)],
)
def test_invalid_requests_are_rejected(family, seed, demos, queries):
    with pytest.raises(ValueError):
        family.generate(seed, {"gravity_policy": "all_up"}, demos, queries)


def test_reusable_audit_covers_counts_shortcuts_and_stress():
    audit = _load(AUDIT_PATH, "_audit_e9238d278276")
    report = audit.build_report(seeds=range(4), demo_counts=(2, 3, 6))
    assert report["status"] == "passed"
    assert report["episodes"] == 24
    assert report["harmful_survivors"] == 0
    assert report["exact_30x30_pairs"] == 24
    assert report["public_projection_failures"] == []
