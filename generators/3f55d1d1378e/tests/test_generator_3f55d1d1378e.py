"""Focused regression tests for generator 3f55d1d1378e."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "3f55d1d1378e"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.3f55d1d1378e.generator"
)


def _canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return [*row["train"], *row["test"]]
    raise AssertionError("canonical task not found")


def _clear_component(grid, obj):
    for r, c in obj["cells"]:
        grid[r][c] = 0


def _paint_shape(grid, obj, shape, color=None):
    r0, c0, _, _ = obj["bbox"]
    color = int(obj["color"] if color is None else color)
    for r, c in shape:
        grid[r0 + r][c0 + c] = color


def test_rule_hash_and_translation_only_semantics_are_pinned():
    assert GEN.RULE_HASH == "d14af3f6ff73"
    grid = GEN.generate(101, 0, difficulty="easy")
    assert GEN.schedule_profile(101, 0, "easy") == "rotation_trap"
    assert GEN._solve_exact(grid) != GEN._solve_dihedral(grid)
    assert GEN._solve_exact(grid) != GEN._solve_count_only(grid)


def test_all_canonical_inputs_are_accepted_and_solved_by_exact_duplicates():
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN._solve_exact(pair["input"]) == pair["output"]

    fitting_rivals = {
        name
        for name, rival in GEN.SEMANTIC_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in pairs)
    }
    assert fitting_rivals == {
        "same_cell_count",
        "same_up_to_rotation_or_reflection",
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == fitting_rivals


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_all_public_axis_boundaries_are_exactly_observable(difficulty):
    for h in (9, 14):
        for w in (13, 18):
            for duplicate_count in (2, 3):
                for unique_count in (1, 2):
                    grid = GEN.generate(
                        202,
                        5,
                        difficulty=difficulty,
                        grid_h=h,
                        grid_w=w,
                        duplicate_count=duplicate_count,
                        unique_count=unique_count,
                    )
                    assert GEN.observe_overrides(grid) == {
                        "grid_h": h,
                        "grid_w": w,
                        "duplicate_count": duplicate_count,
                        "unique_count": unique_count,
                    }
                    assert GEN.self_check(grid) == []


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)


def test_self_check_rejects_four_structural_impostors():
    base = GEN.generate(
        303,
        2,
        difficulty="medium",
        duplicate_count=2,
        unique_count=2,
    )
    assert GEN.self_check(base) == []
    comps = GEN._components(base)
    counts = {}
    for obj in comps:
        counts.setdefault(obj["key"], []).append(obj)
    duplicate_group = next(group for group in counts.values() if len(group) == 2)
    unique_group = [group[0] for group in counts.values() if len(group) == 1]

    # 1. Remove one duplicate: every remaining shape is unique.
    no_repeat = copy.deepcopy(base)
    _clear_component(no_repeat, duplicate_group[0])
    assert any("repeated shape class" in err for err in GEN.self_check(no_repeat))

    # 2. Turn the sole repeated pair into an identity scene by repainting every
    # unique object as the repeated shape (all objects now survive).
    all_repeat = copy.deepcopy(base)
    for obj in unique_group:
        _clear_component(all_repeat, obj)
        _paint_shape(all_repeat, obj, duplicate_group[0]["key"])
    assert GEN.self_check(all_repeat)

    # 3. Recolor a separate object to reuse another object's color.
    reused_color = copy.deepcopy(base)
    source, target = comps[0], comps[-1]
    for r, c in target["cells"]:
        reused_color[r][c] = int(source["color"])
    assert any("distinct non-zero color" in err for err in GEN.self_check(reused_color))

    # 4. Add an illegal ARC color.
    bad_color = copy.deepcopy(base)
    bad_color[0][0] = 12
    assert any("invalid ARC colors" in err for err in GEN.self_check(bad_color))


def test_three_consecutive_profiles_refute_every_named_rival_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(404, i, difficulty=difficulty) for i in range(3)]
        assert {
            GEN.schedule_profile(404, i, difficulty) for i in range(3)
        } == set(GEN.SCHEDULE_PROFILES)
        for witness in GEN.SEMANTIC_WITNESSES.values():
            assert any(witness(grid) for grid in grids)

        demos = [
            {"input": grid, "output": GEN._solve_exact(grid)}
            for grid in grids
        ]
        query_grid = GEN.generate(404, 3, difficulty=difficulty)
        query = {"input": query_grid, "output": GEN._solve_exact(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(505, 2, difficulty="hard")
    second = GEN.generate(505, 2, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
