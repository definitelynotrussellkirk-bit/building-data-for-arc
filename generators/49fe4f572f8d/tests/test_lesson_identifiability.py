from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

MODULE_PATH = REPO_ROOT / "generators" / "49fe4f572f8d" / "generator.py"
SPEC = importlib.util.spec_from_file_location("lesson_generator_49fe4f572f8d", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


EXPECTED_COMPETITORS = {
    "identity",
    "reverse_column_order",
    "freeze_bottom_supported_columns",
    "cap_three_cells_per_column",
    "unique_colors_only_gravity",
    "max_seven_cells_only",
    "max_three_columns_only",
    "canonical_profile_only",
    "canonical_shape_only",
    "five_plus_colors_only",
}


def _pair(seed: int, sample_index: int, band: str) -> dict[str, list[list[int]]]:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN._gravity_down(grid)}


def _observed_scope(grid: list[list[int]]) -> tuple[int, int, int, int, int]:
    foreground = [value for row in grid for value in row if value]
    occupied_columns = sum(
        any(grid[row][column] for row in range(len(grid)))
        for column in range(len(grid[0]))
    )
    return (
        len(grid),
        len(grid[0]),
        len(foreground),
        occupied_columns,
        len(set(foreground)),
    )


def test_boundary_slots_jointly_leave_every_canonical_scope_limit():
    assert hasattr(GEN, "LESSON_COMPETITORS"), (
        "the generator declares EXAMPLES_NEEDED but has no lesson competitor contract"
    )
    assert EXPECTED_COMPETITORS <= set(GEN.LESSON_COMPETITORS)
    assert "beyond_canonical_scope" in GEN.SEMANTIC_WITNESSES

    for band in ("easy", "medium", "hard"):
        for slot in (1, 5, 9):
            grid = GEN.generate(20261003, slot, difficulty=band)
            # One joint boundary lesson refutes five scope-restricted rules:
            # canonical profiles/shapes, <=7 cells, <=3 columns, and >=5 colors.
            assert _observed_scope(grid) == (10, 10, 10, 4, 2)
            assert GEN.SEMANTIC_WITNESSES["beyond_canonical_scope"](grid)


def test_every_five_demo_window_refutes_every_declared_competitor():
    assert hasattr(GEN, "lesson_identifiable"), (
        "EXAMPLES_NEEDED=5 is currently unverified at lesson level"
    )
    assert hasattr(GEN, "LESSON_COMPETITORS")

    # Check every cyclic schedule residue, every difficulty band, and multiple
    # layouts. A five-demo window must identify the rule before a sixth query.
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 91, 20261003):
            for start in range(10):
                pairs = [_pair(seed, start + offset, band) for offset in range(6)]
                demos, query = pairs[:5], pairs[5]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    seed,
                    start,
                    GEN.lesson_identifiable(demos, query),
                )
                for name, competitor in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(pair["input"]) != pair["output"]
                        for pair in demos
                    ), (band, seed, start, name)


def test_deep_schedule_slots_guarantee_a_four_cell_column():
    # Production-path replay that exposed the old weighted-but-not-guaranteed
    # deep scene: hard, seed 104871007183328, sample_index 883 (slot 3).
    cases = [
        ("hard", 104871007183328, 883),
        ("easy", 0, 3),
        ("medium", 1, 7),
        ("hard", 20261003, 13),
        ("easy", 91, 17),
    ]
    for band, seed, sample_index in cases:
        grid = GEN.generate(seed, sample_index, difficulty=band)
        column_counts = [
            sum(grid[row][column] != 0 for row in range(len(grid)))
            for column in range(len(grid[0]))
        ]
        assert max(column_counts) >= 4, (band, seed, sample_index, column_counts)
        assert GEN.SEMANTIC_WITNESSES["gravity_handles_four_plus_cells"](grid)
