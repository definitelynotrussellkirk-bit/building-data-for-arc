"""Behavioral tests for the native rotation-scope parametric family."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK = "0a855288946a"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
from reviewer_support import find_root, canonical_pairs

ROOT = find_root(__file__)
NATIVE = HOME / "workspace" / "parametric" / "native.py"


def load_native():
    spec = importlib.util.spec_from_file_location("_rotation_scope_test", NATIVE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_program_is_byte_exact_catalog_authority():
    from arcpuzzles import Catalog

    native = load_native()
    canonical = {v["program_solution"] for v in Catalog(ROOT).get(TASK)["variants"]}
    assert canonical == {native.program({"rotation_scope": "all_cells"})}
    assert native.program({"rotation_scope": "rarest_color_orbits"}) not in canonical


@pytest.mark.parametrize("settings", [
    None, {}, "all_cells", {"rotation_scope": "unknown"},
    {"rotation_scope": True}, {"rotation_scope": "all_cells", "extra": 1},
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
    args = dict(seed=0, settings={"rotation_scope": "all_cells"}, demos=2, queries=4)
    args[field] = value
    with pytest.raises((TypeError, ValueError)):
        native.generate(**args)


@pytest.mark.parametrize("scope", ["all_cells", "rarest_color_orbits"])
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_independent_counts_and_episode_contract(scope, demos, queries):
    native = load_native()
    episode = native.generate(17, {"rotation_scope": scope}, demos, queries)
    assert episode["program_solution"] == native.program({"rotation_scope": scope})
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    seen = set()
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        assert native.analyze(grid)["rarest_color"] in range(1, 10)
        assert pair["output"] == native.transform(grid, scope)
        key = json.dumps(grid, separators=(",", ":"))
        assert key not in seen
        seen.add(key)


def test_matched_inputs_and_query_prefix_are_setting_independent():
    native = load_native()
    all_cells = native.generate(17, {"rotation_scope": "all_cells"}, 3, 4)
    rare = native.generate(17, {"rotation_scope": "rarest_color_orbits"}, 3, 4)
    short = native.generate(17, {"rotation_scope": "rarest_color_orbits"}, 3, 1)
    for split in ("train", "test"):
        assert [p["input"] for p in all_cells[split]] == [p["input"] for p in rare[split]]
    assert short["train"] == rare["train"]
    assert short["test"] == rare["test"][:1]
    assert all(a["output"] != b["output"] for a, b in zip(all_cells["train"], rare["train"]))


def test_minimum_lesson_rejects_declared_rivals_without_query_answers():
    native = load_native()
    for seed in (0, 17, 83):
        for scope in native.SETTINGS:
            episode = native.generate(seed, {"rotation_scope": scope}, 2, 4)
            survivors = {
                name for name in native.RIVAL_NAMES
                if all(native.rival_output(pair["input"], name) == pair["output"]
                       for pair in episode["train"])
            }
            assert survivors == {scope}


def test_rarest_stage_is_input_dependent_and_changes_orbit_selection():
    native = load_native()
    first = native.generate(11, {"rotation_scope": "rarest_color_orbits"}, 2, 4)["train"][0]["input"]
    facts = native.analyze(first)
    counts = Counter(v for row in first for v in row if v)
    assert counts[facts["rarest_color"]] < min(v for k, v in counts.items() if k != facts["rarest_color"])
    selected = set(map(tuple, facts["selected_cells"]))
    assert selected
    assert all((facts["height"] - 1 - r, facts["width"] - 1 - c) not in selected for r, c in selected)
    output = native.transform(first, "rarest_color_orbits")
    changed = {(r, c) for r in range(facts["height"]) for c in range(facts["width"])
               if output[r][c] != first[r][c]}
    expected = selected | {(facts["height"] - 1 - r, facts["width"] - 1 - c) for r, c in selected}
    assert changed == expected


def test_fourth_query_is_substantive_30_by_30_content():
    native = load_native()
    grid = native.generate(17, {"rotation_scope": "all_cells"}, 3, 4)["test"][3]["input"]
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    assert sum(v != 0 for row in grid for v in row) >= 300
    for r0, c0 in ((0, 0), (0, 15), (15, 0), (15, 15)):
        block = [grid[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15)]
        assert sum(v != 0 for v in block) >= 50
        assert len(set(block) - {0}) >= 3


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    native = load_native()
    random.seed(123456)
    before = random.getstate()
    first = native.generate(23, {"rotation_scope": "rarest_color_orbits"}, 3, 4)
    second = native.generate(23, {"rotation_scope": "rarest_color_orbits"}, 3, 4)
    assert random.getstate() == before
    assert first == second
    first["train"][0]["input"][0][0] = 9
    assert first != second


def test_canonical_program_still_matches_all_original_labels_in_protected_racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    native = load_native()
    program = native.program({"rotation_scope": "all_cells"})
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        assert bridge.runtime_identity["protected"] is True
        wrapped = wrap_rule(program)
        for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
            assert bridge.eval_text(f"({wrapped} {literal})") == pair["output"]


def test_alternative_program_matches_claimed_labels_in_protected_racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    native = load_native()
    episode = native.generate(17, {"rotation_scope": "rarest_color_orbits"}, 2, 4)
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        wrapped = wrap_rule(episode["program_solution"])
        for pair in (episode["train"][0], episode["test"][-1]):
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
            assert bridge.eval_text(f"({wrapped} {literal})") == pair["output"]


def test_reusable_bounded_audit_finds_no_harmful_declared_survivor():
    path = HOME / "workspace" / "parametric" / "audit.py"
    spec = importlib.util.spec_from_file_location("_rotation_scope_audit_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    report = module.run_audit(range(8))
    assert report["status"] == "passed"
    assert report["episodes"] == 8 * 2 * 5
    assert report["harmful_survivors"] == []
    assert report["matched_input_failures"] == []


def test_minimum_lesson_rejects_numeric_rank_rivals_on_regression_seeds():
    native = load_native()
    for seed in (26, 31, 45, 53, 60, 65, 90, 106, 108):
        episode = native.generate(seed, {"rotation_scope": "rarest_color_orbits"}, 2, 4)
        survivors = {
            name for name in native.RIVAL_NAMES
            if all(native.rival_output(pair["input"], name) == pair["output"]
                   for pair in episode["train"])
        }
        assert survivors == {"rarest_color_orbits"}
