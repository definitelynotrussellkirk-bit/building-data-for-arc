"""Focused contract tests for marker selection followed by column ordering."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator, public_challenge_bytes

TASK_ID = "0005ab5b7704"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ORDERS = ("left_to_right", "body_density_desc")


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
        "parameters": {"column_order": list(ORDERS)},
        "default": {"column_order": "left_to_right"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/body_density_desc.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/wrong_intermediate.rkt",
            f"generators/{TASK_ID}/workspace/parametric/audit.py",
        ],
    }
    assert adapter.program({"column_order": "left_to_right"}) == _canonical_program()
    assert (HOME / "rules" / "canonical.rkt").read_text() == _canonical_program()
    assert adapter.program({"column_order": "body_density_desc"}) != _canonical_program()


@pytest.mark.parametrize("settings", [None, {}, {"column_order": True}, {"column_order": "reverse"}, {"column_order": "left_to_right", "extra": 1}])
def test_invalid_settings_reject(settings):
    adapter = _load("adapter.py", "adapter_invalid")
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, demos=3, queries=4)


@pytest.mark.parametrize("order", ORDERS)
def test_counts_are_prefix_stable_copy_isolated_and_setting_neutral(order):
    adapter = _load("adapter.py", f"adapter_counts_{order}")
    full = adapter.generate(91, {"column_order": order}, demos=6, queries=4)
    assert full == adapter.generate(91, {"column_order": order}, demos=6, queries=4)
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = adapter.generate(91, {"column_order": order}, demos=demos, queries=queries)
            assert episode["train"] == full["train"][:demos]
            assert episode["test"] == full["test"][:queries]
    full["test"][0]["input"][0][0] = 9
    assert adapter.generate(91, {"column_order": order}, 6, 4)["test"][0]["input"][0][0] != 9
    other = "body_density_desc" if order == "left_to_right" else "left_to_right"
    assert _inputs(adapter.generate(91, {"column_order": order}, 6, 4)) == _inputs(adapter.generate(91, {"column_order": other}, 6, 4))


@pytest.mark.parametrize("seed", [0, 17, 211])
@pytest.mark.parametrize("order", ORDERS)
def test_two_demonstrations_identify_setting_and_refute_named_rivals(seed, order):
    prototype = _load("prototype.py", f"prototype_teach_{seed}_{order}")
    adapter = _load("adapter.py", f"adapter_teach_{seed}_{order}")
    episode = adapter.generate(seed, {"column_order": order}, demos=2, queries=4)
    survivors = [
        candidate
        for candidate in ORDERS
        if all(prototype.solve_python(pair["input"], candidate) == pair["output"] for pair in episode["train"])
    ]
    assert survivors == [order]
    certificate = prototype.teaching_check(episode, order)
    assert certificate["demo_survivors"] == []
    assert certificate["harmful_survivors"] == []


def test_fourth_query_is_substantive_30x30_and_density_order_is_nontrivial():
    prototype = _load("prototype.py", "prototype_stress")
    adapter = _load("adapter.py", "adapter_stress")
    pair = adapter.generate(20261025, {"column_order": "body_density_desc"}, 3, 4)["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    analysis = prototype.analyze(grid)
    assert analysis["foreground_cells"] >= 350
    assert len(analysis["selected_columns"]) >= 6
    assert len(set(analysis["selected_counts"])) == len(analysis["selected_counts"])
    assert analysis["density_order"] != analysis["selected_columns"]
    assert analysis["max_unselected_count"] > min(analysis["selected_counts"])


def test_public_turn_masks_private_fields_and_is_first_turn_stable():
    adapter = _load("adapter.py", "adapter_public")
    one = adapter.generate(33, {"column_order": "body_density_desc"}, 3, 1)
    four = adapter.generate(33, {"column_order": "body_density_desc"}, 3, 4)
    public = adapter.public_turn(four, 0)
    assert public == {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    assert public_challenge_bytes(one) == public_challenge_bytes(public)
    text = json.dumps(public, sort_keys=True)
    assert "column_order" not in text and "program_solution" not in text


def test_dependency_trace_requires_marker_selection_before_density_sort():
    prototype = _load("prototype.py", "prototype_dependency")
    adapter = _load("adapter.py", "adapter_dependency")
    grid = adapter.generate(1701, {"column_order": "body_density_desc"}, 2, 4)["test"][0]["input"]
    trace = prototype.dependency_trace(grid)
    assert trace["step_a"] == "select the header-marked columns and measure their body occupancy"
    assert trace["intermediate_value"] == prototype.analyze(grid)["selected_with_counts"]
    assert trace["output"] == prototype.solve_python(grid, "body_density_desc")
    assert trace["wrong_intermediate_output"] != trace["output"]


def test_racket_programs_match_python_on_a_distinguishing_pair():
    prototype = _load("prototype.py", "prototype_racket")
    adapter = _load("adapter.py", "adapter_racket")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    grid = adapter.generate(7, {"column_order": "body_density_desc"}, 2, 1)["train"][0]["input"]
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["protected"] is True
        for order in ORDERS:
            actual = bridge.eval_text(f"({wrap_rule(adapter.program({'column_order': order}))} {literal})")
            assert actual == prototype.solve_python(grid, order)
