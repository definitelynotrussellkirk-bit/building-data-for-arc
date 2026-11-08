"""Focused regression tests for generator 3eff273eeb83."""
from __future__ import annotations

import copy
import importlib
import random

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module("puzzle_generators.per_puzzle.3eff273eeb83.generator")


def _grid(rows: list[str]) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


def test_rule_hash_and_every_canonical_pair() -> None:
    pairs = canonical_pairs("3eff273eeb83")
    assert len(pairs) == 7
    assert GEN.RULE_HASH == "3ac43b22416f"
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN._transform(source) == pair["output"]
        assert source == pair["input"]


def test_unit_length_canonical_regression() -> None:
    one_right = _grid(["000", "052", "000"])
    one_up = _grid(["0000000", "0000000", "0002000", "0005000", "0000000"])
    assert GEN.self_check(one_right) == []
    assert GEN.self_check(one_up) == []


def test_self_check_rejects_structural_impostors() -> None:
    impostors = {
        "gapped": _grid(["000000", "025020", "000000", "000000", "000000", "000000"]),
        "two_sided": _grid(["00000", "02520", "00000", "00000", "00000"]),
        "diagonal": _grid(["20000", "05000", "00000", "00000", "00000"]),
        "detached": _grid(["000000", "050022", "000000", "000000", "000000", "000000"]),
        "rotation_oob": _grid(["22500", "00000", "00000", "00000", "00000"]),
        "illegal_color": _grid(["00000", "05200", "00000", "00040", "00000"]),
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_exact_override_observability_and_unknown_rejection() -> None:
    cases = (
        {"line_length": 1},
        {"line_length": 4},
        {"line_direction": "vertical_up"},
        {"line_direction": "horizontal_right"},
        {"size_class": "canonical"},
        {"size_class": "expanded"},
        {"pivot_position": "center"},
        {"pivot_position": "offset"},
        {
            "line_length": 4,
            "line_direction": "horizontal_left",
            "size_class": "canonical",
            "pivot_position": "offset",
        },
    )
    for overrides in cases:
        grid = GEN.generate(918273, 7, difficulty="hard", **overrides)
        observed = GEN.observe_overrides(grid)
        assert all(observed[key] == value for key, value in overrides.items())
        assert GEN.self_check(grid) == []

    for bad in ({"unknown": 1}, {"line_length": True}, {"line_length": 5}):
        try:
            GEN.generate(1, 0, **bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid overrides {bad}")


def test_replay_freshness_and_global_rng_purity() -> None:
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(77, 9, difficulty="medium")
    middle = random.getstate()
    second = GEN.generate(77, 9, difficulty="medium")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after


def test_every_three_example_window_spans_both_axes() -> None:
    for start in range(32):
        directions = [GEN.schedule_profile(0, start + offset) for offset in range(3)]
        assert len(set(directions)) == 3
        axes = {"horizontal" if d.startswith("horizontal") else "vertical" for d in directions}
        assert axes == {"horizontal", "vertical"}
