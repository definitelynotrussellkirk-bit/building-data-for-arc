"""Keep the supplemental verifier's enumeration complete and portable."""
import importlib.util
from pathlib import Path
from reviewer_support import find_root

ROOT = find_root(__file__)
TASK = '28268c57c367'
PATH = next(p for p in (
    ROOT/'generators'/TASK/'workspace'/'review_probe.py',
    ROOT/'puzzle_generators'/'per_puzzle'/TASK/'workspace'/'review_probe.py',
) if p.is_file())
SPEC = importlib.util.spec_from_file_location('ray_review_probe', PATH)
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_joint_boundary_product_is_complete_and_legal():
    cases = list(PROBE.joint_boundary_pins())
    assert len(cases) == 504
    assert len({tuple(sorted(p.items())) for p in cases}) == 504
    for p in cases:
        assert len(p) == 7
        assert p['wall_col'] <= p['grid_w'] - 2
        assert 1 <= p['n_distinct_colors'] <= p['n_cells'] <= 6
    assert {'grid_h': 5, 'grid_w': 7, 'wall_col': 5, 'n_cells': 6,
            'n_distinct_colors': 6, 'n_gray': 3, 'n_right': 3} in cases


def test_each_cyclic_start_holds_out_every_position():
    rows = list(PROBE.rotation_splits(2))
    assert len(rows) == 8
    assert {(r['start'], r['query']) for r in rows} == {
        (s, q) for s in range(2) for q in range(s, s+4)}
    for row in rows:
        assert row['query'] not in row['demonstrations']
        assert len(row['demonstrations']) == 3
        assert set(row['demonstrations']) | {row['query']} == set(range(row['start'],row['start']+4))
