"""Native parametric family regressions for 786a759f780e."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root, load_selected_generator, public_challenge_bytes, public_challenge_id

TASK_ID = "786a759f780e"
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
    return {"train": episode["train"], "test": [{"input": episode["test"][query_index]["input"]}]}


def test_contract_and_default_program_are_exact(adapter):
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"hole_order": ["ascending", "descending"]},
        "default": {"hole_order": "ascending"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/descending.rkt",
            f"generators/{TASK_ID}/workspace/parametric/area_only.rkt",
        ],
    }
    canonical = (HOME / "canonical.rkt").read_text()
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "47d9603ce1b57c3124c98da91980bfa74990a432166bc40a9d1d3ee58a1a2db2"
    )
    assert SOURCE_SHA256 == "e5caaeb59dcbcfd5c9efc45b2d8291e96d7ce8600302237107dd80e8136ce7ba"
    assert adapter.program({"hole_order": "ascending"}) == canonical
    assert adapter.program({"hole_order": "descending"}) == (HOME / "descending.rkt").read_text()
    assert adapter.program({"hole_order": "descending"}) != canonical


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"hole_order": "ascending", "extra": 1},
     {"hole_order": "unknown"}, {"hole_order": True}],
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
        adapter.generate(settings={"hole_order": "ascending"}, **kwargs)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_matched_inputs_and_prefix_stability(adapter, seed):
    small = adapter.generate(seed, {"hole_order": "ascending"}, 2, 1)
    large = adapter.generate(seed, {"hole_order": "ascending"}, 6, 4)
    descending = adapter.generate(seed, {"hole_order": "descending"}, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert [p["input"] for p in large["train"]] == [p["input"] for p in descending["train"]]
    assert [p["input"] for p in large["test"]] == [p["input"] for p in descending["test"]]


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


def test_queries_include_substantive_30_by_30_case(prototype):
    episode = prototype.generate_episode(17, "descending", demos=6, queries=4)
    assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]] == [
        (12, 15), (18, 20), (24, 27), (30, 30)
    ]
    grid = episode["test"][3]["input"]
    analysis = prototype.analyze(grid)
    objects = analysis["objects"]
    assert len(objects) >= 5
    assert {0, 1, 2, 3}.issubset({obj["holes"] for obj in objects})
    assert any(len(obj["colors"]) > 1 for obj in objects)
    assert sum(v != 0 for row in grid for v in row) >= 80
    assert any(grid[0]) and any(grid[-1])
    assert any(row[0] for row in grid) and any(row[-1] for row in grid)
    assert prototype.solve(grid, "ascending") != prototype.solve(grid, "descending")


def test_sorting_consumes_hole_count_intermediate(prototype):
    grid = prototype.sample_input(17, "query", 3)
    analysis = prototype.analyze(grid)
    assert len({obj["holes"] for obj in analysis["objects"]}) >= 4
    ascending = prototype.solve(grid, "ascending")
    wrong = prototype.solve(grid, "area_only")
    assert ascending != wrong
    assert prototype.pack(prototype.sorted_objects(analysis["objects"], "ascending")) == ascending
    assert prototype.pack(prototype.sorted_objects(analysis["objects"], "area_only")) == wrong


def test_public_first_turn_is_masked_and_count_independent(adapter):
    one = adapter.generate(17, {"hole_order": "descending"}, 3, 1)
    four = adapter.generate(17, {"hole_order": "descending"}, 3, 4)
    public_one = _public(one)
    public_four_first = _public(four)
    assert public_challenge_bytes(public_one) == public_challenge_bytes(public_four_first)
    assert public_challenge_id(public_one) == public_challenge_id(public_four_first)
    payload = json.loads(public_challenge_bytes(public_one))
    assert set(payload) == {"train", "test"}
    assert set(payload["test"][0]) == {"input"}
    assert "program_solution" not in payload
    assert "hole_order" not in json.dumps(payload)
