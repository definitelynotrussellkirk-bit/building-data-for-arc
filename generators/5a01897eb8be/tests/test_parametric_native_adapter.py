"""Native promotion contract for the corner-ring parameter family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "5a01897eb8be"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}/workspace/parametric"
ADAPTER = HOME / "adapter.py"
PROMOTION = HOME / "promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing native source: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load(ADAPTER, "native_corner_rings_5a01897eb8be")


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return programs.pop()


def test_native_contract_declares_bounded_four_query_family():
    contract = json.loads(PROMOTION.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {
            "ring_step": [2, 4],
            "corners": ["all", "diagonal"],
        },
        "default": {"ring_step": 2, "corners": "all"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
    }


def test_native_default_program_is_exact_canonical(adapter):
    assert adapter.program({"ring_step": 2, "corners": "all"}) == _canonical_program()


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"ring_step": 2},
        {"corners": "all"},
        {"ring_step": 2, "corners": "all", "extra": 1},
        {"ring_step": True, "corners": "all"},
        {"ring_step": 3, "corners": "all"},
        {"ring_step": 2, "corners": "four"},
    ],
)
def test_native_adapter_rejects_undeclared_settings(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


def test_native_generate_projects_private_query_labels(adapter):
    settings = {"ring_step": 4, "corners": "diagonal"}
    episode = adapter.generate(17, settings, demos=3, queries=4)
    assert set(episode) == {"train", "test", "program_solution"}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(settings)
    assert all(set(pair) == {"input", "output"} for pair in episode["train"])
    assert all(set(pair) == {"input", "output"} for pair in episode["test"])
    fingerprints = {
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    }
    assert len(fingerprints) == 7


def test_native_generate_uses_claim_labels_without_starting_racket(adapter, monkeypatch):
    """Qualification owns protected execution; adapter generation stays pure."""

    class ForbiddenBridge:
        def __init__(self, *args, **kwargs):
            raise AssertionError("native adapter must not start an embedded Racket bridge")

    monkeypatch.setattr(adapter._PROTOTYPE, "RacketBridge", ForbiddenBridge)
    settings = {"ring_step": 4, "corners": "diagonal"}
    episode = adapter.generate(41, settings, demos=2, queries=4)

    for split in ("train", "test"):
        for pair in episode[split]:
            assert pair["output"] == adapter._PROTOTYPE.python_transform(
                pair["input"], 4, "diagonal"
            )


def test_native_inputs_are_setting_neutral_and_queries_are_demo_count_stable(adapter):
    def inputs(episode, split):
        return [pair["input"] for pair in episode[split]]

    settings = [
        {"ring_step": step, "corners": corners}
        for step in (2, 4)
        for corners in ("all", "diagonal")
    ]
    episodes = [adapter.generate(29, setting, demos=3, queries=4) for setting in settings]
    baseline = episodes[0]
    assert all(inputs(episode, "train") == inputs(baseline, "train") for episode in episodes[1:])
    assert all(inputs(episode, "test") == inputs(baseline, "test") for episode in episodes[1:])

    two_demo = adapter.generate(29, settings[0], demos=2, queries=4)
    six_demo = adapter.generate(29, settings[0], demos=6, queries=4)
    assert inputs(two_demo, "test") == inputs(six_demo, "test") == inputs(baseline, "test")
