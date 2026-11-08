"""Behavioral contract for the native area-parity / anchor-threshold family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "ea763f9c5b1d"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proto = _load("_test_ea763f9c5b1d_parametric", HOME / "prototype.py")
adapter = _load("_test_ea763f9c5b1d_adapter", HOME / "adapter.py")


def _canonical_row() -> dict:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(TASK_ID)


def _component_cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def test_default_program_is_the_exact_selected_canonical_source():
    expected = _canonical_row()["program_solution"]
    observed = adapter.program({"rule_mode": "area_parity"})
    assert observed == expected
    assert (HOME / "canonical.rkt").read_bytes() == expected.encode("utf-8")
    assert hashlib.sha256(observed.encode()).hexdigest() == hashlib.sha256(expected.encode()).hexdigest()


def test_literal_scene_has_independently_derived_outputs_for_both_rules():
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 6, 0, 0],
        [0, 1, 1, 0, 0, 0, 6, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 6, 6, 0, 0, 6, 6, 0, 0],
        [0, 6, 0, 0, 0, 6, 6, 0, 0],
        [0, 0, 0, 0, 0, 6, 0, 0, 0],
    ]
    expected_parity = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 4, 4, 0, 0, 0, 4, 0, 0],
        [0, 4, 4, 0, 0, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 3, 3, 0, 0, 3, 3, 0, 0],
        [0, 3, 0, 0, 0, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 3, 0, 0, 0],
    ]
    expected_threshold = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 4, 4, 0, 0, 0, 3, 0, 0],
        [0, 4, 4, 0, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 3, 3, 0, 0, 4, 4, 0, 0],
        [0, 3, 0, 0, 0, 4, 4, 0, 0],
        [0, 0, 0, 0, 0, 4, 0, 0, 0],
    ]
    assert proto.solve_python(grid, "area_parity") == expected_parity
    assert proto.solve_python(grid, "anchor_threshold") == expected_threshold
    facts = proto.analyze_scene(grid)
    assert facts["anchor_size"] == 4
    assert sorted(facts["component_sizes"]) == [2, 3, 4, 5]


def test_generation_is_deterministic_prefix_stable_and_setting_matched():
    for seed in (0, 17, 999):
        two = adapter.generate(seed, {"rule_mode": "anchor_threshold"}, 2, 4)
        six = adapter.generate(seed, {"rule_mode": "anchor_threshold"}, 6, 4)
        one_query = adapter.generate(seed, {"rule_mode": "anchor_threshold"}, 2, 1)
        parity = adapter.generate(seed, {"rule_mode": "area_parity"}, 6, 4)
        assert two == adapter.generate(seed, {"rule_mode": "anchor_threshold"}, 2, 4)
        assert two["train"] == six["train"][:2]
        assert two["test"] == six["test"]
        assert one_query["test"] == two["test"][:1]
        assert [p["input"] for p in parity["train"] + parity["test"]] == [
            p["input"] for p in six["train"] + six["test"]
        ]


def test_inputs_are_distinct_valid_and_queries_cover_large_and_boundary_cases():
    episode = adapter.generate(17, {"rule_mode": "anchor_threshold"}, 6, 4)
    all_pairs = episode["train"] + episode["test"]
    keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in all_pairs]
    assert len(keys) == len(set(keys)) == 10
    for pair in all_pairs:
        facts = proto.analyze_scene(pair["input"])
        assert facts["anchor_count"] == 1
        assert 3 <= facts["anchor_size"] <= 7
        assert min(facts["component_sizes"]) < facts["anchor_size"]
        assert max(facts["component_sizes"]) > facts["anchor_size"]
        assert facts["component_sizes"].count(facts["anchor_size"]) >= 2
        assert pair["output"] == proto.solve_python(pair["input"], "anchor_threshold")
    sizes = [(len(p["input"]), len(p["input"][0])) for p in episode["test"]]
    assert sizes[-1] == (30, 30)
    large = proto.analyze_scene(episode["test"][-1]["input"])
    assert len(large["component_sizes"]) >= 12
    assert large["occupied_rows"] >= 24
    assert large["occupied_cols"] >= 24
    assert any(
        r in (0, 29) or c in (0, 29)
        for r, c in large["all_cells"]
    )


def test_minimum_two_demos_reject_every_declared_shortcut_for_both_settings():
    for seed in range(20):
        for mode in proto.RULE_MODES:
            episode = adapter.generate(seed, {"rule_mode": mode}, 2, 4)
            intended = [pair["output"] for pair in episode["train"]]
            for name, solver in proto.declared_rivals(mode).items():
                rival = [solver(pair["input"]) for pair in episode["train"]]
                assert rival != intended, (seed, mode, name)


def test_public_first_turn_is_query_count_neutral_and_private_fields_are_ignored():
    setting = {"rule_mode": "anchor_threshold"}
    one = adapter.generate(17, setting, 3, 1)
    four = adapter.generate(17, setting, 3, 4)
    first_from_four = {"train": four["train"], "test": [four["test"][0]]}
    assert public_challenge_bytes(one) == public_challenge_bytes(first_from_four)
    changed = copy.deepcopy(first_from_four)
    changed["settings"] = {"rule_mode": "area_parity"}
    changed["program_solution"] = "private mutation"
    changed["test"][0]["output"] = [[9]]
    changed["future_queries"] = four["test"][1:]
    assert public_challenge_bytes(changed) == public_challenge_bytes(first_from_four)


@pytest.mark.parametrize(
    "bad_settings",
    [None, {}, {"rule_mode": "bad"}, {"rule_mode": "area_parity", "extra": 1}],
)
def test_invalid_settings_are_rejected(bad_settings):
    with pytest.raises(ValueError):
        adapter.program(bad_settings)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(-1, 2, 1), (2**63, 2, 1), (0, 1, 1), (0, 7, 1), (0, 2, 0), (0, 2, 5), (True, 2, 1)],
)
def test_invalid_request_bounds_are_rejected(seed, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(seed, {"rule_mode": "area_parity"}, demos, queries)
