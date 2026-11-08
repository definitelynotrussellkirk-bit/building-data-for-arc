"""Behavioral contract for the native outline / most-occluded-fill family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
PARAMETRIC = HOME / "workspace/parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ORACLE = PARAMETRIC / "oracle.py"
RIVALS = PARAMETRIC / "rivals.py"
OUTLINE = {"finish": "outline"}
OCCLUDED = {"finish": "fill_most_occluded"}


def load(path: Path, stem: str):
    assert path.is_file(), f"{path.name} has not been implemented"
    name = f"_5ccd_{stem}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def prototype():
    return load(PROTOTYPE, "prototype")


def oracle():
    return load(ORACLE, "oracle")


def rivals():
    return load(RIVALS, "rivals")


def rows(*lines: str) -> list[list[int]]:
    return [[int(cell) for cell in line] for line in lines]


def literal_input():
    return rows(
        "00000000000",
        "00000000000",
        "00000000000",
        "00000101000",
        "00000000000",
        "00000000200",
        "00000000070",
        "00000000000",
        "00720000000",
    )


def literal_outline():
    return rows(
        "00000000000",
        "00000000000",
        "00000000000",
        "00000111000",
        "00000000000",
        "00022222200",
        "00777777770",
        "00720000270",
        "00777777770",
    )


def literal_occluded():
    return rows(
        "00000000000",
        "00000000000",
        "00000000000",
        "00000111000",
        "00000000000",
        "00022222200",
        "00772222770",
        "00722222270",
        "00777777770",
    )


def execute_racket(source: str, grid, bridge):
    from puzzle_generators.rule_wrap import wrap_rule

    datum = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(source)} {datum})")


def test_default_program_is_exact_unique_canonical_authority():
    p = prototype()
    sources = {
        row["program_solution"]
        for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == "5ccdbe078da6"
    }
    assert len(sources) == 1
    canonical = sources.pop()
    assert p.canonical_source() == canonical == p.program(OUTLINE)
    assert hashlib.sha256(canonical.encode()).hexdigest() == p.CANONICAL_PROGRAM_SHA256
    assert p.program(OCCLUDED) != canonical


def test_literal_oracle_names_real_intermediate_and_fills_selected_interior():
    o = oracle()
    grid = literal_input()
    before = copy.deepcopy(grid)
    assert o.solve(grid, "outline") == literal_outline()
    assert o.solve(grid, "fill_most_occluded") == literal_occluded()
    intermediate = o.occlusion_intermediate(grid)
    assert intermediate["reading_order"] == [1, 2, 7]
    assert intermediate["selected_color"] == 2
    assert intermediate["selected_index"] == 1
    assert [row["loss"] for row in intermediate["colors"]] == [0, 8, 0]
    assert grid == before


def test_literal_programs_match_hand_derived_outputs_in_protected_racket():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        assert execute_racket(p.program(OUTLINE), literal_input(), bridge) == literal_outline()
        assert execute_racket(p.program(OCCLUDED), literal_input(), bridge) == literal_occluded()


def test_seed_count_and_setting_validation_rejects_coercions():
    p = prototype()
    for seed in (True, False, -1, 2**63, 1.0, "17", None):
        with pytest.raises((ValueError, TypeError)):
            p.sample_inputs(seed)
        with pytest.raises((ValueError, TypeError)):
            p.generate(seed, OUTLINE)
    for name, values in (("demos", (1, 7, True, 3.0)), ("queries", (0, 5, False, 1.0))):
        for value in values:
            with pytest.raises((ValueError, TypeError)):
                p.sample_inputs(17, **{name: value})
    for settings in ({}, {"finish": "unknown"}, {"finish": "outline", "extra": 1}, None, "outline"):
        with pytest.raises((ValueError, TypeError)):
            p.program(settings)
        with pytest.raises((ValueError, TypeError)):
            p.generate(17, settings)


def test_split_prefixes_are_stable_and_counts_are_independent():
    p = prototype()
    full = p.sample_inputs(17, demos=6, queries=4)
    assert len(full["train"]) == 6 and len(full["test"]) == 4
    for demos, queries in ((2, 1), (2, 4), (3, 2), (6, 1)):
        small = p.sample_inputs(17, demos=demos, queries=queries)
        assert small["train"] == full["train"][:demos]
        assert small["test"] == full["test"][:queries]


def test_sampler_is_deterministic_fresh_setting_independent_and_rng_isolated():
    p = prototype()
    random.seed(412)
    state = random.getstate()
    first = p.sample_inputs(17, demos=6, queries=4)
    assert random.getstate() == state
    second = p.sample_inputs(17, demos=6, queries=4)
    assert first == second
    first["train"][0][0][0] = (first["train"][0][0][0] + 1) % 10
    assert p.sample_inputs(17, demos=6, queries=4) == second
    assert p.sample_inputs(0, demos=6, queries=4) != second
    for settings in (OUTLINE, OCCLUDED):
        episode = p.generate(17, settings, demos=2, queries=4)
        assert [x["input"] for x in episode["train"]] == second["train"][:2]
        assert [x["input"] for x in episode["test"]] == second["test"]


def test_maximum_episode_has_ten_distinct_valid_pair_inputs():
    p = prototype()
    o = oracle()
    for seed in (0, 17, 2**63 - 1):
        sample = p.sample_inputs(seed, demos=6, queries=4)
        grids = sample["train"] + sample["test"]
        encoded = [json.dumps(grid, separators=(",", ":")) for grid in grids]
        assert len(encoded) == len(set(encoded)) == 10
        for grid in grids:
            assert o.validate_pair_grid(grid) == []
            assert len(o.positions(grid)) == 3
            assert all(len(cells) == 2 for cells in o.positions(grid).values())


def test_first_two_demos_refute_all_declared_finite_shortcuts_without_queries():
    p = prototype()
    r = rivals()
    for seed in (0, 17, 2**63 - 1):
        demos = p.sample_inputs(seed, demos=2, queries=1)["train"]
        for settings in (OUTLINE, OCCLUDED):
            finish = settings["finish"]
            truth = [r.predict(grid, finish) for grid in demos]
            survivors = [
                name
                for name in r.active_rivals(finish)
                if all(r.predict(grid, finish, name) == output for grid, output in zip(demos, truth))
            ]
            assert survivors == [], (seed, finish, survivors)


def test_generated_claims_match_protected_racket_for_both_settings():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        for settings in (OUTLINE, OCCLUDED):
            episode = p.generate(17, settings, demos=3, queries=4)
            assert episode["program_solution"] == p.program(settings)
            assert len(episode["train"]) == 3 and len(episode["test"]) == 4
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == execute_racket(episode["program_solution"], pair["input"], bridge)


def test_fourth_query_is_substantive_30_by_30_boundary_stress():
    p = prototype()
    o = oracle()
    grid = p.sample_inputs(17, demos=2, queries=4)["test"][3]
    assert len(grid) == 30 and len(grid[0]) == 30
    points = [point for cells in o.positions(grid).values() for point in cells]
    assert min(r for r, c in points) == 0 and max(r for r, c in points) == 29
    assert min(c for r, c in points) == 0 and max(c for r, c in points) == 29
    outline = o.solve(grid, "outline")
    filled = o.solve(grid, "fill_most_occluded")
    assert sum(a != b for ra, rb in zip(outline, filled) for a, b in zip(ra, rb)) >= 400
    assert sum(v != 0 for row in outline for v in row) >= 120


def test_wrong_intermediate_counterfactual_changes_a_qualified_shape():
    p = prototype()
    o = oracle()
    grid = p.sample_inputs(17, demos=2, queries=4)["train"][1]
    true_meta = o.occlusion_intermediate(grid)
    wrong_meta = o.counterfactual_intermediate(grid, "largest_perimeter")
    assert true_meta["selected_color"] != wrong_meta["selected_color"]
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        truth = execute_racket(p.program(OCCLUDED), grid, bridge)
        wrong = execute_racket(p.counterfactual_program("largest_perimeter"), grid, bridge)
    assert truth != wrong


def test_public_turn_reveals_one_input_and_no_program_setting_or_future_query():
    p = prototype()
    episode = p.generate(17, OCCLUDED, demos=2, queries=4)
    before = copy.deepcopy(episode)
    visible = p.public_turn(episode, query_index=1)
    assert set(visible) == {"train", "test"}
    assert len(visible["train"]) == 2 and len(visible["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert set(visible["test"][0]) == {"input"}
    assert visible["test"][0]["input"] == episode["test"][1]["input"]
    assert episode == before
    serialized = json.dumps(visible)
    assert "program_solution" not in serialized and "fill_most_occluded" not in serialized


def test_first_turn_bytes_do_not_reveal_total_query_count():
    p = prototype()
    from reviewer_support import public_challenge_bytes

    for settings in (OUTLINE, OCCLUDED):
        one = p.generate(17, settings, demos=2, queries=1)
        four = p.generate(17, settings, demos=2, queries=4)
        assert public_challenge_bytes(p.public_turn(one)) == public_challenge_bytes(p.public_turn(four))


def test_adapter_is_thin_and_contract_supports_two_to_six_demos_four_queries():
    p = prototype()
    adapter = PARAMETRIC / "adapter.py"
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert adapter.is_file()
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/5ccdbe078da6/workspace/parametric/adapter.py",
        "parameters": {"finish": ["outline", "fill_most_occluded"]},
        "default": OUTLINE,
        "qualification_demos": 3,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }
    loaded = load(adapter, "adapter")
    assert loaded.program(OUTLINE) == p.program(OUTLINE)
    assert loaded.generate(17, OCCLUDED, 2, 4) == p.generate(17, OCCLUDED, 2, 4)


def test_reusable_self_audit_reports_no_two_demo_finite_survivors():
    audit = load(PARAMETRIC / "self_audit.py", "self_audit")
    report = audit.audit_demos(17)
    assert report["findings"] == []
    assert {row["finish"] for row in report["settings"]} == {"outline", "fill_most_occluded"}
    assert all(row["survivors"] == [] for row in report["settings"])
    assert report["query_outputs_consulted_for_selection"] is False
