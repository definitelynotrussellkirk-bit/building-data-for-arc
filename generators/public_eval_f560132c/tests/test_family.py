from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import random
import sys
import pytest
from reviewer_support import find_root

ROOT = find_root(Path(__file__))
HOME = ROOT / 'generators/public_eval_f560132c'


def load(name: str):
    path = HOME / ('generator.py' if name == 'generator' else f'workspace/parametric/{name}.py')
    assert path.is_file(), f'missing implementation: {path}'
    spec = importlib.util.spec_from_file_location(f'f560132c_test_{name}', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def originals():
    challenge = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['f560132c']
    gold = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['f560132c']
    rows = challenge['train'] + [{'input': p['input'], 'output': o} for p, o in zip(challenge['test'], gold)]
    return [
        {
            'input': [[int(v) for v in row] for row in pair['input']],
            'output': [[int(v) for v in row] for row in pair['output']],
        }
        for pair in rows
    ]


@pytest.mark.parametrize('pair', originals())
def test_all_official_labels(pair):
    p = load('prototype')
    assert p.solve(pair['input'], 'pack_only') == pair['output']
    assert p.self_check(pair['input']) == []


def test_exact_canonical_copy_and_literal_rule_id():
    a = load('adapter')
    g = load('generator')
    assert g.RULE_TASK_ID == 'ee_f560132c'
    assert a.program({'finish_rule': 'pack_only'}) == (HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes() == (HOME/'workspace/parametric/canonical.rkt').read_bytes()


@pytest.mark.parametrize('seed', [0, 1, 17, 43])
def test_counts_prefixes_matched_inputs(seed):
    a = load('adapter')
    p = load('prototype')
    full = a.generate(seed, {'finish_rule': 'pack_only'}, 6, 4)
    other = a.generate(seed, {'finish_rule': 'highlight_hub'}, 6, 4)
    assert [x['input'] for s in ('train', 'test') for x in full[s]] == [x['input'] for s in ('train', 'test') for x in other[s]]
    assert all(x['output'] != y['output'] for x, y in zip(full['train'], other['train']))
    for demos in range(2, 7):
        for queries in range(1, 5):
            e = a.generate(seed, {'finish_rule': 'pack_only'}, demos, queries)
            assert e['train'] == full['train'][:demos]
            assert e['test'] == full['test'][:queries]
            assert len(e['train']) == demos and len(e['test']) == queries
            assert e['program_solution'] == a.program({'finish_rule': 'pack_only'})
            fingerprints = [json.dumps(x['input'], separators=(',', ':')) for s in ('train', 'test') for x in e[s]]
            assert len(fingerprints) == len(set(fingerprints))
            for s in ('train', 'test'):
                for pair in e[s]:
                    assert p.self_check(pair['input']) == []
                    assert p.solve(pair['input'], 'pack_only') == pair['output']
    big = next(x['input'] for x in a.BANKS[0].generate(seed, {'finish_rule': 'pack_only'},6,4)['test'] if len(x['input']) == len(x['input'][0]) == 30)
    assert sum(v != 0 for row in big for v in row) >= 250


@pytest.mark.parametrize('seed', [0, 5, 17, 43])
def test_minimum_lesson_identifies_setting_and_hub_not_largest(seed):
    a = load('adapter')
    p = load('prototype')
    canonical = a.generate(seed, {'finish_rule': 'pack_only'}, 2, 4)
    alternate = a.generate(seed, {'finish_rule': 'highlight_hub'}, 2, 4)
    assert any(x['output'] != y['output'] for x, y in zip(canonical['train'], alternate['train']))
    for pair in alternate['train']:
        decoded = p.decode(pair['input'])
        assert decoded['hub_piece'] != decoded['largest_piece']
        assert any(v == 1 for row in pair['output'] for v in row)


@pytest.mark.parametrize('settings', [None, {}, {'finish_rule': 'bad'}, {'finish_rule': True}, {'finish_rule': 'pack_only', 'x': 1}])
def test_invalid_settings(settings):
    with pytest.raises((TypeError, ValueError)):
        load('adapter').program(settings)


@pytest.mark.parametrize('seed,demos,queries', [
    (True,2,4), (-1,2,4), (0,1,4), (0,7,4), (0,2,0), (0,2,5), (0,2,True), (0,2.0,4),
])
def test_invalid_request(seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        load('adapter').generate(seed, {'finish_rule': 'pack_only'}, demos, queries)


@pytest.mark.parametrize('bad', [None, [], [[]], [[True]], [[1.0]], [[-1]], [[10]], [[0],[0,1]], [[0]*31]])
def test_invalid_grids(bad):
    p = load('prototype')
    with pytest.raises((TypeError, ValueError)):
        p.solve(bad)
    assert p.self_check(bad)


def test_public_projection_is_single_query_and_private_invariant():
    a = load('adapter')
    e = a.generate(17, {'finish_rule': 'highlight_hub'}, 3, 4)
    one = a.generate(17, {'finish_rule': 'highlight_hub'}, 3, 1)
    visible = a.public_bytes(e, 0)
    assert visible == a.public_bytes(one, 0)
    parsed = json.loads(visible)
    assert parsed == {'train': e['train'], 'test': [{'input': e['test'][0]['input']}]}
    changed = copy.deepcopy(e)
    changed['settings'] = {'private': True}
    changed['program_solution'] = 'PRIVATE'
    changed['query_source_indices'] = ['PRIVATE']
    for pair in changed['test']:
        pair['output'] = {'private': True}
    changed['test'][1:] = [{'invalid_future': True}]
    assert a.public_bytes(changed, 0) == visible
    changed = copy.deepcopy(e)
    changed['test'][0]['input'][0][0] = (changed['test'][0]['input'][0][0] + 1) % 10
    assert a.public_bytes(changed, 0) != visible


def test_query_presentation_is_shuffled_and_rng_is_local():
    a = load('adapter')
    before = random.getstate()
    orders = {tuple(a.generate(seed, {'finish_rule': 'pack_only'}, 2, 4)['query_source_indices']) for seed in range(16)}
    assert random.getstate() == before
    assert len(orders) > 5 and any(order[0] != 0 for order in orders)


def test_wrong_intermediate_changes_large_query():
    a = load('adapter')
    p = load('prototype')
    e = a.generate(17, {'finish_rule': 'highlight_hub'}, 6, 4)
    pair = next(x for x in a.BANKS[0].generate(17, {'finish_rule':'highlight_hub'},6,4)['test'] if len(x['input']) == len(x['input'][0]) == 30)
    wrong = p.solve(pair['input'], 'highlight_largest')
    assert wrong != pair['output']
    assert sum(a != b for ra, rb in zip(wrong, pair['output']) for a, b in zip(ra, rb)) >= 20


def test_production_entry_is_relocatable(tmp_path):
    import shutil
    copy_home = tmp_path/'public_eval_f560132c'
    shutil.copytree(HOME, copy_home, ignore=shutil.ignore_patterns('__pycache__', 'tests', 'evidence'))
    spec = importlib.util.spec_from_file_location('relocated_f560', copy_home/'generator.py')
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    first = mod.generate(29, 0)
    assert first == mod.generate(29, 0) and mod.self_check(first) == []
    assert mod.generate(29, 1) != first
    with pytest.raises(ValueError): mod.generate(29, 0, unknown=1)


def test_decoding_is_shared_across_finish_rules(monkeypatch):
    p = load('prototype')
    grid = p.scene(0, 0)
    calls = 0
    real_pack = p._pack

    def counted_pack(pieces):
        nonlocal calls
        calls += 1
        return real_pack(pieces)

    monkeypatch.setattr(p, '_pack', counted_pack)
    p._solve_cached.cache_clear()
    p._decode_cached.cache_clear()
    p.solve(grid, 'pack_only')
    p.solve(grid, 'highlight_hub')
    assert calls == 1


def test_verifier_rejects_stale_source(tmp_path):
    import hashlib
    verify = load('verify')
    source = tmp_path/'source.py'
    source.write_text('value = 1\n')
    binding = {'files': [{'path': 'source.py', 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}]}
    verify.check_binding(tmp_path, binding)
    source.write_text('value = 2\n')
    with pytest.raises(ValueError, match='Source binding'):
        verify.check_binding(tmp_path, binding)


def test_racket_sources_are_single_complete_forms():
    from arc_repl.parser import parse_all
    for name in ('canonical.rkt', 'highlight_hub.rkt', 'highlight_largest.rkt', 'highlight_key.rkt'):
        forms = parse_all((HOME/'workspace/parametric'/name).read_text())
        assert len(forms) == 1, name
