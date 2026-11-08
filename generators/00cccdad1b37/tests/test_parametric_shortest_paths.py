"""Native parametric shortest-path family: deterministic sampling and exact rules."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load_prototype():
    path = PARAMETRIC / "prototype.py"
    assert path.is_file(), "parametric shortest-path prototype is missing"
    spec = importlib.util.spec_from_file_location("_test_shortest_parametric", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


def canonical_source():
    from arcpuzzles import Catalog

    catalog = Catalog(ROOT)
    row = catalog.describe("00cccdad1b37")
    programs = {v["program_solution"] for v in catalog._variants()[row["rule_task_id"]]}
    assert len(programs) == 1
    return next(iter(programs))


def apply_racket(source, grid):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket"
        assert identity["protected"] is True
        return bridge.eval_text(f"({wrap_rule(source)} {literal})")


def test_default_program_is_exact_canonical_bytes(prototype):
    assert prototype.program({"route_segment": "whole"}) == canonical_source()


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_counts_matched_inputs_distinct_and_teaching(prototype, demos):
    settings = ({"route_segment": "whole"}, {"route_segment": "after_gate"})
    episodes = [prototype.generate(17, setting, demos, 4) for setting in settings]
    for episode, setting in zip(episodes, settings):
        assert episode["settings"] == setting
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [p["input"] for p in episode["train"] + episode["test"]]
        assert len({json.dumps(g, separators=(",", ":")) for g in inputs}) == demos + 4
        assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 30]
        certificate = prototype.check_teaching(episode["train"], setting)
        assert certificate["survivors"] == [setting["route_segment"]]
        assert certificate["fit_scope"] == "demonstrations_only"
    for split in ("train", "test"):
        assert [p["input"] for p in episodes[0][split]] == [p["input"] for p in episodes[1][split]]
    assert all(a["output"] != b["output"]
               for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


@pytest.mark.parametrize("setting", ["whole", "after_gate"])
def test_racket_program_executes_claimed_labels(prototype, setting):
    episode = prototype.generate(3, {"route_segment": setting}, 2, 4)
    source = prototype.program({"route_segment": setting})
    for pair in episode["train"] + episode["test"]:
        assert apply_racket(source, pair["input"]) == pair["output"]


def test_after_gate_uses_input_dependent_gate_and_omits_prefix(prototype):
    grids = [prototype.sample_input(29, "query", i, prototype.QUERY_PROFILES[i]) for i in range(4)]
    gates = [prototype.selected_gate(g) for g in grids]
    assert len(set(gates)) >= 3
    for grid in grids:
        whole = prototype.transform(grid, {"route_segment": "whole"})
        suffix = prototype.transform(grid, {"route_segment": "after_gate"})
        marked_whole = {(r, c) for r, row in enumerate(whole) for c, v in enumerate(row) if v == 8}
        marked_suffix = {(r, c) for r, row in enumerate(suffix) for c, v in enumerate(row) if v == 8}
        assert marked_suffix
        assert marked_suffix < marked_whole
        analysis = prototype.analyze(grid)
        assert analysis["partial"]
        assert analysis["partial"].isdisjoint(marked_whole)
        assert prototype.selected_gate(grid) in marked_suffix


def test_bounded_audit_rejects_declared_shortcuts(prototype):
    report = prototype.audit(seed=41, demos=3, queries=4)
    assert report["status"] == "passed"
    assert set(report["settings"]) == {"whole", "after_gate"}
    for row in report["settings"].values():
        assert row["survivors"] == [row["chosen"]]
        assert row["query_count"] == 4
        assert all(value["rejected"] for value in row["rivals"].values())


@pytest.mark.parametrize("field,value", [
    ("seed", -1), ("seed", True), ("demos", 1), ("demos", 7),
    ("demos", 3.0), ("queries", 0), ("queries", 5), ("queries", "4"),
])
def test_invalid_requests_fail(prototype, field, value):
    args = {"seed": 0, "settings": {"route_segment": "whole"}, "demos": 3, "queries": 4}
    args[field] = value
    with pytest.raises(ValueError):
        prototype.generate(**args)


@pytest.mark.parametrize("settings", [
    {}, {"route_segment": "unknown"}, {"route_segment": True},
    {"route_segment": "whole", "extra": 1},
])
def test_invalid_settings_fail(prototype, settings):
    with pytest.raises(ValueError):
        prototype.program(settings)


def test_strict_grid_rejects_bool_ragged_and_bad_palette(prototype):
    grid = prototype.sample_input(0, "demo", 0, prototype.DEMO_PROFILES[0])
    for mutation in ("bool", "ragged", "palette"):
        bad = deepcopy(grid)
        if mutation == "bool":
            bad[0][0] = True
        elif mutation == "ragged":
            bad[0].pop()
        else:
            bad[0][0] = 9
        with pytest.raises(ValueError):
            prototype.strict_grid(bad)
