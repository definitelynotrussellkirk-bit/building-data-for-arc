"""Contract tests for the native 73f849e69e0a parametric family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random

import pytest

from reviewer_support import find_root

TASK_ID = "73f849e69e0a"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


def _load(path=SOURCE, name="parametric_73f849e69e0a"):
    assert path.is_file(), f"task-local source is missing: {path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load()


def _canonical_program() -> str:
    matches = []
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row["program_solution"])
    assert matches and len(set(matches)) == 1
    return matches[0]


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_rotate_is_distinct(proto) -> None:
    canonical = _canonical_program()
    assert proto.program({"orientation": "identity"}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "07d5df073b976e08aaca5c377718a2554bbddca567207d05496b491986a33e2d"
    )
    alternate = proto.program({"orientation": "rotate_cw"})
    assert alternate != canonical
    assert "(* (- 2 dc) 2)" in alternate
    assert "(* dr 2)" in alternate


def test_matched_inputs_identify_orientation_and_cover_separator_roles(proto) -> None:
    identity = proto.generate(17, {"orientation": "identity"}, demos=3, queries=4)
    rotated = proto.generate(17, {"orientation": "rotate_cw"}, demos=3, queries=4)
    assert _inputs(identity) == _inputs(rotated)
    assert len(identity["train"]) == len(rotated["train"]) == 3
    assert len(identity["test"]) == len(rotated["test"]) == 4
    assert len({proto.digest(grid) for grid in _inputs(identity)}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(identity["train"], rotated["train"]))
    facts = [proto.semantic_observables(pair["input"]) for pair in identity["train"]]
    assert {row["sep_row"] for row in facts} == {6, 7, 8}
    assert all(row["icon_asymmetric_under_rotate_cw"] for row in facts)
    assert all(row["icon_contains_red"] for row in facts)
    assert all(row["icon_color_count"] >= 3 for row in facts)
    assert all(row["marker_count"] >= 3 for row in facts)
    stress_pair = identity["test"][-1]
    stress = proto.semantic_observables(stress_pair["input"])
    assert (stress["bot_h"], stress["bot_w"]) == (10, 10)
    assert (len(stress_pair["output"]), len(stress_pair["output"][0])) == (30, 30)
    assert stress["marker_bbox"] == [0, 0, 9, 9]


@pytest.mark.parametrize("demos", [2, 6])
def test_supported_demo_boundaries_return_four_queries(proto, demos: int) -> None:
    episode = proto.generate(5, {"orientation": "identity"}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4


def test_demo_and_query_prefixes_are_count_independent(proto) -> None:
    small = proto.generate(13, {"orientation": "identity"}, demos=2, queries=1)
    large = proto.generate(13, {"orientation": "identity"}, demos=6, queries=4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    more_queries = proto.generate(13, {"orientation": "identity"}, demos=2, queries=4)
    assert small["train"] == more_queries["train"]
    assert small["test"][0] == more_queries["test"][0]


def test_determinism_freshness_global_rng_and_setting_independence(proto) -> None:
    random.seed(20261026)
    state = random.getstate()
    first = proto.generate(4242, {"orientation": "identity"}, demos=3, queries=4)
    second = proto.generate(4242, {"orientation": "identity"}, demos=3, queries=4)
    rival = proto.generate(4242, {"orientation": "rotate_cw"}, demos=3, queries=4)
    assert first == second
    assert first is not second
    assert _inputs(first) == _inputs(rival)
    assert random.getstate() == state
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
    assert first != second
    assert proto.generate(4242, {"orientation": "identity"}, demos=3, queries=4) == second


def test_transform_is_pure_and_rotate_cw_matches_python_icon_rotation(proto) -> None:
    grid = proto.generate(2, {"orientation": "identity"}, demos=2, queries=1)["train"][0]["input"]
    original = copy.deepcopy(grid)
    identity = proto.transform(grid, {"orientation": "identity"})
    rotated = proto.transform(grid, {"orientation": "rotate_cw"})
    facts = proto.semantic_observables(grid)
    icon = facts["icon"]
    expected_rotated_icon = [[icon[2 - col][row] for col in range(3)] for row in range(3)]
    assert grid == original
    assert identity != rotated
    marker_row, marker_col = facts["markers"][0]
    ro, co = marker_row * 3, marker_col * 3
    assert [row[co : co + 3] for row in rotated[ro : ro + 3]] == expected_rotated_icon


def test_invalid_contracts_fail_closed_without_bool_aliases(proto) -> None:
    for bad in ({}, {"orientation": "identity", "extra": 1}, {"orientation": "flip"}, None):
        with pytest.raises(ValueError):
            proto.program(bad)
    for request in (
        {"demos": 1, "queries": 4},
        {"demos": 7, "queries": 4},
        {"demos": 3, "queries": 0},
        {"demos": 3, "queries": 5},
        {"demos": True, "queries": 4},
        {"demos": 3, "queries": False},
    ):
        with pytest.raises(ValueError):
            proto.generate(0, {"orientation": "identity"}, **request)
    with pytest.raises(ValueError):
        proto.generate(True, {"orientation": "identity"}, demos=3, queries=4)
    with pytest.raises(ValueError):
        proto.generate(0, {"orientation": "flip"}, demos=3, queries=4)


def test_probe_declares_full_two_setting_two_seed_matrix() -> None:
    source = ROOT / f"generators/{TASK_ID}/workspace/parametric/probe.py"
    probe = _load(source, "probe_73f849e69e0a")
    jobs = probe.qualification_jobs()
    assert len(jobs) == 4
    assert {row["seed"] for row in jobs} == {0, 17}
    assert {row["settings"]["orientation"] for row in jobs} == {"identity", "rotate_cw"}
    assert {(row["demos"], row["queries"]) for row in jobs} == {(3, 4)}
