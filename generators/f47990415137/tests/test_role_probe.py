from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'workspace'))
from check_lesson_roles import score_roles


def test_detects_only_role_with_sole_discriminator():
    pairs = [{'input':[[n]],'output':[[n]]} for n in range(5)]
    rival = lambda grid: [[99]] if grid == [[2]] else grid
    findings, matches = score_roles(pairs, {'conditional':rival})
    assert findings == [{'query_index':2,'rival':'conditional'}]
    assert matches['conditional'] == [True,True,False,True,True]


def test_two_discriminators_survive_any_single_query_rotation():
    pairs = [{'input':[[n]],'output':[[n]]} for n in range(4)]
    rival = lambda grid: [[99]] if grid[0][0] < 2 else grid
    assert score_roles(pairs, {'conditional':rival})[0] == []


def test_equivalent_rival_is_not_query_ambiguity():
    pairs = [{'input':[[0]],'output':[[0]]}]
    assert score_roles(pairs, {'equivalent':lambda grid:grid})[0] == []


@pytest.mark.parametrize('pair_count', [0])
def test_empty_role_evaluation_is_not_a_pass(pair_count):
    with pytest.raises(ValueError, match='empty'):
        score_roles([], {'identity': lambda grid: grid})


def test_missing_rivals_is_not_a_pass():
    with pytest.raises(ValueError, match='rival'):
        score_roles([{'input': [[0]], 'output': [[0]]}], {})


def test_empty_census_is_not_a_pass(tmp_path):
    import hashlib
    import json
    from check_lesson_roles import audit
    source = tmp_path / 'generator.py'
    source.write_text('LESSON_COMPETITORS = {"identity": lambda grid: grid}\n')
    census = tmp_path / 'census.json'
    census.write_text(json.dumps({
        'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'task_id': 'toy', 'rule_source_sha256': 'toy', 'lessons': [], 'per_band': {},
    }))
    with pytest.raises(ValueError, match='empty|missing'):
        audit(census, source)
