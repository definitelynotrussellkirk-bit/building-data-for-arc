from __future__ import annotations
import copy, json, sys
from pathlib import Path
import pytest

BASE=Path(__file__).resolve().parents[1]
PARAM=BASE/'workspace'/'parametric'
sys.path.insert(0,str(PARAM))
import prototype as p


def test_declares_exact_three_branch_settings():
    assert p.SETTINGS == ('split_both','clockwise_only','counterclockwise_only')

def test_canonical_default_is_split_both():
    assert p.CANONICAL_SETTING == 'split_both'

def test_clockwise_rotation():
    assert p.clockwise((0,1)) == (1,0)

def test_counterclockwise_rotation():
    assert p.counterclockwise((0,1)) == (-1,0)

def test_empty_grid_is_preserved():
    assert p.solve([], 'split_both') == []

def test_split_both_reaches_both_sides_of_each_wall():
    grid=p.make_scene(0)
    out=p.solve(grid,'split_both')
    assert p.converted_targets(grid,out) >= 4

def test_clockwise_and_counterclockwise_choose_different_targets():
    grid=p.make_scene(1)
    assert p.solve(grid,'clockwise_only') != p.solve(grid,'counterclockwise_only')

def test_all_settings_are_pairwise_distinct_on_scene():
    grid=p.make_scene(2)
    outs=[p.solve(grid,s) for s in p.SETTINGS]
    assert len({json.dumps(x) for x in outs}) == 3

def test_scene_generation_is_deterministic():
    assert p.make_scene(17) == p.make_scene(17)

def test_scene_uses_only_task_colors():
    assert {v for row in p.make_scene(3) for v in row} <= {0,3,7,8}

def test_scene_has_exactly_two_adjacent_seed_cells():
    assert p.is_lawful_scene(p.make_scene(4))

def test_episode_inputs_do_not_depend_on_hidden_setting():
    episodes=[p.build_episode(11,s) for s in p.SETTINGS]
    inputs=[[x['input'] for x in e['demonstrations']]+[e['query']['input']] for e in episodes]
    assert inputs[0] == inputs[1] == inputs[2]

def test_episode_contains_three_demonstrations_and_one_query():
    e=p.build_episode(5,'split_both')
    assert len(e['demonstrations']) == 3 and set(e['query']) >= {'input','output'}

def test_every_retained_pair_identifies_setting():
    e=p.build_episode(6,'split_both')
    for item in e['demonstrations']+[e['query']]:
        outs=[p.solve(item['input'],s) for s in p.SETTINGS]
        assert len({json.dumps(x) for x in outs}) == 3

def test_public_projection_hides_only_query_label():
    e=p.build_episode(7,'clockwise_only')
    public=p.public_projection(e)
    assert 'output' not in public['query']
    assert all('output' in d for d in public['demonstrations'])

def test_private_episode_retains_query_label():
    assert 'output' in p.build_episode(8,'counterclockwise_only')['query']

def test_canonical_program_snapshot_is_exact_extraction():
    extracted=p.extract_canonical_program()
    snap=(PARAM/'racket'/'canonical-source.rkt').read_text()
    assert snap == extracted

def test_racket_files_exist_for_each_setting():
    for s in p.SETTINGS:
        assert (PARAM/'racket'/f'{s}.rkt').is_file()

@pytest.mark.parametrize('setting',p.SETTINGS)
def test_racket_matches_python(setting):
    grid=p.make_scene(9)
    assert p.run_racket(grid,setting) == p.solve(grid,setting)

def test_canonical_training_pairs_match_default_when_available():
    checked,mismatches=p.check_canonical_training()
    assert checked >= 1
    assert mismatches == []
