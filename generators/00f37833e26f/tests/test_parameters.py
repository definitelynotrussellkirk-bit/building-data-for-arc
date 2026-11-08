"""Focused contract tests for residual-component selection after subtraction."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator, public_challenge_bytes

TASK_ID = "00f37833e26f"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
POLICIES = ("all", "largest_component")


def _load(filename: str, suffix: str):
    path = HOME / filename
    assert path.is_file(), f"missing native source: {path}"
    name = f"_test_{TASK_ID}_{suffix}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_base_generator_supports_required_ordinary_draws():
    generator, _path, _digest = load_selected_generator(TASK_ID, root=ROOT)
    for difficulty, seed in ((None, 17), ("medium", 43)):
        grid = generator.generate(seed, 0, difficulty=difficulty)
        assert generator.self_check(grid, difficulty=difficulty, meta=None) == []


def test_contract_and_exact_canonical_default():
    adapter = _load("adapter.py", "adapter")
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"residual_policy": list(POLICIES)},
        "default": {"residual_policy": "all"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/largest_component.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/wrong_intermediate.rkt",
            f"generators/{TASK_ID}/workspace/parametric/audit.py",
        ],
    }
    assert adapter.program({"residual_policy": "all"}) == _canonical_program()
    assert (HOME / "rules" / "canonical.rkt").read_text() == _canonical_program()
    assert adapter.program({"residual_policy": "largest_component"}) != _canonical_program()


@pytest.mark.parametrize("settings", [None, {}, {"residual_policy": True}, {"residual_policy": "smallest"}, {"residual_policy": "all", "extra": 1}])
def test_invalid_settings_reject(settings):
    adapter = _load("adapter.py", "adapter_invalid")
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, demos=3, queries=4)


@pytest.mark.parametrize("policy", POLICIES)
def test_counts_are_prefix_stable_copy_isolated_and_setting_neutral(policy):
    adapter = _load("adapter.py", f"adapter_counts_{policy}")
    full = adapter.generate(91, {"residual_policy": policy}, demos=6, queries=4)
    replay = adapter.generate(91, {"residual_policy": policy}, demos=6, queries=4)
    assert full == replay
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = adapter.generate(91, {"residual_policy": policy}, demos=demos, queries=queries)
            assert episode["train"] == full["train"][:demos]
            assert episode["test"] == full["test"][:queries]
    full["train"][0]["input"][0][0] = 9
    assert adapter.generate(91, {"residual_policy": policy}, 6, 4)["train"][0]["input"][0][0] != 9

    other = "largest_component" if policy == "all" else "all"
    matched = adapter.generate(91, {"residual_policy": other}, 6, 4)
    assert _inputs(adapter.generate(91, {"residual_policy": policy}, 6, 4)) == _inputs(matched)


@pytest.mark.parametrize("seed", [0, 17, 100, 211])
@pytest.mark.parametrize("policy", POLICIES)
def test_two_demonstrations_identify_setting_and_refute_named_rivals(seed, policy):
    prototype = _load("prototype.py", f"prototype_teach_{seed}_{policy}")
    adapter = _load("adapter.py", f"adapter_teach_{seed}_{policy}")
    episode = adapter.generate(seed, {"residual_policy": policy}, demos=2, queries=4)
    survivors = [
        candidate
        for candidate in POLICIES
        if all(prototype.solve_python(pair["input"], candidate) == pair["output"] for pair in episode["train"])
    ]
    assert survivors == [policy]
    certificate = prototype.teaching_check(episode, policy)
    assert certificate["demo_survivors"] == []
    assert certificate["harmful_survivors"] == []


def test_fourth_query_is_substantive_30x30_and_has_unique_largest_residual():
    prototype = _load("prototype.py", "prototype_stress")
    adapter = _load("adapter.py", "adapter_stress")
    pair = adapter.generate(20261025, {"residual_policy": "largest_component"}, 3, 4)["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    analysis = prototype.analyze(grid)
    assert analysis["foreground_cells"] >= 120
    assert len(analysis["residual_components"]) >= 5
    sizes = analysis["residual_component_sizes"]
    assert sizes.count(max(sizes)) == 1
    assert prototype.solve_python(grid, "all") != prototype.solve_python(grid, "largest_component")


def test_public_turn_masks_private_fields_and_is_first_turn_stable():
    adapter = _load("adapter.py", "adapter_public")
    one = adapter.generate(33, {"residual_policy": "largest_component"}, 3, 1)
    four = adapter.generate(33, {"residual_policy": "largest_component"}, 3, 4)
    public = adapter.public_turn(four, 0)
    assert public == {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    assert public_challenge_bytes(one) == public_challenge_bytes(public)
    text = json.dumps(public, sort_keys=True)
    assert "residual_policy" not in text and "program_solution" not in text


def test_dependency_trace_requires_subtraction_before_component_selection():
    prototype = _load("prototype.py", "prototype_dependency")
    adapter = _load("adapter.py", "adapter_dependency")
    grid = adapter.generate(1701, {"residual_policy": "largest_component"}, 2, 4)["test"][0]["input"]
    trace = prototype.dependency_trace(grid)
    assert trace["step_a"] == "normalize the green source and gray mask, then subtract the mask"
    assert trace["intermediate_value"] == prototype.analyze(grid)["residual_cells"]
    assert trace["output"] == prototype.solve_python(grid, "largest_component")
    assert trace["wrong_intermediate_output"] != trace["output"]


def test_racket_programs_match_python_on_a_distinguishing_pair():
    prototype = _load("prototype.py", "prototype_racket")
    adapter = _load("adapter.py", "adapter_racket")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    grid = adapter.generate(7, {"residual_policy": "largest_component"}, 2, 1)["train"][0]["input"]
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["protected"] is True
        for policy in POLICIES:
            actual = bridge.eval_text(f"({wrap_rule(adapter.program({'residual_policy': policy}))} {literal})")
            assert actual == prototype.solve_python(grid, policy)
