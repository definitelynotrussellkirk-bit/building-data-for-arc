"""Regressions for lawful contact boundaries and shortcut-resistant lessons."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
TASK = "366cda05b486"
GENERATOR = next(path for path in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("contact_contract_subject", GENERATOR)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

DIAGONAL = [[1, 3, 0, 0, 0], [0, 3, 4, 0, 0], [0, 0, 0, 8, 7]]
DIAGONAL_OUTPUT = [[8, 8, 0], [0, 8, 8]]


def _parts(grid):
    """Independent color-blind cardinal flood fill for observable scene roles."""
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, color in enumerate(row) if color != 0}
    groups = []
    while remaining:
        start = min(remaining)
        todo, group = [start], {start}
        remaining.remove(start)
        while todo:
            r, c = todo.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in remaining:
                    remaining.remove(q)
                    group.add(q)
                    todo.append(q)
        groups.append(group)
    return groups


def _cyan_role(grid):
    groups = _parts(grid)
    selected = next(group for group in groups if any(grid[r][c] == 1 for r, c in group))
    distractor = next(group for group in groups if group is not selected)
    return (any(grid[r][c] == 8 for r, c in selected),
            any(grid[r][c] == 8 for r, c in distractor))


def test_canonical_inputs_pass_without_privileged_metadata():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert MODULE.self_check(pair["input"]) == []


@pytest.mark.parametrize("case", ["selected_cyan", "repeated_color", "diagonal"])
def test_reference_lawful_boundaries_are_accepted(case):
    pairs = canonical_pairs(TASK, root=ROOT)
    if case == "selected_cyan":
        grid = [[8 if v == 3 else v for v in row] for row in pairs[0]["input"]]
        expected = pairs[0]["output"]
    elif case == "repeated_color":
        grid = [[3 if v == 7 else v for v in row] for row in pairs[1]["input"]]
        expected = pairs[1]["output"]
    else:
        grid, expected = copy.deepcopy(DIAGONAL), DIAGONAL_OUTPUT
    assert MODULE.self_check(grid) == []
    assert MODULE.expected_output(grid) == expected


def test_racket_confirms_the_three_boundary_outputs():
    from arc_repl.racket_bridge import RacketBridge

    with canonical_path(ROOT).open() as handle:
        source = next(json.loads(line)["program_solution"] for line in handle
                      if json.loads(line).get("task_id") == TASK)
    pairs = canonical_pairs(TASK, root=ROOT)
    cases = [
        ([[8 if v == 3 else v for v in row] for row in pairs[0]["input"]], pairs[0]["output"]),
        ([[3 if v == 7 else v for v in row] for row in pairs[1]["input"]], pairs[1]["output"]),
        (DIAGONAL, DIAGONAL_OUTPUT),
    ]
    bridge = RacketBridge()
    try:
        for grid, expected in cases:
            literal = "'( " + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            body = source.strip()[len("(rule!"):-1]
            assert bridge.eval_text(f"(let ([g {literal}]) {body})") == expected
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_retain_canonical_profiles_in_every_band(band):
    profiles = {(len(pair["input"]), len(pair["input"][0]),
                 len({v for row in pair["input"] for v in row}))
                for pair in canonical_pairs(TASK, root=ROOT)}
    hits = 0
    for i in range(20):
        seed = int(hashlib.sha256(f"profile-floor:v1:{TASK}:{band}:{i}".encode()).hexdigest()[:12], 16)
        grid = MODULE.generate(seed, seed % 7919 + i, difficulty=band)
        observed = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        hits += observed in profiles
    assert hits >= 1, f"no canonical profile in {band}'s pinned 20 draws"


def test_default_curriculum_decouples_cyan_from_selection():
    roles = {_cyan_role(MODULE.generate(419, index, difficulty="medium"))
             for index in range(16)}
    assert roles == {(False, False), (False, True), (True, False), (True, True)}


def test_default_curriculum_includes_cardinal_and_diagonal_near_contacts():
    diagonal = 0
    separate = 0
    for i in range(16):
        grid = MODULE.generate(419, i, difficulty="medium")
        left, right = _parts(grid)
        touching = any((r + dr, c + dc) in right for r, c in left
                       for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)))
        diagonal += touching
        separate += not touching
    assert diagonal > 0
    assert separate > 0


def test_missing_lesson_witness_is_rejected_and_demonstration_repairs_it():
    assert callable(getattr(MODULE, "lesson_identifiable", None)), "missing production lesson guard"
    example = canonical_pairs(TASK, root=ROOT)[0]
    query = {"input": [[1, 3, 0, 0, 0, 5, 5, 5],
                       [0, 3, 4, 0, 0, 5, 5, 6],
                       [0, 0, 0, 0, 0, 6, 6, 6]],
             "output": DIAGONAL_OUTPUT}
    assert any("largest" in reason for reason in MODULE.lesson_identifiable([example] * 3, query))
    # Once this same distinction is shown, no rival that predicts it wrongly
    # can still fit every demonstration. This checks answers, not a metadata bit.
    assert MODULE.lesson_identifiable([example, query, example], query) == []


def test_diagonal_witness_refutes_eight_connected_rival():
    rivals = getattr(MODULE, "SEMANTIC_RIVALS", {})
    assert "eight_connected" in rivals, "missing connectivity rival"
    assert rivals["eight_connected"](DIAGONAL) != DIAGONAL_OUTPUT


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_consecutive_defaults_refute_object_count_selection(band):
    # A default curriculum must teach the blue cue when the distractor owns
    # more monochromatic objects, not leave that case override-only.
    for start in range(6):
        reversed_counts = False
        for index in range(start, start + 3):
            grid = MODULE.generate(419, index, difficulty=band)
            groups = _parts(grid)
            selected = next(group for group in groups if any(grid[r][c] == 1 for r, c in group))
            distractor = next(group for group in groups if group is not selected)
            selected_colors = {grid[r][c] for r, c in selected}
            distractor_colors = {grid[r][c] for r, c in distractor}
            reversed_counts |= len(distractor_colors) > len(selected_colors)
        assert reversed_counts, f"object-count cue never refuted in {band} start={start}"


def test_count_rival_detects_canonical_fitting_shortcut():
    assert "most_objects" in getattr(MODULE, "LESSON_COMPETITORS", {}), "missing count rival"
    demos = canonical_pairs(TASK, root=ROOT)
    grid = MODULE.generate(419, 0, difficulty="medium", cluster_components=3,
                           distractor_components=4, seed_size=1, grid_h=9, grid_w=12)
    query = {"input": grid, "output": MODULE.expected_output(grid)}
    assert any("most_objects" in reason for reason in MODULE.lesson_identifiable(demos, query))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_pair_default_windows_keep_witnesses_after_query_rotation(band):
    for seed in (0, 419):
        pairs = []
        for index in range(8):
            grid = MODULE.generate(seed, index, difficulty=band)
            pairs.append({"input": grid, "output": MODULE.expected_output(grid)})
        for start in range(5):
            window = pairs[start:start + 4]
            for held_out in range(4):
                demos = [pair for i, pair in enumerate(window) if i != held_out]
                assert MODULE.lesson_identifiable(demos, window[held_out]) == [], (
                    f"lost a unique witness: band={band},seed={seed},start={start},query={held_out}")


@pytest.mark.parametrize("overrides", [{"not_an_axis": 1}, {"seed_size": True},
                                      {"cluster_components": 3.9}, {"grid_h": "9"}])
def test_invalid_or_unknown_exact_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(13, 2, difficulty="easy", **overrides)
