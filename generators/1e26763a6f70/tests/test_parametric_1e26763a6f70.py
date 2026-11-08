"""Native parametric family regressions for 1e26763a6f70."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root, load_selected_generator, public_challenge_bytes, public_challenge_id

TASK_ID = "1e26763a6f70"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = HOME / f"{name}.py"
    module_name = f"_arc_{TASK_ID}_{name}_{hashlib.sha256(str(path).encode()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load("prototype")


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter")


def _public(episode, query_index=0):
    return {
        "train": episode["train"],
        "test": [{"input": episode["test"][query_index]["input"]}],
    }


def test_contract_and_default_program_are_exact(adapter):
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"pair_selection": ["all_pairs", "longest_pairs"]},
        "default": {"pair_selection": "all_pairs"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/longest_pairs.rkt",
            f"generators/{TASK_ID}/workspace/parametric/shortest_pairs.rkt",
        ],
    }
    canonical = (HOME / "canonical.rkt").read_text()
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "dffe1ada016820c3d6ece8ab0b99b01883ec1265e24bd9c223ffa4d1ac92a5a7"
    )
    assert adapter.program({"pair_selection": "all_pairs"}) == canonical
    assert adapter.program({"pair_selection": "longest_pairs"}) == (
        HOME / "longest_pairs.rkt"
    ).read_text()
    assert adapter.program({"pair_selection": "longest_pairs"}) != canonical


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"pair_selection": "all_pairs", "extra": 1},
        {"pair_selection": "unknown"},
        {"pair_selection": True},
    ],
)
def test_invalid_settings_are_rejected(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": -1, "demos": 3, "queries": 4},
        {"seed": True, "demos": 3, "queries": 4},
        {"seed": 0, "demos": 1, "queries": 4},
        {"seed": 0, "demos": 7, "queries": 4},
        {"seed": 0, "demos": 3, "queries": 0},
        {"seed": 0, "demos": 3, "queries": 5},
    ],
)
def test_invalid_counts_and_seed_are_rejected(adapter, kwargs):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(settings={"pair_selection": "all_pairs"}, **kwargs)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_matched_inputs_and_prefix_stability(adapter, seed):
    all_small = adapter.generate(seed, {"pair_selection": "all_pairs"}, 2, 1)
    all_large = adapter.generate(seed, {"pair_selection": "all_pairs"}, 6, 4)
    longest = adapter.generate(seed, {"pair_selection": "longest_pairs"}, 6, 4)

    assert all_small["train"] == all_large["train"][:2]
    assert all_small["test"] == all_large["test"][:1]
    assert [p["input"] for p in all_large["train"]] == [p["input"] for p in longest["train"]]
    assert [p["input"] for p in all_large["test"]] == [p["input"] for p in longest["test"]]
    assert all_small["program_solution"] == adapter.program({"pair_selection": "all_pairs"})
    assert longest["program_solution"] == adapter.program({"pair_selection": "longest_pairs"})


def test_first_two_demos_identify_each_setting_and_declared_rivals(prototype):
    for seed in (0, 17, 12345):
        for setting in prototype.SETTING_NAMES:
            episode = prototype.generate_episode(seed, setting, demos=2, queries=4)
            assert prototype.teaching_survivors(episode["train"]) == [setting]


def test_claims_match_python_mirror_and_inputs_are_distinct(prototype):
    for seed in (0, 17):
        for setting in prototype.SETTING_NAMES:
            episode = prototype.generate_episode(seed, setting, demos=6, queries=4)
            pairs = episode["train"] + episode["test"]
            assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in pairs}) == 10
            for pair in pairs:
                assert pair["output"] == prototype.solve(pair["input"], setting)


def test_query_profiles_include_substantive_30_by_30_case(prototype):
    episode = prototype.generate_episode(17, "longest_pairs", demos=6, queries=4)
    assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]] == [
        (12, 15),
        (18, 20),
        (24, 27),
        (30, 30),
    ]
    grid = episode["test"][3]["input"]
    analysis = prototype.analyze(grid)
    assert len(analysis["eligible_pairs"]) >= 7
    assert {pair["orientation"] for pair in analysis["eligible_pairs"]} == {
        "horizontal",
        "vertical",
    }
    assert len({pair["span"] for pair in analysis["eligible_pairs"]}) >= 4
    assert sum(cell != 0 for row in grid for cell in row) >= 100
    assert any(grid[0]) and any(grid[-1])
    assert any(row[0] for row in grid) and any(row[-1] for row in grid)
    changed = sum(
        before != after
        for row_a, row_b in zip(grid, episode["test"][3]["output"], strict=True)
        for before, after in zip(row_a, row_b, strict=True)
    )
    assert changed >= 2


def test_longest_selection_consumes_derived_span_intermediate(prototype):
    grid = prototype.sample_input(17, "query", 3)
    analysis = prototype.analyze(grid)
    spans = [pair["span"] for pair in analysis["eligible_pairs"]]
    assert len(set(spans)) >= 4
    expected = prototype.solve(grid, "longest_pairs")
    wrong = prototype.solve(grid, "shortest_pairs")
    assert expected != wrong
    assert {pair["span"] for pair in prototype.selected_pairs(analysis, "longest_pairs")} == {max(spans)}
    assert {pair["span"] for pair in prototype.selected_pairs(analysis, "shortest_pairs")} == {min(spans)}


def test_public_first_turn_is_masked_and_count_independent(adapter):
    one = adapter.generate(17, {"pair_selection": "longest_pairs"}, 3, 1)
    four = adapter.generate(17, {"pair_selection": "longest_pairs"}, 3, 4)
    public_one = _public(one)
    public_four_first = _public(four)
    assert public_challenge_bytes(public_one) == public_challenge_bytes(public_four_first)
    assert public_challenge_id(public_one) == public_challenge_id(public_four_first)
    payload = json.loads(public_challenge_bytes(public_one))
    assert set(payload) == {"train", "test"}
    assert set(payload["test"][0]) == {"input"}
    assert "program_solution" not in payload
    assert "pair_selection" not in json.dumps(payload)
