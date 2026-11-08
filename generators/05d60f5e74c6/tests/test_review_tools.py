"""Small pure-function regressions for the retained review tooling."""
from pathlib import Path
import importlib.util
import sys

WORKSPACE = Path(__file__).resolve().parents[1] / 'workspace'
sys.path.insert(0, str(WORKSPACE))
import audit_targets
import review_probe


def test_audit_success_is_not_failed_merely_because_axes_were_tested():
    decision = getattr(audit_targets, 'has_verified_findings', None)
    assert callable(decision), 'audit exit needs an explicit outcome predicate'
    move = {'ambiguous_lessons': [], 'generation_or_parity_failures': [], 'boundary_failures': []}
    top = {'count_mismatches': [], 'ignored_axes': [
        {'same_input_count': 0, 'total': 20}, {'same_input_count': 3, 'total': 20}]}
    assert not decision(move, top)
    top['ignored_axes'][0]['same_input_count'] = 20
    assert decision(move, top)


def test_input_only_geometry_distinguishes_cardinal_and_diagonal_contact():
    grid = [[1, 1, 0], [0, 0, 1], [0, 0, 1]]
    assert len(review_probe.components(grid)) == 2
    assert len(review_probe.components(grid, diagonal=True)) == 1
    assert review_probe.scene_features(grid)['same_color_diagonal_join']


def test_audit_rivals_are_independent_and_do_not_mutate_input():
    grid = [[1, 0, 0], [1, 0, 0], [0, 1, 1]]
    before = [r[:] for r in grid]
    assert audit_targets.recolor_eight_connected(grid) == [[4, 0, 0], [4, 0, 0], [0, 4, 4]]
    assert grid == before
