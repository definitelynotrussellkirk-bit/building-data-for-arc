"""Focused semantic regressions for generator fe03db1e1459."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


TASK_ID = "fe03db1e1459"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
AUTHORITY = ROOT / (
    "data/base/solutions/banks/ce088a50599a/M155__fe03db1e1459.json"
)
BANDS = ("easy", "medium", "hard")


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_all_canonical_pairs_are_accepted_strict_and_exact():
    row = _canonical_row()
    pairs = [*row["train"], row["test"]]
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_rule_pin_and_all_task_local_authorities_are_exactly_synchronized():
    canonical = _canonical_row()["program_solution"]
    authority = json.loads(AUTHORITY.read_text())
    target = authority["racket_target"]
    assert GEN.RULE_HASH == "b6f49ccc5f81"
    assert GEN.RULE_HASH == _normalized_hash(canonical)
    assert target["target_code"] == canonical
    assert target["raw_code"] == canonical
    assert target["target_code_role"] == "selected_task_rule"
    assert target["raw_code_role"] == "archival_executable_source"


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("grid_h", [9, 11])
@pytest.mark.parametrize("grid_w", [12, 15])
@pytest.mark.parametrize("blue_object_size", [4, 6])
@pytest.mark.parametrize("marker_dr", [-1, 2])
@pytest.mark.parametrize("marker_dc", [-3, 2])
def test_full_boundary_override_product_is_exact(
    band, grid_h, grid_w, blue_object_size, marker_dr, marker_dc
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "blue_object_size": blue_object_size,
        "marker_dr": marker_dr,
        "marker_dc": marker_dc,
    }
    grid = GEN.generate(8127, 41, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested


def test_interior_zero_components_are_supported_but_zero_vector_rejects():
    for band in BANDS:
        horizontal = GEN.generate(
            111, 7, difficulty=band, marker_dr=0, marker_dc=1
        )
        vertical = GEN.generate(
            112, 8, difficulty=band, marker_dr=1, marker_dc=0
        )
        assert GEN.observe_overrides(horizontal)["marker_dr"] == 0
        assert GEN.observe_overrides(vertical)["marker_dc"] == 0
        with pytest.raises(ValueError, match="no displacement"):
            GEN.generate(
                113, 9, difficulty=band, marker_dr=0, marker_dc=0
            )


def test_default_distribution_cycles_every_linked_profile_in_every_band():
    for band in BANDS:
        profiles = set()
        witnesses = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        grids = set()
        for sample_index in range(75):
            grid = GEN.generate(30_000 + sample_index, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            obs = GEN.semantic_observables(grid)
            profiles.add(obs["linked_profile_index"])
            grids.add(_freeze(grid))
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                witnesses[name] += bool(predicate(grid))
        assert profiles == set(range(5))
        assert all(count > 0 for count in witnesses.values())
        assert len(grids) >= 72


def test_self_check_rejects_targeted_semantic_impostors():
    base = GEN.generate(4001, 1, difficulty="medium")

    foreign_output_color = copy.deepcopy(base)
    zero = next(
        (r, c)
        for r, row in enumerate(foreign_output_color)
        for c, value in enumerate(row)
        if value == 0
    )
    foreign_output_color[zero[0]][zero[1]] = 8
    assert any("foreign/output" in e for e in GEN.self_check(foreign_output_color))

    duplicate_marker = copy.deepcopy(base)
    zero = next(
        (r, c)
        for r, row in enumerate(duplicate_marker)
        for c, value in enumerate(row)
        if value == 0
    )
    duplicate_marker[zero[0]][zero[1]] = 2
    assert any("exactly one color-2" in e for e in GEN.self_check(duplicate_marker))

    disconnected = copy.deepcopy(base)
    blue = [
        (r, c)
        for r, row in enumerate(disconnected)
        for c, value in enumerate(row)
        if value == 1
    ]
    disconnected[blue[0][0]][blue[0][1]] = 0
    zero = next(
        (r, c)
        for r, row in enumerate(disconnected)
        for c, value in enumerate(row)
        if value == 0
        and all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in blue[1:])
    )
    disconnected[zero[0]][zero[1]] = 1
    assert any("4-connected" in e for e in GEN.self_check(disconnected))

    wrong_morphology = [[0] * 12 for _ in range(9)]
    for c in range(4):
        wrong_morphology[4][3 + c] = 1
    wrong_morphology[1][1] = 2
    wrong_morphology[2][1] = 3
    assert any("morphology" in e for e in GEN.self_check(wrong_morphology))

    clipped = [[0] * 12 for _ in range(9)]
    for r, c in GEN._L4:
        clipped[7 + r][c] = 1
    clipped[1][1] = 2
    clipped[3][3] = 3
    assert any("in bounds" in e for e in GEN.self_check(clipped))


def test_negative_recombination_is_not_strict_but_oracle_can_execute():
    grid = GEN.generate(5001, 0, difficulty="easy")
    p2 = next(
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2
    )
    p3 = next(
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3
    )
    grid[p3[0]][p3[1]] = 0
    # Replace the profile-1 (1,0) vector with a lawful but noncanonical linked
    # recombination (1,1). The replacement cue exists only in the marker pair.
    replacement = (p2[0] + 1, p2[1] + 1)
    assert grid[replacement[0]][replacement[1]] == 0
    grid[replacement[0]][replacement[1]] = 3
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid)
    output = GEN.rule_mirror(grid)
    assert output != grid
    assert any(8 in row for row in output)


def test_lesson_windows_rebut_plausible_competitors():
    for band in BANDS:
        for start in range(10):
            pairs = []
            for offset in range(4):
                grid = GEN.generate(6100 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_determinism_fresh_returns_and_process_global_rng_isolation():
    random.seed(20260724)
    state = random.getstate()
    first = GEN.generate(9123, 4567, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(9123, 4567, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert GEN.generate(9123, 4567, difficulty="hard") == second


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, texture="canonical")
