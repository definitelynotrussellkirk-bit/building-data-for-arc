"""Regressions for the nested-frame base and its native frame-order family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PROTOTYPE = HOME / "workspace" / "parametric" / "prototype.py"
GENERATOR = HOME / "generator.py"


def load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return load(GENERATOR, "_test_74_generator")


@pytest.fixture(scope="module")
def prototype():
    return load(PROTOTYPE, "_test_74_parametric")


def marker_count(grid):
    return sum(cell == 2 for row in grid for cell in row)


def inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def hand_fixture():
    grid = [[0] * 11 for _ in range(11)]
    for r in range(1, 10):
        grid[r][1] = grid[r][9] = 1
    for c in range(1, 10):
        grid[1][c] = grid[9][c] = 1
    for r in range(3, 8):
        grid[r][3] = grid[r][7] = 1
    for c in range(3, 8):
        grid[3][c] = grid[7][c] = 1
    grid[10][0] = 2
    return grid


def test_base_schedule_cannot_repeat_outermost_selector_for_three_demos(generator):
    # Retained audit seed 9 previously produced three N=1 examples, allowing the
    # wrong "always outermost" rule to fit every demonstration.
    counts = [marker_count(generator.generate(9, i)) for i in range(3)]
    assert counts[0] == 1
    assert any(count > 1 for count in counts[1:]), counts
    assert all(generator.self_check(generator.generate(9, i)) == [] for i in range(3))


def canonical_pair(generator, grid):
    return {"input": deepcopy(grid), "output": generator.rule_mirror(grid)}


def test_base_semantic_contract_identifies_every_three_example_schedule_window(generator):
    assert generator.EXAMPLES_NEEDED == 3
    for difficulty in ("easy", None, "hard"):
        for window, start in enumerate((0, 11, 22, 33)):
            seed = 700 + 10 * window + (0 if difficulty is None else len(difficulty))
            pairs = [
                canonical_pair(
                    generator,
                    generator.generate(seed, start + offset, difficulty=difficulty),
                )
                for offset in range(4)
            ]
            assert generator.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_base_semantic_contract_names_the_retained_outermost_shortcut(generator):
    demos = [
        canonical_pair(generator, generator.generate(9, index, select_idx=0))
        for index in range(3)
    ]
    query = canonical_pair(generator, generator.generate(9, 3, select_idx=1))
    before = deepcopy((demos, query))
    reasons = generator.lesson_identifiable(demos, query)
    assert any("always_outermost" in reason for reason in reasons), reasons
    assert (demos, query) == before


def test_base_semantic_contract_rejects_bad_labels_and_too_few_demos(generator):
    pairs = [canonical_pair(generator, generator.generate(17, index)) for index in range(4)]
    bad = deepcopy(pairs[:3])
    bad[1]["output"] = [[0]]
    reasons = generator.lesson_identifiable(bad, pairs[3])
    assert any("demo 1 output" in reason for reason in reasons), reasons
    reasons = generator.lesson_identifiable(pairs[:2], pairs[3])
    assert any("at least 3 demonstrations" in reason for reason in reasons), reasons


def test_base_semantic_witnesses_are_real_counterexamples(generator):
    outer = generator.generate(31, 0, select_idx=0)
    non_outer = generator.generate(31, 1, select_idx=1)
    assert generator.strict_canonical_like(outer) == []
    assert generator.strict_canonical_like(generator._draw_from_degenerate("no_markers", None))

    expected_witnesses = {
        "outermost_selected",
        "non_outer_selected",
        "non_innermost_selected",
        "innermost_selected",
        "inner_exclusion_required",
    }
    assert set(generator.SEMANTIC_WITNESSES) == expected_witnesses
    assert set(generator.SEMANTIC_RIVALS) == {
        "always_outermost",
        "always_innermost",
        "fill_selected_interior",
    }
    assert generator.SEMANTIC_WITNESSES["non_outer_selected"](non_outer)
    assert (
        generator.SEMANTIC_RIVALS["always_outermost"](non_outer)
        != generator.rule_mirror(non_outer)
    )
    assert generator.SEMANTIC_WITNESSES["inner_exclusion_required"](outer)
    assert (
        generator.SEMANTIC_RIVALS["fill_selected_interior"](outer)
        != generator.rule_mirror(outer)
    )


def test_base_rule_mirror_matches_protected_canonical_racket(generator, prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    def apply(bridge, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(prototype.CANONICAL_PROGRAM)} {literal})")

    cases = [
        generator.generate(53, 0, difficulty="easy"),
        generator.generate(53, 1, difficulty="easy"),
        generator.generate(53, 2),
        generator.generate(53, 3),
        generator.generate(53, 4, difficulty="hard"),
        generator.generate(53, 5, difficulty="hard"),
    ]
    with RacketBridge(timeout=60) as bridge:
        assert bridge.runtime_identity["protected"] is True
        for grid in cases:
            assert generator.rule_mirror(grid) == apply(bridge, grid)


def test_frame_order_changes_the_selected_ring_on_a_hand_checked_input(prototype):
    grid = hand_fixture()
    outer = prototype.transform(grid, {"frame_order": "outer_first"})
    inner = prototype.transform(grid, {"frame_order": "inner_first"})
    assert outer[2][2] == 8 and outer[4][4] == 0
    assert inner[2][2] == 0 and inner[4][4] == 8


def test_default_program_is_exact_canonical_and_matched_inputs_teach_both_settings(prototype):
    from arcpuzzles import Catalog

    row = Catalog(ROOT).describe("74a2d06b72b1")
    canonical = {v["program_solution"] for v in Catalog(ROOT)._variants()[row["rule_task_id"]]}
    assert canonical == {prototype.program({"frame_order": "outer_first"})}

    outer = prototype.generate(17, {"frame_order": "outer_first"}, demos=2, queries=4)
    inner = prototype.generate(17, {"frame_order": "inner_first"}, demos=2, queries=4)
    assert inputs(outer) == inputs(inner)
    assert len(outer["train"]) == len(inner["train"]) == 2
    assert len(outer["test"]) == len(inner["test"]) == 4
    assert len({json.dumps(grid) for grid in inputs(outer)}) == 6
    assert outer["train"][0]["output"] != inner["train"][0]["output"]
    assert prototype.check_teaching(outer["train"], outer["settings"])["survivors"] == ["outer_first"]
    assert prototype.check_teaching(inner["train"], inner["settings"])["survivors"] == ["inner_first"]


@pytest.mark.parametrize("demos", [2, 6])
def test_demo_boundaries_keep_four_queries_and_query_prefix(prototype, demos):
    episode = prototype.generate(23, {"frame_order": "outer_first"}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    single = prototype.generate(23, {"frame_order": "outer_first"}, demos=demos, queries=1)
    assert single["test"] == episode["test"][:1]


def test_substantive_30x30_query_and_invalid_contracts(prototype):
    episode = prototype.generate(31, {"frame_order": "inner_first"}, demos=3, queries=4)
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    analysis = prototype.analyze(stress)
    assert len(analysis["frames"]) >= 5
    assert sum(cell == 1 for row in stress for cell in row) >= 250
    for kwargs in ({"demos": 1, "queries": 4}, {"demos": 7, "queries": 4}, {"demos": 3, "queries": 0}, {"demos": 3, "queries": 5}):
        with pytest.raises(ValueError):
            prototype.generate(0, {"frame_order": "outer_first"}, **kwargs)
    with pytest.raises(ValueError):
        prototype.program({"frame_order": "sideways"})


def test_bounded_shortcut_audit_rejects_fixed_frame_and_fill_shortcuts(prototype):
    report = prototype.audit(41)
    assert report["status"] == "passed"
    for setting in ("outer_first", "inner_first"):
        assert report["settings"][setting]["survivors"] == [setting]
        assert all(row["rejected"] for row in report["settings"][setting]["rivals"].values())


def test_python_labels_match_protected_racket_for_both_settings(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    def apply(bridge, source, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(source)} {literal})")

    with RacketBridge(timeout=60) as bridge:
        assert bridge.runtime_identity["protected"] is True
        for setting in ("outer_first", "inner_first"):
            episode = prototype.generate(41, {"frame_order": setting}, demos=2, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert apply(bridge, episode["program_solution"], pair["input"]) == pair["output"]


def test_tampered_label_and_private_fields_do_not_affect_public_projection(prototype):
    from reviewer_support import public_challenge_bytes

    episode = prototype.generate(7, {"frame_order": "outer_first"}, demos=2, queries=4)
    visible = public_challenge_bytes(episode)
    changed = deepcopy(episode)
    changed["settings"] = {"frame_order": "inner_first"}
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == visible
    bad = deepcopy(episode)
    bad["train"][0]["output"] = [[0]]
    with pytest.raises(ValueError):
        prototype.verify_episode(bad)
