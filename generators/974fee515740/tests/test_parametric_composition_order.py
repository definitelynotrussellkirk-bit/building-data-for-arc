"""Behavioral tests for the native composition-order parametric family."""
from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK = "974fee515740"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
NATIVE = HOME / "workspace" / "parametric" / "native.py"


def load_native():
    spec = importlib.util.spec_from_file_location("_composition_order_test", NATIVE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_program_is_byte_exact_catalog_authority():
    from arcpuzzles import Catalog

    native = load_native()
    canonical = {v["program_solution"] for v in Catalog(ROOT).get(TASK)["variants"]}
    assert canonical == {native.program({"composition_order": "rotate_then_combine"})}
    assert native.program({"composition_order": "combine_then_rotate"}) not in canonical


@pytest.mark.parametrize("settings", [
    None, {}, "rotate_then_combine", {"composition_order": "unknown"},
    {"composition_order": True},
    {"composition_order": "rotate_then_combine", "extra": 1},
])
def test_settings_fail_closed(settings):
    native = load_native()
    with pytest.raises((TypeError, ValueError)):
        native.program(settings)
    with pytest.raises((TypeError, ValueError)):
        native.generate(0, settings, 2, 4)


@pytest.mark.parametrize("field,value", [
    ("seed", True), ("seed", -1), ("seed", 1.0),
    ("demos", 1), ("demos", 7), ("demos", True),
    ("queries", 0), ("queries", 5), ("queries", False),
])
def test_request_boundaries_fail_closed(field, value):
    native = load_native()
    args = dict(seed=0, settings={"composition_order": "rotate_then_combine"}, demos=2, queries=4)
    args[field] = value
    with pytest.raises((TypeError, ValueError)):
        native.generate(**args)


@pytest.mark.parametrize("order", ["rotate_then_combine", "combine_then_rotate"])
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_independent_counts_and_episode_contract(order, demos, queries):
    native = load_native()
    episode = native.generate(17, {"composition_order": order}, demos, queries)
    assert episode["program_solution"] == native.program({"composition_order": order})
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    seen = set()
    for pair in episode["train"] + episode["test"]:
        facts = native.analyze(pair["input"])
        assert pair["output"] == native.transform(pair["input"], order)
        assert facts["red_mask"] and facts["blue_mask"]
        key = json.dumps(pair["input"], separators=(",", ":"))
        assert key not in seen
        seen.add(key)


def test_matched_inputs_query_prefix_and_setting_difference():
    native = load_native()
    default = native.generate(17, {"composition_order": "rotate_then_combine"}, 3, 4)
    alternate = native.generate(17, {"composition_order": "combine_then_rotate"}, 3, 4)
    short = native.generate(17, {"composition_order": "combine_then_rotate"}, 3, 1)
    for split in ("train", "test"):
        assert [p["input"] for p in default[split]] == [p["input"] for p in alternate[split]]
    assert short["train"] == alternate["train"]
    assert short["test"] == alternate["test"][:1]
    assert all(a["output"] != b["output"] for a, b in zip(default["train"], alternate["train"]))
    assert all(a["output"] != b["output"] for a, b in zip(default["test"], alternate["test"]))


def test_minimum_lesson_rejects_declared_rivals_without_query_answers():
    native = load_native()
    for seed in (0, 17, 83):
        for order in native.SETTINGS:
            episode = native.generate(seed, {"composition_order": order}, 2, 4)
            survivors = {
                name for name in native.RIVAL_NAMES
                if all(native.rival_output(pair["input"], name) == pair["output"]
                       for pair in episode["train"])
            }
            assert survivors == {order}


def test_intermediate_order_is_input_derived_and_causally_consumed():
    native = load_native()
    grid = native.generate(19, {"composition_order": "rotate_then_combine"}, 2, 4)["train"][0]["input"]
    facts = native.analyze(grid)
    assert facts["rotation_code"] in (2, 3, 4)
    assert facts["rotated_blue_mask"] != facts["blue_mask"]
    first = native.transform(grid, "rotate_then_combine")
    second = native.transform(grid, "combine_then_rotate")
    assert first != second
    assert first == facts["rotate_then_combine_output"]
    assert second == facts["combine_then_rotate_output"]


def test_fourth_query_is_substantive_distributed_30_by_30_content():
    native = load_native()
    grid = native.generate(17, {"composition_order": "rotate_then_combine"}, 3, 4)["test"][3]["input"]
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    assert sum(value != 0 for row in grid for value in row) >= 45
    for r0, c0 in ((0, 0), (0, 15), (15, 0), (15, 15)):
        block = [grid[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15)]
        assert any(value != 0 for value in block)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    native = load_native()
    random.seed(121212)
    before = random.getstate()
    first = native.generate(23, {"composition_order": "combine_then_rotate"}, 3, 4)
    second = native.generate(23, {"composition_order": "combine_then_rotate"}, 3, 4)
    assert random.getstate() == before
    assert first == second
    first["train"][0]["input"][0][0] = 9
    assert first != second


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def test_canonical_program_still_matches_all_original_labels_in_protected_racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    native = load_native()
    wrapped = wrap_rule(native.program({"composition_order": "rotate_then_combine"}))
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        assert bridge.runtime_identity["protected"] is True
        for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
            assert bridge.eval_text(f"({wrapped} {_literal(pair['input'])})") == pair["output"]


def test_alternative_program_matches_claimed_labels_in_protected_racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    native = load_native()
    episode = native.generate(17, {"composition_order": "combine_then_rotate"}, 2, 4)
    wrapped = wrap_rule(episode["program_solution"])
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        assert bridge.runtime_identity["protected"] is True
        for pair in (episode["train"][0], episode["train"][1], episode["test"][-1]):
            assert bridge.eval_text(f"({wrapped} {_literal(pair['input'])})") == pair["output"]


def test_reusable_bounded_audit_finds_no_harmful_declared_survivor():
    path = HOME / "workspace" / "parametric" / "audit.py"
    spec = importlib.util.spec_from_file_location("_composition_order_audit_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    report = module.run_audit(range(8))
    assert report["status"] == "passed"
    assert report["episodes"] == 8 * 2 * 5
    assert report["harmful_survivors"] == []
    assert report["matched_input_failures"] == []
