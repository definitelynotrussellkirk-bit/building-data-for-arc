"""Native promotion contract for local-frame direct/running-parity readout."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "2fb0197be694"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = HOME / "adapter.py"
PROMOTION_PATH = HOME / "promotion.json"


def _load(path: Path, stem: str):
    assert path.is_file(), f"missing native artifact: {path.relative_to(ROOT)}"
    name = f"_{stem}_{TASK_ID}_{path.stat().st_mtime_ns}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    ledger = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task row missing")


def _serialized_inputs(episode: dict) -> list[str]:
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in episode["train"] + episode["test"]
    ]


def test_contract_has_two_exact_settings_and_preserves_canonical_program():
    contract = json.loads(PROMOTION_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"encoding": ["direct", "running_parity"]},
        "default": {"encoding": "direct"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt"
        ],
    }

    adapter = _load(ADAPTER_PATH, "native_adapter_contract")
    direct = adapter.program({"encoding": "direct"})
    parity = adapter.program({"encoding": "running_parity"})
    assert direct == _canonical_program()
    assert parity.startswith("(rule! ")
    assert parity != direct
    assert adapter.program({"encoding": "running_parity"}) == parity


def test_constructive_two_demo_lesson_has_literal_expected_outputs():
    adapter = _load(ADAPTER_PATH, "native_adapter_lesson")
    direct = adapter.generate(17, {"encoding": "direct"}, 2, 4)
    parity = adapter.generate(17, {"encoding": "running_parity"}, 2, 4)

    assert [pair["output"] for pair in direct["train"]] == [
        [[8, 0, 0, 0]],
        [[0, 8, 8, 0]],
    ]
    assert [pair["output"] for pair in parity["train"]] == [
        [[8, 8, 8, 8]],
        [[0, 8, 0, 0]],
    ]
    assert [pair["input"] for pair in direct["train"] + direct["test"]] == [
        pair["input"] for pair in parity["train"] + parity["test"]
    ]


def test_generation_supports_independent_counts_distinct_inputs_and_real_stress():
    adapter = _load(ADAPTER_PATH, "native_adapter_stress")
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = adapter.generate(
                41,
                {"encoding": "running_parity"},
                demos,
                queries,
            )
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == queries
            inputs = _serialized_inputs(episode)
            assert len(inputs) == len(set(inputs)) == demos + queries
            assert episode["program_solution"] == adapter.program(
                {"encoding": "running_parity"}
            )

    full = adapter.generate(41, {"encoding": "direct"}, 6, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in full["test"]]
    assert shapes == [(11, 17), (21, 29), (30, 30), (6, 16)]

    stress = full["test"][2]["input"]
    nonzero = [(r, c, value) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    distractors = [(r, c, value) for r, c, value in nonzero if value in {1, 5, 6, 7, 9}]
    assert len(distractors) >= 250
    assert {value for _, _, value in distractors} == {1, 5, 6, 7, 9}
    assert any(r == 0 for r, _, _ in distractors)
    assert any(r == 29 for r, _, _ in distractors)
    assert any(c == 0 for _, c, _ in distractors)
    assert any(c == 29 for _, c, _ in distractors)

    boundary = full["test"][3]["input"]
    target_cells = [
        (r, c)
        for r, row in enumerate(boundary)
        for c, value in enumerate(row)
        if value in {2, 3, 4, 8}
    ]
    assert any(r in {0, len(boundary) - 1} or c in {0, len(boundary[0]) - 1} for r, c in target_cells)


def test_settings_counts_seed_and_public_projection_are_strict():
    adapter = _load(ADAPTER_PATH, "native_adapter_validation")
    valid = {"encoding": "direct"}

    for invalid in (
        {},
        {"encoding": "unknown"},
        {"encoding": False},
        {"encoding": "direct", "extra": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(invalid)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, invalid, 2, 4)

    for seed in (-1, True, 1.5, "0"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, valid, 2, 4)
    for demos, queries in ((1, 4), (7, 4), (2, 0), (2, 5), (True, 4), (2, False)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, valid, demos, queries)

    episode = adapter.generate(0, valid, 2, 4)
    raw = public_challenge_bytes(episode)
    visible = json.loads(raw)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert public_challenge_id(episode) == __import__("hashlib").sha256(raw).hexdigest()
    assert b"encoding" not in raw and b"rule!" not in raw and b"running_parity" not in raw


def test_first_query_prefix_is_identical_for_single_and_four_query_use():
    adapter = _load(ADAPTER_PATH, "native_adapter_prefix")
    settings = {"encoding": "running_parity"}
    single = adapter.generate(99, settings, 3, 1)
    full = adapter.generate(99, settings, 3, 4)
    assert single["train"] == full["train"]
    assert single["test"][0] == full["test"][0]
