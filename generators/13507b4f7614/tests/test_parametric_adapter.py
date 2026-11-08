"""Behavioral tests for the episode sampler, not the fixed canonical generator."""
from pathlib import Path
import importlib.util
import json
import pytest

PATH = Path(__file__).resolve().parents[1] / 'workspace' / 'parametric' / 'adapter.py'


def load():
    assert PATH.is_file(), 'native episode adapter has not been implemented'
    spec = importlib.util.spec_from_file_location('parametric_13507_sampler_test', PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def key(grid):
    return json.dumps(grid, separators=(',', ':'))


def test_adapter_exists():
    load()


@pytest.mark.parametrize('axis', ['none', 'horizontal', 'vertical'])
@pytest.mark.parametrize('demos,queries', [(2,1), (2,4), (3,4), (6,4)])
def test_independent_counts_distinct_inputs_and_exact_cells(axis, demos, queries):
    adapter = load()
    episode = adapter.generate(17, {'join_axis': axis}, demos, queries)
    assert len(episode['train']) == demos
    assert len(episode['test']) == queries
    inputs = [p['input'] for p in episode['train'] + episode['test']]
    assert len({key(g) for g in inputs}) == demos + queries
    assert all(type(c) is int and c in (0,4) for g in inputs for row in g for c in row)
    assert episode['program_solution'] == adapter.program({'join_axis': axis})


def test_inputs_are_setting_independent_and_prefix_stable():
    adapter = load()
    episodes = [adapter.generate(3, {'join_axis': a}, 3, 4) for a in ('none','horizontal','vertical')]
    for split in ('train', 'test'):
        assert all([p['input'] for p in e[split]] == [p['input'] for p in episodes[0][split]] for e in episodes)
    short = adapter.generate(3, {'join_axis': 'horizontal'}, 2, 1)
    long = adapter.generate(3, {'join_axis': 'horizontal'}, 6, 4)
    assert short['train'] == long['train'][:2]
    assert short['test'] == long['test'][:1]
    assert adapter.generate(3, {'join_axis': 'horizontal'}, 6, 4) == long


@pytest.mark.parametrize('axis', ['none','horizontal','vertical'])
def test_two_demos_identify_setting_without_query_answers(axis):
    adapter = load()
    e = adapter.generate(0, {'join_axis': axis}, 2, 4)
    survivors = [a for a in ('none','horizontal','vertical') if all(
        adapter.RULES.transform(p['input'], a) == p['output'] for p in e['train'])]
    assert survivors == [axis]


@pytest.mark.parametrize('seed', [True, False, 1.0, '1', -1, None])
def test_rejects_noninteger_or_negative_seeds(seed):
    with pytest.raises(ValueError):
        load().generate(seed, {'join_axis': 'none'}, 3, 4)


@pytest.mark.parametrize('demos,queries', [(True,4),(1,4),(7,4),(2.0,4),(3,0),(3,5),(3,True)])
def test_rejects_unsupported_counts(demos, queries):
    with pytest.raises(ValueError):
        load().generate(0, {'join_axis': 'none'}, demos, queries)


@pytest.mark.parametrize('settings', [{}, {'join_axis': 'diagonal'}, {'join_axis': True}, {'join_axis':'none','extra':1}])
def test_rejects_invalid_settings(settings):
    with pytest.raises(ValueError):
        load().generate(0, settings, 3, 4)


def test_large_query_has_real_density_and_contacts_all_canvas_edges():
    adapter = load()
    e = adapter.generate(0, {'join_axis':'horizontal'}, 3, 4)
    g = e['test'][3]['input']
    assert len(g) == len(g[0]) == 30
    assert sum(c == 4 for row in g for c in row) >= 240
    assert any(g[0]) and any(g[-1]) and any(row[0] for row in g) and any(row[-1] for row in g)
    for rows in (range(0,14),range(16,30)):
        for cols in (range(0,14),range(16,30)):
            assert sum(g[r][c] == 4 for r in rows for c in cols) >= 30
    assert len(e['train'][0]['input']) == len(e['train'][0]['input'][0]) == 16


def test_queries_do_not_reuse_any_of_the_six_possible_demonstrations():
    adapter = load()
    for seed in (0,1,17):
        e = adapter.generate(seed, {'join_axis':'none'}, 6,4)
        assert not {key(p['input']) for p in e['train']} & {key(p['input']) for p in e['test']}


def test_first_two_demonstrations_refute_one_bridge_shortcut_in_racket():
    """One-pair joining must be taught before any query asks for a longer chain."""
    adapter = load()
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    repo = PATH.parents[4]
    runtime = repo / 'shared/runtime'
    with _local_imports(runtime, PATH.parent):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity['protected'] is True
            for axis in ('horizontal','vertical'):
                source = adapter.program({'join_axis':axis})
                rival = source.replace('(paint-cells out bridge 4)',
                    '(if (equal? out source) (paint-cells out bridge 4) out)')
                assert rival != source
                for seed in (0,17):
                    e = adapter.generate(seed, {'join_axis':axis}, 2,4)
                    assert any(apply(rival,p['input']) != p['output'] for p in e['train']), (
                        f'{axis} seed={seed}: one-bridge rival survives both demonstrations')
        finally:
            bridge.close()
