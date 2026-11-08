"""Mixed supported row containers must not crash canonical validation."""
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import canonical_pairs, load_generator  # noqa: E402

GEN = load_generator()


@pytest.mark.parametrize("outer_container", [list, tuple])
@pytest.mark.parametrize("tuple_border", [0, -1])
def test_mixed_border_row_types_preserve_canonical_scene(outer_container, tuple_border):
    pair = canonical_pairs()[0]
    grid = [list(row) for row in pair["input"]]
    grid[tuple_border] = tuple(grid[tuple_border])
    grid = outer_container(grid)

    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN._solve(grid) == pair["output"]


@pytest.mark.parametrize("damaged_border", [0, -1])
@pytest.mark.parametrize("tuple_border", [0, -1])
def test_invalid_border_in_mixed_row_grid_is_diagnostic(damaged_border, tuple_border):
    grid = [list(row) for row in canonical_pairs()[0]["input"]]
    grid[damaged_border][1] = (grid[0][0] + 1) % 10
    grid[tuple_border] = tuple(grid[tuple_border])

    errors = GEN.self_check(grid)
    assert any("top and bottom borders" in error for error in errors)
    assert GEN.strict_canonical_like(grid) == errors
