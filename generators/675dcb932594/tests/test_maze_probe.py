"""Independent graph fixtures and evidence-preserving CLI regression."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess
import sys

for ancestor in Path(__file__).resolve().parents:
    support = next((p for p in (ancestor / 'reviewer_support.py',
                               ancestor / 'shared/runtime/reviewer_support.py') if p.is_file()), None)
    if support is not None:
        sys.path.insert(0, str(support.parent))
        break
else:
    raise ImportError('No local reviewer_support.py')

from reviewer_support import find_root

ROOT = find_root(__file__)
TOOL = next(p for p in (ROOT / 'generators/675dcb932594/workspace/maze_probe.py',
                       ROOT / 'puzzle_generators/per_puzzle/675dcb932594/workspace/maze_probe.py')
            if p.is_file())
SPEC = spec_from_file_location('_independent_maze_probe', TOOL)
PROBE = module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def rows(*strings):
    return [[int(v) for v in row] for row in strings]


def test_rich_tie_counts_and_preservation():
    grid = rows('555555', '500005', '502505', '505505', '500035', '555555')
    stats = PROBE.analyze_grid(grid)
    assert stats['shortest_distance'] == 6
    assert stats['shortest_path_count'] == 2
    assert stats['vertical_move_counts'] == [2, 4]
    assert stats['horizontal_move_counts'] == [2, 4]
    assert stats['move_count_pairs_vertical_horizontal'] == [[2, 4], [4, 2]]
    assert stats['union_zero_count'] == 10
    assert stats['preserved_zero_count'] == 1
    assert stats['diagnostic_output'] == rows('555555', '508885', '582585', '585585', '588835', '555555')
    assert grid[1][1] == 0


def test_irregular_wall_has_eight_shortest_paths():
    # A 4x4 interior has C(6,3)=20 monotone corner-to-corner paths.
    # Twelve visit the removed interior cell: C(2,1) * C(4,2) = 12.
    stats = PROBE.analyze_grid(rows('555555', '520005', '505005', '500005', '500035', '555555'))
    assert stats['shortest_distance'] == 6
    assert stats['shortest_path_count'] == 8
    assert stats['vertical_move_counts'] == [3]
    assert stats['union_zero_count'] == 13
    assert stats['preserved_zero_count'] == 0


def test_cli_discovers_checkout_and_refuses_evidence_overwrite(tmp_path):
    output = tmp_path / 'census.json'
    command = [sys.executable, str(TOOL), '--seed', '0', '--per-band', '1', '--out', str(output)]
    first = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert first.returncode == 0, first.stdout + first.stderr
    report = json.loads(output.read_text())
    assert report['rule_hash'] == '1e4fa5a56660'
    assert report['total_requested_draws'] == 3
    assert len(report['canonical_pairs']) == 5
    assert all(p['diagnostic_matches_canonical_label'] for p in report['canonical_pairs'])
    assert all(row['fits_every_labeled_canonical_pair'] for row in report['canonical_shortcut_fit'].values())
    original = output.read_bytes()
    second = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert second.returncode == 2
    assert output.read_bytes() == original
