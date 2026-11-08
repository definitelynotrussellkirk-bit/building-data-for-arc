"""Hand-derived semantics and protected-Racket checks for the join prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RULES_PATH = HOME / "workspace" / "parametric" / "rules.py"


def _rules():
    assert RULES_PATH.is_file(), "the parametric transformation has not been implemented"
    spec = importlib.util.spec_from_file_location("rectangle_parametric_rules_test", RULES_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid(*rows):
    return [[int(cell) for cell in row] for row in rows]


ODD_PAIR = _grid(
    "000000000", "044404440", "044404440", "044404440", "000000000"
)
ODD_JOINED = _grid(
    "000000000", "044444440", "044444440", "044444440", "000000000"
)
ODD_JOINED_CROSS = _grid(
    "000000000", "000040000", "044444440", "000040000", "000000000"
)
ODD_SEPARATE_CROSSES = _grid(
    "000000000", "004000400", "044404440", "004000400", "000000000"
)


def test_join_recomputes_one_new_cross_instead_of_two_original_crosses():
    rules = _rules()
    before = deepcopy(ODD_PAIR)
    assert rules.joined_grid(ODD_PAIR, "horizontal") == ODD_JOINED
    assert rules.transform(ODD_PAIR, "horizontal") == ODD_JOINED_CROSS
    assert rules.transform(ODD_PAIR, "none") == ODD_SEPARATE_CROSSES
    assert ODD_PAIR == before


def test_join_can_remove_odd_eligibility_and_can_create_odd_eligibility():
    rules = _rules()
    odd_even = _grid("00000000", "04440440", "04440440", "04440440", "00000000")
    assert rules.transform(odd_even, "horizontal") == _grid(
        "00000000", "04444440", "04444440", "04444440", "00000000"
    )
    even_even = _grid("0000000", "0440440", "0440440", "0440440", "0000000")
    assert rules.transform(even_even, "horizontal") == _grid(
        "0000000", "0004000", "0444440", "0004000", "0000000"
    )


def test_vertical_join_has_transposed_geometry_and_horizontal_join_does_not_act():
    rules = _rules()
    vertical = [list(row) for row in zip(*ODD_PAIR)]
    assert rules.transform(vertical, "vertical") == [list(row) for row in zip(*ODD_JOINED_CROSS)]
    assert rules.transform(vertical, "horizontal") == [list(row) for row in zip(*ODD_SEPARATE_CROSSES)]


def test_near_misses_do_not_join_and_non_rectangles_stay_unchanged():
    rules = _rules()
    two_column_gap = _grid(
        "0000000000", "0444004440", "0444004440", "0444004440", "0000000000"
    )
    unequal_span = _grid(
        "000000000", "044400000", "044404440", "044404440", "000004440", "000000000"
    )
    for grid in (two_column_gap, unequal_span):
        assert rules.joined_grid(grid, "horizontal") == grid
    hollow = _grid("00000", "04440", "04040", "04440", "00000")
    assert rules.transform(hollow, "horizontal") == hollow


def test_all_original_eligible_pairs_bridge_simultaneously():
    rules = _rules()
    chain = _grid("0000000000", "0440440440", "0440440440", "0440440440", "0000000000")
    # Three width-two rectangles and two gaps form one width-eight even rectangle.
    assert rules.transform(chain, "horizontal") == _grid(
        "0000000000", "0444444440", "0444444440", "0444444440", "0000000000"
    )


def test_canonical_default_is_exact_registered_program_bytes():
    rules = _rules()
    selected = next(
        json.loads(line)["program_solution"]
        for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == "13507b4f7614"
    )
    assert rules.canonical_program() == selected
    assert rules.program({"join_axis": "none"}) == selected
    assert (RULES_PATH.parent / "canonical.rkt").read_bytes() == selected.encode()


@pytest.mark.parametrize("settings", [None, {}, {"join_axis": "diagonal"}, {"join_axis": True},
    {"join_axis": ["horizontal"]}, {"join_axis": "none", "extra": 1}])
def test_invalid_settings_fail_closed(settings):
    with pytest.raises((TypeError, ValueError)):
        _rules().program(settings)


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 4]], [[True]], [[4.0]], [[2]], [[0] * 31]])
def test_malformed_or_out_of_domain_grids_fail_closed(grid):
    with pytest.raises((TypeError, ValueError)):
        _rules().transform(grid, "none")


def test_protected_racket_matches_hand_witness_and_real_order_ablations():
    rules = _rules()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    def apply(bridge, source, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(source)} {literal})")

    with RacketBridge() as bridge:
        assert bridge.runtime_identity["protected"] is True
        for axis, want in (("none", ODD_SEPARATE_CROSSES), ("horizontal", ODD_JOINED_CROSS),
                           ("vertical", ODD_SEPARATE_CROSSES)):
            assert apply(bridge, rules.program({"join_axis": axis}), ODD_PAIR) == want
        for mode in ("skip_a", "wrong_order"):
            assert apply(bridge, rules.counterfactual_program("horizontal", mode), ODD_PAIR) == ODD_SEPARATE_CROSSES
        assert apply(bridge, rules.counterfactual_program("horizontal", "join_only"), ODD_PAIR) == ODD_JOINED
        assert apply(bridge, rules.counterfactual_program("vertical", "both_axes"), ODD_PAIR) == ODD_JOINED_CROSS
        odd_even = _grid("00000000", "04440440", "04440440", "04440440", "00000000")
        assert apply(bridge, rules.counterfactual_program("horizontal", "ignore_parity"), odd_even) == _grid(
            "00000000", "00040000", "04444440", "00040000", "00000000"
        )


@pytest.mark.parametrize("mode,want", [
    ("height_only", _grid("00000000", "04000000", "04400000", "04000000", "00004440", "00004440", "00000000")),
    ("width_only", _grid("00000000", "04400000", "04400000", "04400000", "00004440", "00000400", "00000000")),
])
def test_one_dimension_parity_rivals_expose_the_mixed_parity_teaching_hole(mode, want):
    rules = _rules()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    grid = _grid("00000000", "04400000", "04400000", "04400000", "00004440", "00004440", "00000000")
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge() as bridge:
        for axis in ("none", "horizontal", "vertical"):
            program = rules.counterfactual_program(axis, mode)
            assert bridge.eval_text(f"({wrap_rule(program)} {literal})") == want
            assert rules.transform(grid, axis) == grid


def test_first_bridge_rival_stops_before_the_second_gap_in_a_three_part_chain():
    rules = _rules()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    chain = _grid("0000000000", "0440440440", "0440440440", "0440440440", "0000000000")
    want_rival = _grid("0000000000", "0004000440", "0444440440", "0004000440", "0000000000")
    want_correct = _grid("0000000000", "0444444440", "0444444440", "0444444440", "0000000000")

    def apply(bridge, program, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")

    with RacketBridge() as bridge:
        for axis in ("horizontal", "vertical"):
            orient = (lambda grid: grid) if axis == "horizontal" else (lambda grid: [list(row) for row in zip(*grid)])
            assert apply(bridge, rules.counterfactual_program(axis, "first_bridge"), orient(chain)) == orient(want_rival)
            assert apply(bridge, rules.program({"join_axis": axis}), orient(chain)) == orient(want_correct)
        assert apply(bridge, rules.counterfactual_program("none", "first_bridge"), chain) == chain


def test_first_group_rival_completes_first_chain_but_ignores_the_second_chain():
    rules = _rules()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    chains = _grid("0000000000", "0440440440", "0440440440", "0440440440", "0000000000",
                   "0440440440", "0440440440", "0440440440", "0000000000")
    want_rival = _grid("0000000000", "0444444440", "0444444440", "0444444440", "0000000000",
                       "0440440440", "0440440440", "0440440440", "0000000000")
    want_correct = _grid("0000000000", "0444444440", "0444444440", "0444444440", "0000000000",
                         "0444444440", "0444444440", "0444444440", "0000000000")

    def apply(bridge, program, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")

    with RacketBridge() as bridge:
        for axis in ("horizontal", "vertical"):
            orient = (lambda grid: grid) if axis == "horizontal" else (lambda grid: [list(row) for row in zip(*grid)])
            assert apply(bridge, rules.counterfactual_program(axis, "first_group"), orient(chains)) == orient(want_rival)
            assert apply(bridge, rules.program({"join_axis": axis}), orient(chains)) == orient(want_correct)
        assert apply(bridge, rules.counterfactual_program("none", "first_group"), chains) == chains
