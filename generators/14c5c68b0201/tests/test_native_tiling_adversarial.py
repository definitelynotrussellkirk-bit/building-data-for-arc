"""Independent literal and native-runner checks for the tiling-axis adapter.

The oracle uses grid values alone and imports neither the production generator
nor either prototype's parsing or label helpers. Native Racket is authoritative.
"""
from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


ADAPTER = Path(__file__).resolve().parents[1] / "workspace/parametric/adapter.py"
SETTINGS = ("both", "horizontal", "vertical")


def _blank_literal():
    grid = [[8] * 10 for _ in range(8)]
    for r in range(1, 6):
        grid[r][1:7] = [0] * 6
    return grid


LITERAL = _blank_literal()
LITERAL[2][2:5] = [1, 1, 0]
LITERAL[3][2:5] = [0, 1, 1]

# The 2x3 stamp begins one row and column after its 5x6 hole's origin.
# Explicit row values independently establish period and phase expectations.
HAND_BOTH = _blank_literal()
HAND_BOTH[1][1:7] = [1, 0, 1, 1, 0, 1]
HAND_BOTH[2][1:7] = [0, 1, 1, 0, 1, 1]
HAND_BOTH[3][1:7] = [1, 0, 1, 1, 0, 1]
HAND_BOTH[4][1:7] = [0, 1, 1, 0, 1, 1]
HAND_BOTH[5][1:7] = [1, 0, 1, 1, 0, 1]
HAND_HORIZONTAL = _blank_literal()
HAND_HORIZONTAL[2][1:7] = [0, 1, 1, 0, 1, 1]
HAND_HORIZONTAL[3][1:7] = [1, 0, 1, 1, 0, 1]
HAND_VERTICAL = _blank_literal()
HAND_VERTICAL[1][2:5] = [0, 1, 1]
HAND_VERTICAL[2][2:5] = [1, 1, 0]
HAND_VERTICAL[3][2:5] = [0, 1, 1]
HAND_VERTICAL[4][2:5] = [1, 1, 0]
HAND_VERTICAL[5][2:5] = [0, 1, 1]
HAND_ANSWERS = {
    "both": HAND_BOTH,
    "horizontal": HAND_HORIZONTAL,
    "vertical": HAND_VERTICAL,
}


def _bounds(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _independent_holes(grid):
    counts = Counter(value for row in grid for value in row)
    background, count = counts.most_common(1)[0]
    assert background != 0 and sum(n == count for n in counts.values()) == 1
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value != background}
    holes = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component, pending = {start}, [start]
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        r0, c0, r1, c1 = _bounds(component)
        assert component == {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        colors = {grid[r][c] for r, c in component} - {0, background}
        assert len(colors) == 1
        color = colors.pop()
        stamp_cells = {(r, c) for r, c in component if grid[r][c] == color}
        holes.append(((r0, c0, r1, c1), _bounds(stamp_cells), color))
    return background, holes


def _oracle(grid, policy, *, hole_origin=False):
    """Recover independent components and tile from their colored stamp cells."""
    _, holes = _independent_holes(grid)
    result = deepcopy(grid)
    for (r0, c0, r1, c1), (sr0, sc0, sr1, sc1), color in holes:
        height, width = sr1 - sr0 + 1, sc1 - sc0 + 1
        motif = [[grid[r][c] == color for c in range(sc0, sc1 + 1)]
                 for r in range(sr0, sr1 + 1)]
        phase_r, phase_c = (r0, c0) if hole_origin else (sr0, sc0)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if policy == "horizontal" and not sr0 <= r <= sr1:
                    continue
                if policy == "vertical" and not sc0 <= c <= sc1:
                    continue
                if motif[(r - phase_r) % height][(c - phase_c) % width]:
                    result[r][c] = color
    return result


def _native_output(bridge, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


@pytest.fixture(scope="module")
def adapter():
    assert ADAPTER.is_file(), "Native root tiling adapter is not implemented"
    spec = importlib.util.spec_from_file_location("independent_native_tiling_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=10.0, startup_timeout=30.0) as active:
        identity = active.runtime_identity
        assert identity["backend"] == "racket" and identity["protected"] is True
        yield active


@pytest.mark.parametrize("policy", SETTINGS)
def test_literal_has_hand_derived_period_phase_and_axis_answer(adapter, policy):
    assert _oracle(LITERAL, policy) == HAND_ANSWERS[policy]
    assert adapter.solve(LITERAL, {"tiling_axes": policy}) == HAND_ANSWERS[policy]


@pytest.mark.parametrize("policy", SETTINGS)
def test_literal_labels_use_native_rule_wrapping(adapter, bridge, policy):
    actual = _native_output(bridge, adapter.program({"tiling_axes": policy}), LITERAL)
    assert actual == HAND_ANSWERS[policy]


def test_wrong_phase_intermediate_changes_native_answer_and_retains_stamp(adapter, bridge):
    program = adapter.program({"tiling_axes": "both"})
    assert program.count("(modulo (- r sr1) sh)") == 1
    assert program.count("(modulo (- c sc1) sw)") == 1
    wrong = program.replace("(modulo (- r sr1) sh)", "(modulo (- r hole-r1) sh)")
    wrong = wrong.replace("(modulo (- c sc1) sw)", "(modulo (- c hole-c1) sw)")
    actual = _native_output(bridge, wrong, LITERAL)
    assert actual == _oracle(LITERAL, "both", hole_origin=True)
    differences = [(r, c) for r in range(8) for c in range(10)
                   if actual[r][c] != HAND_BOTH[r][c]]
    assert len(differences) == 11
    assert differences[0] == (1, 2)
    assert HAND_BOTH[1][2] == 0 and actual[1][2] == 1
    assert all(actual[r][c] == value for r, row in enumerate(LITERAL)
               for c, value in enumerate(row) if value != 0)


@pytest.mark.parametrize("policy", SETTINGS)
def test_generated_small_and_30_square_labels_preserve_holes_and_original_cells(adapter, bridge, policy):
    settings = {"tiling_axes": policy}
    episode = adapter.generate(17, settings, demos=2, queries=4)
    assert len(episode["train"]) == 2 and len(episode["test"]) == 4
    assert (len(episode["train"][0]["input"]), len(episode["train"][0]["input"][0])) == (8, 10)
    large = [pair for pair in episode["test"]
             if (len(pair["input"]), len(pair["input"][0])) == (30, 30)]
    assert len(large) == 1
    pairs = episode["train"] + episode["test"]
    for pair in pairs:
        assert pair["output"] == _oracle(pair["input"], policy)
    program = adapter.program(settings)
    for pair in episode["train"] + large:
        actual = _native_output(bridge, program, pair["input"])
        assert actual == pair["output"] == _oracle(pair["input"], policy)
        # Every background and original stamp cell survives. Only hole zeros
        # are eligible for new paint, including under the one-axis variants.
        assert all(actual[r][c] == value for r, row in enumerate(pair["input"])
                   for c, value in enumerate(row) if value != 0)
