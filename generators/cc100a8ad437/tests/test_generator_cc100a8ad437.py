from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GENERATOR_PATH = REPO / "generators" / "cc100a8ad437" / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_cc100a8ad437", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_ordinary_matches_use_independent_arbitrary_offsets(difficulty: str) -> None:
    """Do not teach an origin-anchored template-height/width scan shortcut."""
    for sample_index in range(12):
        grid = GEN.generate(
            seed=0xCC100 + sample_index,
            sample_index=sample_index,
            difficulty=difficulty,
        )
        left, board, _ = GEN._split_input(grid)
        _, shape, color = GEN._crop_template(left)
        hits = GEN._match_positions(board, shape, color)
        shape_h, shape_w = GEN._dims(shape)
        residues = {(row % shape_h, col % shape_w) for row, col in hits}

        assert len(hits) >= 2
        assert len(residues) >= 2, (
            difficulty,
            sample_index,
            hits,
            (shape_h, shape_w),
        )
        assert any(row % shape_h or col % shape_w for row, col in hits)


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_sliding_four_demo_window_refutes_named_shortcuts(
    difficulty: str,
) -> None:
    expected_rivals = {"literal_zero_matching", "dihedral_matching", "origin_lattice_scan"}
    assert set(GEN.SEMANTIC_RIVALS) == expected_rivals
    assert set(GEN.LESSON_COMPETITORS) == expected_rivals

    for start in range(6):
        demos = [_pair(7000 + start, index, difficulty) for index in range(start, start + 4)]
        query = _pair(9000 + start, start + 4, difficulty)

        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                difficulty,
                start,
                name,
            )

@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_scheduled_canonical_anchor_is_present_in_every_band(difficulty: str) -> None:
    """Each curriculum band must retain a deterministic exact canonical-scale draw."""
    grid = GEN.generate(seed=0xC0FFEE, sample_index=4, difficulty=difficulty)
    profile = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    assert profile in {(6, 12, 3), (7, 12, 3), (7, 13, 3)}
    assert GEN.observe_overrides(grid)["shape_size"] == 5
    assert GEN.observe_overrides(grid)["n_inst"] == 2

@pytest.mark.parametrize("grid_h", (6, 7, 8))
def test_partial_small_board_overrides_adapt_unspecified_shape_and_count(
    grid_h: int,
) -> None:
    """Valid dimension overrides must not fail because random defaults overpack them."""
    for seed in range(30):
        grid = GEN.generate(
            seed=seed,
            sample_index=seed,
            difficulty="hard",
            grid_h=grid_h,
            board_w=8,
        )
        assert len(grid) == grid_h
        assert len(grid[0]) == 12
