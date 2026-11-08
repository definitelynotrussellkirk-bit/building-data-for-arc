"""Behavioral checks for the separate orbit-completion parametric family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/ba0c6a5828f9/workspace/parametric"
SETTINGS = ("all_orbits", "most_clipped")


def load_local(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"Parametric implementation is missing: {path}"
    spec = importlib.util.spec_from_file_location(f"parametric_ba0c6a5828f9_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fixture_grid() -> list[list[int]]:
    grid = [[0] * 8 for _ in range(7)]
    grid[2][2] = 2
    for r, c in ((0, 6), (2, 4), (3, 3)):
        grid[r][c] = 1
    return grid


def hand_outputs() -> dict[str, list[list[int]]]:
    grid = fixture_grid()
    selected = deepcopy(grid)
    selected[6][4] = 1
    all_orbits = deepcopy(selected)
    for r, c in ((4, 2), (2, 0), (0, 2), (3, 1), (1, 1), (1, 3)):
        all_orbits[r][c] = 1
    return {"all_orbits": all_orbits, "most_clipped": selected}


def test_hand_derived_selector_and_outputs():
    # A bug in orbit counting or selecting max/first instead of the unique
    # minimum changes this literal fixture's chosen marker and output cells.
    model = load_local("prototype")
    grid = fixture_grid()
    info = model.selector_info(grid)
    assert info["selected"] == [0, 6]
    assert info["selected_visible_count"] == 2
    assert sorted(row["visible_count"] for row in info["markers"]) == [2, 4, 4]
    for scope, expected in hand_outputs().items():
        original = deepcopy(grid)
        assert model.solve(grid, {"completion_scope": scope}) == expected
        assert grid == original


def test_default_program_is_exact_selected_catalog_authority():
    from arcpuzzles import Catalog

    adapter = load_local("adapter")
    catalog = Catalog(ROOT)
    selected = catalog.describe("ba0c6a5828f9").get("rule_task_id", "ba0c6a5828f9")
    programs = {row["program_solution"] for row in catalog.get(selected)["variants"]}
    assert len(programs) == 1
    canonical = programs.pop()
    assert adapter.program({"completion_scope": "all_orbits"}) == canonical
    assert adapter.program({"completion_scope": "most_clipped"}) != canonical


def test_contract_declares_exact_settings_resources_and_limits():
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/ba0c6a5828f9/workspace/parametric/adapter.py",
        "parameters": {"completion_scope": list(SETTINGS)},
        "default": {"completion_scope": "all_orbits"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/ba0c6a5828f9/workspace/parametric/prototype.py",
            "generators/ba0c6a5828f9/workspace/parametric/rules/canonical.rkt",
            "generators/ba0c6a5828f9/workspace/parametric/rules/most_clipped.rkt",
        ],
    }


@pytest.mark.parametrize("settings", [
    None, {}, [], "all_orbits", {"completion_scope": True},
    {"completion_scope": "ALL_ORBITS"}, {"completion_scope": "all_orbits", "extra": 1},
])
def test_invalid_settings_are_rejected(settings):
    adapter = load_local("adapter")
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, 3, 4)


@pytest.mark.parametrize("field,bad", [
    ("seed", True), ("seed", -1), ("seed", 2**63), ("seed", 1.0),
    ("demos", 1), ("demos", 7), ("demos", True), ("demos", 3.0),
    ("queries", 0), ("queries", 5), ("queries", True), ("queries", "4"),
])
def test_request_boundaries_reject_coercion(field, bad):
    adapter = load_local("adapter")
    args = {"seed": 0, "settings": {"completion_scope": "all_orbits"}, "demos": 3, "queries": 4}
    args[field] = bad
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(**args)


def test_supported_counts_are_exact_distinct_and_prefix_stable():
    adapter = load_local("adapter")
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = adapter.generate(17, {"completion_scope": "most_clipped"}, demos, queries)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == queries
            inputs = [p["input"] for p in episode["train"] + episode["test"]]
            assert len(inputs) == len({json.dumps(g) for g in inputs})
    short = adapter.generate(29, {"completion_scope": "all_orbits"}, 2, 1)
    long = adapter.generate(29, {"completion_scope": "all_orbits"}, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]


def test_inputs_are_matched_across_settings_and_labels_differ():
    adapter = load_local("adapter")
    for seed in (0, 17, 991):
        episodes = [adapter.generate(seed, {"completion_scope": scope}, 3, 4) for scope in SETTINGS]
        for split in ("train", "test"):
            assert [p["input"] for p in episodes[0][split]] == [p["input"] for p in episodes[1][split]]
        assert all(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


def test_two_demos_reject_all_named_rivals_for_each_setting():
    model = load_local("prototype")
    for seed in (0, 3, 17, 29):
        for scope in SETTINGS:
            episode = model.generate(seed, {"completion_scope": scope}, 2, 4)
            assert model.demo_rival_failures(episode["train"], {"completion_scope": scope}) == []


def test_declared_rival_programs_execute_and_match_independent_python_claims():
    # A malformed rival is not evidence of elimination.  Every declared finite
    # rival must execute on protected Racket and reproduce its Python claim.
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    model = load_local("prototype")
    grid = fixture_grid()
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    bridge = RacketBridge(timeout=20)
    try:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for name, source in model.RIVAL_PROGRAMS.items():
            actual = bridge.eval_text(f"({wrap_rule(source)} {literal})")
            assert actual == model.solve_rival(grid, name), name
    finally:
        bridge.close()


def test_fourth_query_is_substantive_30x30_orbit_stress():
    model = load_local("prototype")
    for seed in (0, 17, 991):
        grid = model.sample_inputs(seed, 3, 4)["test"][-1]
        assert (len(grid), len(grid[0])) == (30, 30)
        markers = model.marker_cells(grid)
        assert len(markers) >= 14
        assert min(r for r, _ in markers) <= 1 and max(r for r, _ in markers) >= 28
        assert min(c for _, c in markers) <= 1 and max(c for _, c in markers) >= 28
        quadrants = {(r >= 15, c >= 15) for r, c in markers}
        assert quadrants == {(False, False), (False, True), (True, False), (True, True)}
        info = model.selector_info(grid)
        counts = [row["visible_count"] for row in info["markers"]]
        assert counts.count(min(counts)) == 1
        assert min(counts) in (2, 3)
        assert 3 in counts and 4 in counts
        for scope in SETTINGS:
            out = model.solve(grid, {"completion_scope": scope})
            assert sum(a != b for ra, rb in zip(grid, out) for a, b in zip(ra, rb)) >= 1


def test_sequential_public_projection_hides_private_data_and_preserves_first_turn():
    model = load_local("prototype")
    one = model.generate(31, {"completion_scope": "most_clipped"}, 3, 1)
    four = model.generate(31, {"completion_scope": "most_clipped"}, 3, 4)
    assert model.public_turn_bytes(one, 0) == model.public_turn_bytes(four, 0)
    visible = json.loads(model.public_turn_bytes(four, 0))
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    tampered = deepcopy(four)
    tampered["settings"] = {"completion_scope": "all_orbits"}
    tampered["seed"] = 999
    tampered["program_solution"] = "private"
    tampered["test"][0]["output"][0][0] = 9
    assert model.public_turn_bytes(tampered, 0) == model.public_turn_bytes(four, 0)
    assert len({model.public_turn_id(four, i) for i in range(4)}) == 4


def test_reusable_audit_builds_and_verifies_source_bound_public_bundle(tmp_path):
    # A future reviewer must be able to replay a small protected-Racket audit,
    # verify every saved byte, and see no private setting/program/query answer
    # in the public turns.
    audit = load_local("audit")
    out = tmp_path / "audit"
    summary = audit.build(
        out,
        jobs=[
            {"seed": 0, "settings": {"completion_scope": "all_orbits"}},
            {"seed": 0, "settings": {"completion_scope": "most_clipped"}},
        ],
        demos=2,
        queries=4,
        reliability_seeds=2,
    )
    assert summary["status"] == "passed"
    assert summary["episodes"] == 2
    assert summary["public_turns"] == 8
    checked = audit.verify(out)
    assert checked["status"] == "passed"
    for public in sorted((out / "public").glob("*.json")):
        assert public.stem == __import__("hashlib").sha256(public.read_bytes()).hexdigest()
        visible = json.loads(public.read_bytes())
        assert set(visible) == {"train", "test"}
        assert len(visible["test"]) == 1
        assert set(visible["test"][0]) == {"input"}
