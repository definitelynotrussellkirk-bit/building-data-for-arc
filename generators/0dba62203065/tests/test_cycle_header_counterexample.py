from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_DIR.parents[1]
for path in (REPO_ROOT, REPO_ROOT / "src", REPO_ROOT / "shared" / "runtime"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

MODULE_PATH = TASK_DIR / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_0dba62203065_cycle_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _cycle_from_first_two(grid: list[list[int]]) -> list[list[int]]:
    """Rival: infer the whole legend from its first two cells, ignoring later cells."""
    colors = tuple(range(2, 9))
    start = colors.index(grid[0][0])
    if grid[0][1] == colors[(start + 1) % len(colors)]:
        step = 1
    elif grid[0][1] == colors[(start - 1) % len(colors)]:
        step = -1
    else:
        raise AssertionError("first two header cells must preserve the base cycle")
    inferred = [colors[(start + step * col) % len(colors)] for col in range(len(grid[0]))]

    output = [row[:] for row in grid]
    for cells in GEN._components(grid):
        left = min(col for _, col in cells)
        for row, col in cells:
            output[row][col] = inferred[left]
    return output


def test_anchor_swap_legend_profile_forces_actual_header_lookup() -> None:
    grid = GEN.generate(77, 1, difficulty="medium")

    assert GEN.self_check(grid) == []
    assert GEN.observe_legend_profile(grid) == "anchor_swap"
    assert _cycle_from_first_two(grid) != GEN.rule_mirror(grid)


def test_two_demo_schedule_declares_and_refutes_cycle_shortcut() -> None:
    demos = []
    profiles = []
    for sample_index in (0, 1):
        grid = GEN.generate(991, sample_index, difficulty="medium")
        truth = GEN.rule_mirror(grid)
        demos.append({"input": grid, "output": truth})
        profiles.append(GEN.observe_legend_profile(grid))

    assert profiles == ["cyclic", "anchor_swap"]
    assert "cycle_from_first_two" in GEN.SEMANTIC_RIVALS
    assert GEN.SEMANTIC_RIVALS["cycle_from_first_two"](demos[0]["input"]) == demos[0]["output"]
    assert GEN.SEMANTIC_RIVALS["cycle_from_first_two"](demos[1]["input"]) != demos[1]["output"]
    assert GEN.SEMANTIC_WITNESSES["row_one_body"](demos[1]["input"])
    assert "cycle_from_first_two" in GEN.WITNESS_RIVALS["row_one_body"]

    query_grid = GEN.generate(991, 2, difficulty="medium")
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []


def test_anchor_swap_preserves_first_cell_counterexample() -> None:
    grid = GEN.generate(110_043, 43, difficulty="medium")

    assert GEN.observe_legend_profile(grid) == "anchor_swap"
    assert GEN.SEMANTIC_RIVALS["first_cell_column"](grid) != GEN.rule_mirror(grid)


def test_anchor_swap_search_tries_all_valid_partners() -> None:
    """Regression: semantic census found a valid swap after a rejected first draw."""
    grid = GEN.generate(
        225_536_731_915_187,
        4037,
        difficulty="easy",
    )

    assert GEN.self_check(grid) == []
    assert GEN.observe_legend_profile(grid) == "anchor_swap"
    assert GEN.SEMANTIC_RIVALS["cycle_from_first_two"](grid) != GEN.rule_mirror(grid)
    assert GEN.SEMANTIC_RIVALS["first_cell_column"](grid) != GEN.rule_mirror(grid)
