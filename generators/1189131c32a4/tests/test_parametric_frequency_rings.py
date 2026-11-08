"""Focused tests for the proposed frequency-ring parameter family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "1189131c32a4"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}/workspace/parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"
PROMOTION_PATH = HOME / "promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing requested artifact: {path}"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def prototype():
    return _load(PROTOTYPE_PATH, "_test_1189131c32a4_frequency_rings")


def adapter():
    return _load(ADAPTER_PATH, "_test_1189131c32a4_frequency_adapter")


def canonical_source() -> str:
    sources = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(sources) == 1
    return sources.pop()


def frozen_grid(grid):
    return tuple(tuple(row) for row in grid)


def episode_inputs(episode):
    return [frozen_grid(pair["input"]) for pair in episode["train"] + episode["test"]]


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(max_calls_before_restart=256) as runtime:
        yield runtime


def test_default_program_is_exact_canonical_and_all_four_programs_are_distinct():
    module = prototype()
    canonical = canonical_source()
    assert module.CANONICAL_SOURCE_SHA256 == hashlib.sha256(canonical.encode()).hexdigest()
    assert module.program(module.DEFAULT_SETTINGS, root=ROOT) == canonical

    programs = {
        module.settings_key(settings): module.program(settings, root=ROOT)
        for settings in module.ALL_SETTINGS
    }
    assert len(programs) == 4
    assert len(set(programs.values())) == 4
    assert module.DEFAULT_SETTINGS in module.ALL_SETTINGS


def test_promotion_contract_is_bounded_and_adapter_is_thin():
    module = prototype()
    promoted = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert promoted == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {
            "frequency_order": list(module.FREQUENCY_ORDERS),
            "tie_break": list(module.TIE_BREAKS),
        },
        "default": module.DEFAULT_SETTINGS,
        "limits": {"demos": [2, 8], "queries": [1, 8]},
        "resources": [f"generators/{TASK_ID}/workspace/parametric/prototype.py"],
    }
    promoted_adapter = adapter()
    for settings in module.ALL_SETTINGS:
        assert promoted_adapter.program(settings) == module.program(settings, root=ROOT)


def test_same_seed_uses_identical_inputs_and_every_demo_identifies_all_parameters():
    module = prototype()
    promoted_adapter = adapter()
    episodes = [
        promoted_adapter.generate(17, settings, demos=3, queries=4)
        for settings in module.ALL_SETTINGS
    ]
    inputs = [episode_inputs(episode) for episode in episodes]
    assert all(value == inputs[0] for value in inputs)
    assert len(inputs[0]) == len(set(inputs[0])) == 7

    for settings, episode in zip(module.ALL_SETTINGS, episodes, strict=True):
        assert episode["settings"] == settings
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == module.program(settings, root=ROOT)
        assert module.fit_settings(episode["train"]) == [settings]
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == module.transform(pair["input"], settings)

    for pair_index in range(7):
        split = "train" if pair_index < 3 else "test"
        index = pair_index if split == "train" else pair_index - 3
        outputs = {
            frozen_grid(episode[split][index]["output"])
            for episode in episodes
        }
        assert len(outputs) == 4


def test_demo_and_query_counts_are_independent_prefixes():
    module = prototype()
    promoted_adapter = adapter()
    full = promoted_adapter.generate(29, module.DEFAULT_SETTINGS, demos=8, queries=8)
    small = promoted_adapter.generate(29, module.DEFAULT_SETTINGS, demos=2, queries=1)
    medium = promoted_adapter.generate(29, module.DEFAULT_SETTINGS, demos=5, queries=4)
    assert episode_inputs(small)[:2] == episode_inputs(full)[:2]
    assert [frozen_grid(pair["input"]) for pair in small["test"]] == [
        frozen_grid(full["test"][0]["input"])
    ]
    assert [frozen_grid(pair["input"]) for pair in medium["train"]] == [
        frozen_grid(pair["input"]) for pair in full["train"][:5]
    ]
    assert [frozen_grid(pair["input"]) for pair in medium["test"]] == [
        frozen_grid(pair["input"]) for pair in full["test"][:4]
    ]


def test_default_racket_program_reproduces_every_canonical_pair(bridge):
    module = prototype()
    source = module.program(module.DEFAULT_SETTINGS, root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert module.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_every_setting_and_every_episode_label_executes_in_racket(bridge):
    module = prototype()
    promoted_adapter = adapter()
    for settings in module.ALL_SETTINGS:
        episode = promoted_adapter.generate(31, settings, demos=2, queries=4)
        report = module.verify_episode(episode, bridge=bridge)
        assert report["settings"] == settings
        assert report["label_count"] == 6
        assert report["surviving_settings"] == [settings]
        assert report["all_query_predictions_distinct"] is True
        assert all(row["matches_python"] for row in report["program_checks"])


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"frequency_order": "most_outside", "tie_break": "descending_numeric"}, 2, 1),
        (-1, {"frequency_order": "most_outside", "tie_break": "descending_numeric"}, 2, 1),
        (2**63, {"frequency_order": "most_outside", "tie_break": "descending_numeric"}, 2, 1),
        (0, {"frequency_order": "most_outside", "tie_break": "descending_numeric"}, 1, 1),
        (0, {"frequency_order": "most_outside", "tie_break": "descending_numeric"}, 9, 1),
        (0, {"frequency_order": "most_outside", "tie_break": "descending_numeric"}, 2, 0),
        (0, {"frequency_order": "most_outside", "tie_break": "descending_numeric"}, 2, 9),
        (0, {"frequency_order": "sideways", "tie_break": "descending_numeric"}, 2, 1),
        (0, {"frequency_order": "most_outside", "tie_break": "random"}, 2, 1),
        (0, {"frequency_order": "most_outside"}, 2, 1),
        (0, {"frequency_order": "most_outside", "tie_break": "descending_numeric", "extra": 1}, 2, 1),
    ],
)
def test_adapter_rejects_invalid_requests(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)
