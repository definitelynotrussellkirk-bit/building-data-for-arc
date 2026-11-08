"""Test the retained findings-only reproducers independently of Racket startup."""
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'workspace'))
from review_probe import canonical_pairs


def normalized(grid):
    return [[int(v) for v in row] for row in grid]


def test_frame_components_and_bbox_rival_fit_canonical():
    from audit_worker import frame_components, fill_bbox_rival
    for p in canonical_pairs('79fa065ed7aa'):
        g = normalized(p['input'])
        assert len(frame_components(g)) == 2
        assert fill_bbox_rival(g) == normalized(p['output'])


def test_broken_border_is_visible_to_geometry_probe():
    from audit_worker import frame_components
    g = normalized(canonical_pairs('79fa065ed7aa')[0]['input'])
    g[1][2] = 0
    components = frame_components(g)
    assert len(components) == 2
    assert sum(not item['complete_border'] for item in components) == 1


def test_domino_rival_fits_every_canonical_pair():
    from audit_worker import rightmost_only
    for p in canonical_pairs('d1e7fb6c23d0'):
        g = normalized(p['input'])
        assert rightmost_only(g) == normalized(p['output'])


def test_two_domino_reproducer_exposes_rightmost_only_shortcut():
    from audit_worker import rightmost_only
    g = [[0, 2, 2, 0, 6, 6, 0]]
    untouched = deepcopy(g)
    assert rightmost_only(g) == [[0, 2, 2, 0, 6, 6, 6]]
    assert g == untouched
