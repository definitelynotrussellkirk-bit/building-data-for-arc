from __future__ import annotations

from reviewer_support import find_root, load_selected_generator

TASK_ID = "7b088f161470"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _row_count_rival(grid: list[list[int]]) -> tuple[int, int, int]:
    analysis = GEN._analysis(grid)
    floor_rows = analysis["floor_rows"]
    floor_colors = analysis["floor_colors"]
    counts = []
    for index, color in enumerate(floor_colors[:3]):
        rows_with_color = sum(
            any(cell == color for cell in grid[row])
            for row in range(floor_rows[index] + 1, floor_rows[index + 1])
        )
        counts.append(rows_with_color // 2)
    return tuple(counts)


def test_generalized_lessons_break_row_count_shortcut() -> None:
    """Removing incomplete distractors would let the known rival recover every count."""
    for index, profile in enumerate(GEN.GENERAL_PROFILES):
        grid = GEN.generate(901 + index, 1701 + index, scene_profile=profile)
        analysis = GEN._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["rung_counts"] == GEN.GENERAL_COUNTS[profile]
        assert _row_count_rival(grid) != analysis["rung_counts"]


def test_generalized_scene_stays_within_arc_grid_limit() -> None:
    """Restoring the two-row optional gaps makes this deterministic scene 31 rows tall."""
    grid = GEN.generate(
        78,
        1326,
        difficulty="easy",
        scene_profile="counts_123",
    )
    assert len(grid) <= 30
    assert len(grid[0]) <= 30
