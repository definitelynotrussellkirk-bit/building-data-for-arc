"""A literal causal regression: orient first, then measure the top edge."""
import importlib.util
from pathlib import Path


def test_normalized_edge_ranking_changes_order_after_rotation():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
    assert path.is_file(), "the parameterized object-ranker is missing"
    spec = importlib.util.spec_from_file_location("ef03216cf2fa_literal", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    grid = [
        [1,1,0,0,2,2,2,0,0,0],
        [1,0,0,0,2,0,0,0,0,0],
        [1,0,0,0,2,2,2,2,2,0],
        [1,0,0,0,0,0,0,0,0,0],
        [1,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0],
        [3,3,3,3,0,0,0,0,0,0],
        [3,0,0,0,0,0,0,0,0,0],
    ]
    wanted = [
        [1,1,1,1,1], [0,0,0,0,1], [0,0,0,0,0],
        [3,3,3,3,0], [3,0,0,0,0], [0,0,0,0,0],
        [2,2,2,0,0], [2,0,0,0,0], [2,2,2,2,2],
    ]
    assert module.solve(grid, "normalized_top_edge") == wanted
    assert module.solve(grid, "perimeter") != wanted
    assert module.solve(grid, "normalized_top_edge", "source_top_edge") != wanted
