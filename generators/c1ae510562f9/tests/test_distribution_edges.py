"""Boundary support and a measurable difficulty effect on ordinary draws."""
import importlib.util
import json

from reviewer_support import find_root


ROOT = find_root(__file__)
SOURCE = ROOT / "generators/c1ae510562f9/generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators/per_puzzle/c1ae510562f9/generator.py"
SPEC = importlib.util.spec_from_file_location("edge_test_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def test_difficulty_changes_canvas_distribution():
    totals = {}
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(17, i, difficulty=band) for i in range(24)]
        totals[band] = (sum(len(g) for g in grids), sum(len(g[0]) for g in grids))
    assert totals["easy"][0] < totals["hard"][0], totals
    assert totals["easy"][1] < totals["hard"][1], totals


def test_generated_empty_counts_cover_zero_through_saturation():
    outputs = set()
    spiral = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2),
              (2, 1), (2, 0), (1, 0), (1, 1))
    for count in range(11):
        grid = GEN.generate(17, count, grid_h=16, grid_w=6,
                            interior_h=max(2, count + 1), interior_w=2,
                            empty_rows=count)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid)["empty_rows"] == count
        expected = [[0] * 3 for _ in range(3)]
        for r, c in spiral[:min(count, 9)]:
            expected[r][c] = 8
        outputs.add(json.dumps(expected))
    assert len(outputs) == 10


def test_validator_rejects_broken_floor_and_exterior_cyan():
    grid = GEN.generate(17, 0, grid_h=9, grid_w=9,
                        interior_h=4, interior_w=3, empty_rows=2)
    gray = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    floor = max(r for r, _ in gray)
    left = min(c for _, c in gray)
    broken = [row[:] for row in grid]
    broken[floor][left + 1] = 0
    assert GEN.self_check(broken)
    outside = [row[:] for row in grid]
    blank_row = next(r for r, row in enumerate(grid) if not any(row))
    outside[blank_row][0] = 8
    assert GEN.self_check(outside)


def test_validator_reports_malformed_input_without_crashing():
    for grid in (None, [], [None], [[]], [[0], [0, 0]], [[True]],
                 [["5"]], [[5.0]], [[5]], [[0, 0], [0, 0]]):
        assert GEN.self_check(grid)


def test_invalid_difficulty_scalars_are_rejected():
    for value in ("__invalid_difficulty__", "HARD", True, 1, 1.0):
        try:
            GEN.generate(17, 3, difficulty=value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid difficulty {value!r}")

def test_seed_and_sample_index_require_exact_integer_provenance():
    for value in (True, False, 1.0, 1.75, "1"):
        try:
            GEN.generate(value, 3)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid seed {value!r}")

    for value in (True, False, -1, 1.0, "1"):
        try:
            GEN.generate(17, value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid sample_index {value!r}")

    # Negative literal integer seeds remain valid deterministic provenance.
    assert GEN.generate(-17, 3) == GEN.generate(-17, 3)
