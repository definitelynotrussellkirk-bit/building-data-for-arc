"""Focused regressions for the repaired rectangle-overlap generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
TASK_ID = "600284beb8e4"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GEN = _load(HOME / "generator.py", "generator_600284beb8e4_under_test")


def _canonical_row() -> dict:
    with (REPO / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _pairs(row: dict) -> list[dict]:
    test = row["test"]
    return [*row["train"], *(test if isinstance(test, list) else [test])]


def _hash(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def _bbox(grid: list[list[int]], color: int) -> tuple[int, int, int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    assert cells
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def test_rule_pin_and_canonical_pairs_are_exact() -> None:
    row = _canonical_row()
    assert GEN.RULE_HASH == "0460c3a13fef"
    assert GEN.RULE_HASH == _hash(row["program_solution"])
    assert len(_pairs(row)) == 3
    for pair in _pairs(row):
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_controls_are_observable_in_every_band(difficulty: str) -> None:
    for relation in GEN.RELATIVE_POSITIONS:
        for edge_mode in GEN.EDGE_MODES:
            grid = GEN.generate(
                41,
                7,
                difficulty=difficulty,
                grid_h=16,
                grid_w=18,
                relative_position=relation,
                edge_mode=edge_mode,
            )
            assert GEN.self_check(grid) == []
            observed = GEN.observe_controls(grid)
            assert observed == {
                "grid_h": 16,
                "grid_w": 18,
                "relative_position": relation,
                "edge_mode": edge_mode,
            }


def test_distribution_covers_both_color_orders_and_crossed_roles() -> None:
    observed = set()
    for index in range(240):
        grid = GEN.generate(70_000 + index, index, difficulty="medium")
        assert GEN.self_check(grid) == []
        observed.add(GEN.observe_controls(grid)["relative_position"])
    assert observed == set(GEN.RELATIVE_POSITIONS)

    north = GEN.generate(1, 1, relative_position="2_north")
    south = GEN.generate(1, 1, relative_position="2_south")
    west = GEN.generate(1, 1, relative_position="2_west")
    east = GEN.generate(1, 1, relative_position="2_east")
    assert _bbox(north, 2)[0] < _bbox(north, 3)[0]
    assert _bbox(south, 2)[0] > _bbox(south, 3)[0]
    assert _bbox(west, 2)[1] < _bbox(west, 3)[1]
    assert _bbox(east, 2)[1] > _bbox(east, 3)[1]


def test_rule_mirror_refutes_the_reported_north_south_shortcut() -> None:
    # The retained rival is expected to survive scenes whose vertical spans
    # happen to match its north/south construction.  These three crossed-role
    # layouts are the constructive counterexamples that actually distinguish
    # it from bbox intersection.
    for relation in ("2_south", "2_horizontal", "2_vertical"):
        grid = GEN.generate(900, 3, relative_position=relation, edge_mode="boundary")
        assert GEN.rule_mirror(grid) != GEN.north_south_shortcut(grid)


def test_request_contract_rejects_coercions_unknowns_and_invalid_difficulty() -> None:
    bad_calls = [
        lambda: GEN.generate(True, 0),
        lambda: GEN.generate(1, False),
        lambda: GEN.generate(1.0, 0),
        lambda: GEN.generate(1, "0"),
        lambda: GEN.generate(1, -1),
        lambda: GEN.generate(1, 0, difficulty="expert"),
        lambda: GEN.generate(1, 0, typo_axis=3),
        lambda: GEN.generate(1, 0, grid_h=True),
        lambda: GEN.generate(1, 0, grid_w=12.0),
        lambda: GEN.generate(1, 0, relative_position=2),
        lambda: GEN.generate(1, 0, edge_mode=False),
    ]
    for call in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            call()


def test_self_check_rejects_targeted_structural_impostors() -> None:
    base = GEN.generate(22, 5, grid_h=12, grid_w=14, relative_position="2_south")
    assert GEN.self_check(base) == []

    missing = copy.deepcopy(base)
    for r, row in enumerate(missing):
        for c, value in enumerate(row):
            if value == 3:
                missing[r][c] = 0
    assert GEN.self_check(missing)

    disjoint = [[0] * 10 for _ in range(10)]
    GEN._draw_border(disjoint, 0, 0, 3, 3, 2)
    GEN._draw_border(disjoint, 6, 6, 9, 9, 3)
    assert GEN.self_check(disjoint)

    interior = copy.deepcopy(base)
    r0, c0, r1, c1 = _bbox(interior, 2)
    if r1 - r0 >= 2 and c1 - c0 >= 2:
        interior[r0 + 1][c0 + 1] = 2
        assert GEN.self_check(interior)

    malformed = copy.deepcopy(base)
    malformed[0].append(0)
    assert GEN.self_check(malformed)

    typed = copy.deepcopy(base)
    typed[0][0] = False
    assert GEN.self_check(typed)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(20261026)
    before = random.getstate()
    first = GEN.generate(77, 12, difficulty="hard")
    middle = GEN.generate(78, 13, difficulty="easy")
    second = GEN.generate(77, 12, difficulty="hard")
    assert random.getstate() == before
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(77, 12, difficulty="hard") == second
    assert middle != second
