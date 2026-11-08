from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest


TASK_ID = "f7c20cfd443f"
ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_pairs() -> list[dict]:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [pair for split in ("train", "test") for pair in row[split]]
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _demo(grid: list[list[int]]) -> dict:
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "89548e944e39"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_default_distribution_keeps_canonical_anchors_and_controlled_scale_breadth():
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(7000 + index, index, difficulty=difficulty) for index in range(20)]
        expected_cycle = GEN.PROFILE_DIMENSIONS[difficulty]
        assert [
            (len(grid), len(grid[0])) for grid in grids
        ] == [expected_cycle[index % len(expected_cycle)] for index in range(20)]
        assert sum((len(grid), len(grid[0])) == (9, 9) for grid in grids) >= 10
        assert all({value for row in grid for value in row} == {0, 5} for grid in grids)
        assert all(3 <= sum(value == 5 for row in grid for value in row) <= 4 for grid in grids)
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert len({tuple(map(tuple, grid)) for grid in grids}) >= 18


def test_every_sliding_four_demo_window_covers_profiles_and_refutes_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            grids = [
                GEN.generate(2026, start + offset, difficulty=difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            profiles = {
                GEN.schedule_profile(2026, start + offset, difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED)
            }
            assert profiles == set(GEN.SCHEDULE_PROFILES)
            demos = [_demo(grid) for grid in grids[: GEN.EXAMPLES_NEEDED]]
            query = {"input": grids[GEN.EXAMPLES_NEEDED]}
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_each_declared_witness_fires_and_its_named_rival_disagrees():
    grids = [GEN.generate(99, index, difficulty="medium") for index in range(8)]
    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        witness_grid = next((grid for grid in grids if witness(grid)), None)
        assert witness_grid is not None, witness_name
        truth = GEN.rule_mirror(witness_grid)
        for rival_name in GEN.WITNESS_RIVALS[witness_name]:
            assert GEN.SEMANTIC_RIVALS[rival_name](witness_grid) != truth


def test_override_boundaries_round_trip_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (7, 15):
            for grid_w in (7, 15):
                for n_seeds in (1, 4):
                    grid = GEN.generate(
                        1234,
                        grid_h + grid_w + n_seeds,
                        difficulty=difficulty,
                        grid_h=grid_h,
                        grid_w=grid_w,
                        n_seeds=n_seeds,
                    )
                    assert GEN.observe_overrides(grid) == {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_seeds": n_seeds,
                    }
                    assert GEN.strict_canonical_like(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(777, 13, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(777, 13, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    first[0][0] = 9
    assert first != second


def test_self_check_rejects_structural_and_marker_grammar_mutations():
    blank = [[0] * 9 for _ in range(9)]
    wrong_color = GEN.generate(17, 0)
    wrong_color[0][0] = 2
    touching = [[0] * 9 for _ in range(9)]
    touching[4][4] = touching[4][5] = 5
    too_many = [[0] * 9 for _ in range(9)]
    for r, c in ((0, 0), (0, 3), (3, 0), (3, 3), (6, 6)):
        too_many[r][c] = 5
    ragged = GEN.generate(18, 1)
    ragged[0].pop()

    for grid in (blank, wrong_color, touching, too_many, ragged):
        assert GEN.self_check(grid), grid


def test_profiles_isolate_the_intended_counterexample_without_confounds():
    def seeds(grid):
        return [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 5
        ]

    def on_edge(grid, cell):
        r, c = cell
        return r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1)

    def halos_overlap(cells):
        return any(
            max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 2
            for index, a in enumerate(cells)
            for b in cells[index + 1 :]
        )

    for difficulty in ("easy", "medium", "hard"):
        for cycle in range(12):
            for offset, profile in enumerate(GEN.SCHEDULE_PROFILES):
                index = cycle * len(GEN.SCHEDULE_PROFILES) + offset
                grid = GEN.generate(4100 + cycle, index, difficulty=difficulty)
                cells = seeds(grid)
                assert GEN.schedule_profile(4100 + cycle, index, difficulty) == profile
                if profile == "canonical_anchor":
                    assert all(r % 3 == 1 and c % 3 == 1 for r, c in cells)
                    assert not any(on_edge(grid, cell) for cell in cells)
                    assert not halos_overlap(cells)
                elif profile == "off_lattice":
                    assert any(r % 3 != 1 or c % 3 != 1 for r, c in cells)
                    assert not any(on_edge(grid, cell) for cell in cells)
                    assert not halos_overlap(cells)
                elif profile == "edge_clip":
                    assert any(on_edge(grid, cell) for cell in cells)
                    assert not halos_overlap(cells)
                elif profile == "overlap":
                    assert not any(on_edge(grid, cell) for cell in cells)
                    assert halos_overlap(cells)
                else:  # pragma: no cover - protects schedule expansion
                    raise AssertionError(profile)
