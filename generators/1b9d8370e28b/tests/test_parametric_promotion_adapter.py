"""Native-promotion contract tests for the cyan-anchor prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import types
from uuid import uuid4

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root


ROOT = find_root(__file__)
HOME = ROOT / "generators/1b9d8370e28b/workspace/parametric"
ADAPTER_PATH = HOME / "adapter.py"
CONTRACT_PATH = HOME / "promotion.json"
PROTOTYPE_PATH = HOME / "prototype.py"
TASK_ID = "1b9d8370e28b"


def _load(path: Path, prefix: str):
    assert path.is_file(), f"missing required promotion source: {path.name}"
    name = f"{prefix}_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _contract() -> dict:
    assert CONTRACT_PATH.is_file(), "missing native promotion contract"
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _pairs(episode: dict) -> list[dict]:
    return episode["train"] + episode["test"]


def test_contract_declares_bounded_native_adapter():
    contract = _contract()
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/1b9d8370e28b/workspace/parametric/adapter.py",
        "parameters": {"cyan_anchor": ["left", "right"]},
        "default": {"cyan_anchor": "left"},
        "limits": {"demos": [1, 32], "queries": [1, 32]},
        "resources": ["generators/1b9d8370e28b/workspace/parametric/prototype.py"],
    }


def test_program_reuses_exact_canonical_and_guarded_variant():
    adapter = _load(ADAPTER_PATH, "cyan_anchor_adapter")
    prototype = _load(PROTOTYPE_PATH, "cyan_anchor_prototype")

    left = adapter.program({"cyan_anchor": "left"})
    right = adapter.program({"cyan_anchor": "right"})

    assert left == prototype.canonical_source(root=ROOT)
    assert right == prototype.materialize_rule("right", root=ROOT)
    assert right != left


def test_generate_supports_independent_counts_and_matched_inputs():
    adapter = _load(ADAPTER_PATH, "cyan_anchor_adapter")
    left = adapter.generate(41, {"cyan_anchor": "left"}, demos=3, queries=4)
    right = adapter.generate(41, {"cyan_anchor": "right"}, demos=3, queries=4)

    assert len(left["train"]) == len(right["train"]) == 3
    assert len(left["test"]) == len(right["test"]) == 4
    assert left["program_solution"] == adapter.program({"cyan_anchor": "left"})
    assert right["program_solution"] == adapter.program({"cyan_anchor": "right"})

    left_pairs, right_pairs = _pairs(left), _pairs(right)
    assert [pair["input"] for pair in left_pairs] == [pair["input"] for pair in right_pairs]
    assert all(a["output"] != b["output"] for a, b in zip(left_pairs, right_pairs))
    assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in left_pairs}) == 7


def test_generate_supports_distinct_32_demo_32_query_boundary():
    adapter = _load(ADAPTER_PATH, "cyan_anchor_adapter")
    episode = adapter.generate(2**31 + 9, {"cyan_anchor": "right"}, demos=32, queries=32)
    pairs = _pairs(episode)
    assert len(episode["train"]) == 32
    assert len(episode["test"]) == 32
    assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in pairs}) == 64


@pytest.mark.parametrize(
    ("seed", "settings", "demos", "queries"),
    [
        (True, {"cyan_anchor": "left"}, 3, 4),
        (-1, {"cyan_anchor": "left"}, 3, 4),
        (2**63, {"cyan_anchor": "left"}, 3, 4),
        (0, {"cyan_anchor": "left"}, True, 4),
        (0, {"cyan_anchor": "left"}, 0, 4),
        (0, {"cyan_anchor": "left"}, 3, 33),
        (0, {"cyan_anchor": "up"}, 3, 4),
        (0, {"cyan_anchor": "left", "extra": 1}, 3, 4),
        (0, None, 3, 4),
    ],
)
def test_adapter_rejects_malformed_requests(seed, settings, demos, queries):
    adapter = _load(ADAPTER_PATH, "cyan_anchor_adapter")
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, settings, demos, queries)


@pytest.mark.parametrize(
    "settings",
    [
        {"cyan_anchor": "up"},
        {"cyan_anchor": "left", "extra": True},
        {},
        None,
    ],
)
def test_program_rejects_undeclared_settings(settings):
    adapter = _load(ADAPTER_PATH, "cyan_anchor_adapter")
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


def test_adapter_ignores_unrelated_cached_prototype_module(monkeypatch):
    fake = types.ModuleType("prototype")
    fake.materialize_rule = lambda *_args, **_kwargs: "wrong cached module"
    monkeypatch.setitem(sys.modules, "prototype", fake)
    adapter = _load(ADAPTER_PATH, "cyan_anchor_adapter")
    assert adapter.program({"cyan_anchor": "left"}).startswith("(rule! ")
    assert adapter.program({"cyan_anchor": "left"}) != "wrong cached module"


def test_native_worker_finds_only_selected_setting_from_demonstrations():
    contract = _contract()
    adapter = _load(ADAPTER_PATH, "cyan_anchor_adapter")
    prototype = _load(PROTOTYPE_PATH, "cyan_anchor_prototype")
    settings = [{"cyan_anchor": "left"}, {"cyan_anchor": "right"}]
    programs = {adapter.program(setting): setting["cyan_anchor"] for setting in settings}

    def apply_program(program, grid):
        return prototype.apply_rule(deepcopy(grid), programs[program])

    jobs = [
        {"seed": 0, "settings": setting, "demos": 3, "queries": 4}
        for setting in settings
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs, apply_program=apply_program)
    assert [row["survivors"] for row in result["checks"]] == [[settings[0]], [settings[1]]]
    assert all(row["label_count"] == 7 for row in result["checks"])


def test_generate_retries_duplicate_inputs_deterministically(monkeypatch):
    adapter = _load(ADAPTER_PATH, "cyan_anchor_adapter")
    original = adapter._PROTOTYPE.build_input
    samples = [original(7, index) for index in range(3)]
    scripted = [samples[0], samples[0], samples[1], samples[2]]
    calls: list[int] = []

    def duplicate_then_unique(seed, pair_index):
        assert seed == 7
        calls.append(pair_index)
        return deepcopy(scripted[pair_index])

    monkeypatch.setattr(adapter._PROTOTYPE, "build_input", duplicate_then_unique)
    episode = adapter.generate(7, {"cyan_anchor": "left"}, demos=2, queries=1)
    assert calls == [0, 1, 2, 3]
    assert [pair["input"] for pair in _pairs(episode)] == samples
