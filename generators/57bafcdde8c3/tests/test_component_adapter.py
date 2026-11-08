"""Literal component semantics and setting-neutral promotion inputs."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys
import types

import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]
SOURCE=HOME/'workspace/parametric/adapter.py'
SHAPES={'A':(0,[(1,1),(2,2)]),'B':(3,[(1,7),(1,8),(1,9)]),
        'C':(4,[(6,1),(6,2),(7,1),(7,2)]),'D':(5,[(6,7),(7,8),(8,9)]),
        'G':(2,[(5,5),(6,5)]),'H':(9,[(7,7),(8,8),(9,9),(10,10)])}


def adapter():
    spec=importlib.util.spec_from_file_location('_component_adapter_test',SOURCE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def literal():
    value=[[1]*12 for _ in range(12)]
    for color,points in SHAPES.values():
        for r,c in points:value[r][c]=color
    value[10][4]=0;value[10][8]=6;value[10][9]=7
    return value


@pytest.fixture(scope='module')
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    with RacketBridge() as bridge:
        assert bridge.runtime_identity['backend']=='racket' and bridge.runtime_identity['protected'] is True
        def apply(program,value):
            text="'("+' '.join('('+' '.join(map(str,row))+')' for row in value)+')'
            return bridge.eval_text('('+wrap_rule(program)+' '+text+')')
        yield apply


@pytest.mark.parametrize('threshold,connectivity,paint',[(2,4,'BCG'),(3,4,'BC'),(4,4,'C'),
    (2,8,'ABCDGH'),(3,8,'BCDH'),(4,8,'CH')])
def test_hand_counted_components_match_exact_programs(racket,threshold,connectivity,paint):
    module=adapter();value=literal();expected=deepcopy(value)
    for name in paint:
        for r,c in SHAPES[name][1]:expected[r][c]=8
    assert racket(module.program({'min_size':threshold,'connectivity':connectivity}),value)==expected
    assert value==literal()


def test_default_program_is_exact_canonical_authority():
    canonical={row['program_solution'] for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
               if (row:=json.loads(line))['task_id']=='57bafcdde8c3'}
    assert canonical=={adapter().program({'min_size':2,'connectivity':4})}


def test_settings_share_inputs_and_queries_do_not_depend_on_demo_count():
    module=adapter();before=random.getstate()
    episodes=[module.generate(17,{'min_size':threshold,'connectivity':connectivity},3,4)
              for threshold in [2,3,4] for connectivity in [4,8]]
    inp=lambda episode:[p['input'] for p in episode['train']+episode['test']]
    assert all(inp(ep)==inp(episodes[0]) for ep in episodes)
    assert random.getstate()==before
    smaller=module.generate(17,{'min_size':2,'connectivity':4},2,4)
    assert [p['input'] for p in smaller['test']]==[p['input'] for p in episodes[0]['test']]
    shapes=[(len(p['input']),len(p['input'][0])) for p in episodes[0]['test']]
    assert shapes==[(13,13),(16,20),(24,24),(30,30)]
    prefix=module.generate(17,{'min_size':2,'connectivity':4},3,1)
    assert prefix['test']==episodes[0]['test'][:1]


def test_shared_demos_distinguish_all_settings_and_reject_wrong_shortcuts():
    module=adapter();prototype=module._prototype
    extras={k:v for k,v in prototype.GEN.SEMANTIC_RIVALS.items() if k!='eight_connected'}
    for settings in prototype.SETTINGS:
        episode=module.generate(0,settings,2,4)
        assert prototype.fit_demos(episode['train'])==[settings]
        for name,rival in extras.items():
            assert any(rival(p['input'])!=p['output'] for p in episode['train']),name


@pytest.mark.parametrize('seed,demos,queries',[(-1,3,4),(True,3,4),(0,1,4),(0,2,0),(0,2,9)])
def test_direct_adapter_enforces_promotion_request_bounds(seed,demos,queries):
    with pytest.raises(ValueError):adapter().generate(seed,{'min_size':2,'connectivity':4},demos,queries)


def test_maximum_counts_are_distinct_and_do_not_use_a_foreign_cached_module(monkeypatch):
    monkeypatch.setitem(sys.modules,'components',types.ModuleType('components'))
    module=adapter();episode=module.generate(0,{'min_size':4,'connectivity':8},8,8)
    assert len(episode['train'])==len(episode['test'])==8
    assert len({json.dumps(p['input']) for p in episode['train']+episode['test']})==16
    assert {(len(p['input']),len(p['input'][0])) for p in episode['test']}=={(13,13),(16,20),(20,16),(24,24),(30,30)}


def test_every_rule_has_positive_action_for_both_foregrounds_and_backgrounds():
    module=adapter();episode=module.generate(2,{'min_size':4,'connectivity':4},2,4)
    for setting in module._prototype.SETTINGS:
        for background in [1,7]:
            assert any(module._prototype._grid(p['input'])==background
                       and module._prototype.transform(p['input'],setting)!=p['input'] for p in episode['train'])
        for foreground in [0,3]:
            assert any(foreground in {c for row in p['input'] for c in row}
                       and module._prototype.transform(p['input'],setting)!=p['input'] for p in episode['train'])


def test_query_palettes_are_not_fixed_by_grid_shape():
    module=adapter();backgrounds=[set() for _ in range(4)];foregrounds=[set() for _ in range(4)]
    for seed in range(16):
        episode=module.generate(seed,{'min_size':2,'connectivity':4},2,4)
        for index,pair in enumerate(episode['test']):
            bg=module._prototype._grid(pair['input']);colors={c for row in pair['input'] for c in row}
            backgrounds[index].add(bg);foregrounds[index].update(colors-{bg})
    assert all(values=={1,7} for values in backgrounds)
    assert all(values=={0,3} for values in foregrounds)
