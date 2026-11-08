"""Promotion-adapter regressions for the retained mark-action prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random
import sys
import types

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "2b34f380ed25"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CONTRACT_PATH = PARAMETRIC / "promotion.json"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"


def load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_path("mark_action_promotion_prototype_test", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return load_path("mark_action_promotion_adapter_test", ADAPTER_PATH)


def canonical_program() -> str:
    with canonical_path(ROOT).open() as handle:
        rows = [json.loads(line) for line in handle]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return programs.pop()


def visible_inputs(episode: dict) -> list:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_contract_and_program_boundary_are_promotion_ready(adapter):
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/2b34f380ed25/workspace/parametric/adapter.py",
        "parameters": {"mark_action": ["half_swap", "reflection"]},
        "default": {"mark_action": "half_swap"},
        "limits": {"demos": [3, 8], "queries": [1, 8]},
    }
    assert adapter.program({"mark_action": "half_swap"}) == canonical_program()
    alternate = adapter.program({"mark_action": "reflection"})
    assert alternate != canonical_program()
    assert alternate.count("(reverse rights)") == 1
    assert alternate.count("(reverse bots)") == 1


def test_adapter_loads_its_adjacent_prototype_not_cached_module(monkeypatch):
    poison = types.ModuleType("prototype")
    poison.program_for = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("cached prototype module was used")
    )
    monkeypatch.setitem(sys.modules, "prototype", poison)
    isolated = load_path("mark_action_promotion_adapter_isolation_test", ADAPTER_PATH)
    assert isolated.program({"mark_action": "half_swap"}) == canonical_program()


def test_generation_is_matched_deterministic_distinct_and_count_independent(adapter):
    settings = {"mark_action": "half_swap"}
    first = adapter.generate(17, settings, 3, 4)
    same = adapter.generate(17, settings, 3, 4)
    assert first == same
    assert (len(first["train"]), len(first["test"])) == (3, 4)
    assert first["program_solution"] == adapter.program(settings)
    keys = [json.dumps(grid, separators=(",", ":")) for grid in visible_inputs(first)]
    assert len(keys) == len(set(keys)) == 7

    more_demos = adapter.generate(17, settings, 8, 1)
    more_queries = adapter.generate(17, settings, 3, 8)
    assert more_demos["train"][:3] == first["train"]
    assert more_demos["test"] == first["test"][:1]
    assert more_queries["train"] == first["train"]
    assert more_queries["test"][:4] == first["test"]
    max_inputs = visible_inputs(adapter.generate(17, settings, 8, 8))
    assert len({json.dumps(grid, separators=(",", ":")) for grid in max_inputs}) == 16

    changed = adapter.generate(18, settings, 3, 4)
    assert visible_inputs(changed) != visible_inputs(first)


def test_setting_changes_labels_not_inputs_and_demos_identify_it(adapter):
    half = adapter.generate(0, {"mark_action": "half_swap"}, 3, 4)
    reflection = adapter.generate(0, {"mark_action": "reflection"}, 3, 4)
    assert visible_inputs(half) == visible_inputs(reflection)
    assert half["program_solution"] != reflection["program_solution"]
    demo_disagreements = [
        index for index, (left, right) in enumerate(zip(half["train"], reflection["train"]))
        if left["output"] != right["output"]
    ]
    query_disagreements = [
        index for index, (left, right) in enumerate(zip(half["test"], reflection["test"]))
        if left["output"] != right["output"]
    ]
    assert demo_disagreements[:2] == [0, 1]
    assert query_disagreements == [0, 1, 2, 3]


def test_all_promotion_labels_match_real_racket(adapter, prototype):
    prototype.ensure_tools()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=30) as bridge:
        for setting in ("half_swap", "reflection"):
            episode = adapter.generate(17, {"mark_action": setting}, 3, 4)
            program = adapter.program({"mark_action": setting})
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.execute(bridge, program, pair["input"])


def test_invalid_typed_controls_fail_before_sampling(adapter):
    good = {"mark_action": "half_swap"}
    bad_calls = [
        (17, {}, 3, 4),
        (17, {"mark_action": "half_swap", "extra": 0}, 3, 4),
        (17, {"mark_action": "flip"}, 3, 4),
        (True, good, 3, 4),
        (-1, good, 3, 4),
        (17, good, 2, 4),
        (17, good, 9, 4),
        (17, good, True, 4),
        (17, good, 3, 0),
        (17, good, 3, 9),
        (17, good, 3, 4.0),
    ]
    state = random.getstate()
    for args in bad_calls:
        with pytest.raises(ValueError):
            adapter.generate(*args)
    assert random.getstate() == state
