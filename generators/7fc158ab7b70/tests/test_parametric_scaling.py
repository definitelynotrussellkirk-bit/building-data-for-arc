"""Proposed prototype tests; these do not certify canonical generation."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = '7fc158ab7b70'
ROOT = find_root(__file__)
GEN, SOURCE, GENERATOR_HASH = load_selected_generator(TASK, root=ROOT)
PROTOTYPE = ROOT / 'generators' / TASK / 'workspace/parametric/scaling.py'
SPEC = importlib.util.spec_from_file_location('parametric_scaling', PROTOTYPE)
P = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = P
SPEC.loader.exec_module(P)


def test_count_then_replicate_discriminating_witness():
    grid = [[1, 0, 0], [0, 2, 0], [0, 0, 1]]
    shapes = {}
    for setting in P.SETTINGS:
        output = P.predict(grid, setting)
        shapes[setting.name] = (len(output), len(output[0]))
    assert shapes == {
        'cells-both': (9, 9), 'cells-rows': (9, 3),
        'cells-columns': (3, 9), 'colors-both': (6, 6),
        'colors-rows': (6, 3), 'colors-columns': (3, 6),
    }
    assert P.predict(grid, P.Setting('cells', 'rows'))[:3] == [grid[0]] * 3


def test_inputs_deterministic_distinct_lawful_and_contrastive():
    for seed in (0, 17, 42, -2):
        grids = P.generate_inputs(seed, train=3, test=4)
        assert grids == P.generate_inputs(seed, train=3, test=4)
        assert len(grids) == len({P.digest(g) for g in grids}) == 7
        assert all(GEN.self_check(g) == [] for g in grids)
        counts = [P.counts(g) for g in grids[:3]]
        assert counts == [(2, 1), (4, 2), (3, 3)]
        for setting in P.SETTINGS:
            for grid in grids:
                out = P.predict(grid, setting)
                assert 1 <= len(out) <= 30 and 1 <= len(out[0]) <= 30
                assert all(type(c) is int and 0 <= c <= 9 for r in out for c in r)


def test_setting_once_per_episode_and_strict_contracts():
    assert P.choose_setting(17) == P.DEFAULT
    choices = {P.choose_setting(s, seedchoose=True) for s in range(100)}
    assert choices == set(P.SETTINGS)
    assert P.choose_setting(7, seedchoose=True) == P.choose_setting(7, seedchoose=True)
    for invalid in (True, 1.2, '17'):
        with pytest.raises((TypeError, ValueError)):
            P.generate_inputs(invalid, train=3, test=4)
    for train, test in ((1, 4), (7, 4), (3, 0), (True, 4), (3, 5)):
        with pytest.raises((TypeError, ValueError)):
            P.generate_inputs(17, train=train, test=test)
    with pytest.raises(ValueError):
        P.Setting('components', 'both')
    with pytest.raises(ValueError):
        P.Setting('cells', 'diagonal')


def test_canonical_default_equals_selected_mirror_and_examples():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert P.predict(pair['input'], P.DEFAULT) == pair['output']
    for grid in P.generate_inputs(17, train=3, test=4):
        assert P.predict(grid, P.DEFAULT) == GEN.rule_mirror(grid)


@pytest.fixture(scope='module')
def authority():
    with P.RacketLabeler(ROOT) as labeler:
        yield labeler


@pytest.mark.parametrize('setting', P.SETTINGS, ids=lambda s: s.name)
def test_actual_racket_all_pairs_and_demonstrations_identify(setting, authority):
    episode = P.build_episode(17, setting=setting, train=3, test=4, labeler=authority)
    assert episode['setting'] == setting.as_dict()
    assert episode['identification']['demo_survivors'] == [setting.name]
    assert len(episode['pairs']['train']) == 3
    assert len(episode['pairs']['test']) == 4
    assert episode['authority']['backend'] == 'racket'
    assert episode['authority']['rule_sha256'] == P.text_hash(P.racket_source(setting))
    assert episode['canonical_parity']['all_equal']
    for pair in episode['pairs']['train'] + episode['pairs']['test']:
        assert pair['output'] == P.predict(pair['input'], setting)
    assert all(not q['ambiguous_rivals'] for q in episode['identification']['queries'])
    # Removing a contrastive demo can leave axis ambiguity for color-count one.
    mono = episode['pairs']['train'][:1]
    survivors = P.identify_demonstrations(mono, authority)
    if setting.count_basis == 'colors':
        assert survivors == ['colors-both', 'colors-rows', 'colors-columns']
    # Query answers are not accepted by the identification function at all.
    changed = json.loads(json.dumps(episode))
    changed['pairs']['test'][0]['output'] = [[9]]
    assert P.identify_demonstrations(changed['pairs']['train'], authority) == [setting.name]


def test_public_challenge_leaks_no_params_program_or_query_answers(authority):
    episode = P.build_episode(41, train=4, test=4, labeler=authority)
    public = P.public_challenge(episode)
    assert set(public) == {'train', 'test'}
    assert all(set(p) == {'input', 'output'} for p in public['train'])
    assert all(set(p) == {'input'} for p in public['test'])
    assert len(public['test']) == 4 and len(public['train']) == 4
    assert public['train'] == episode['pairs']['train']
    assert len({P.digest(p['input']) for p in public['train'] + public['test']}) == 8


def test_setting_explicit_values_are_never_silently_defaulted():
    for bad in ('', False, 0):
        with pytest.raises(ValueError):
            P.choose_setting(17, count_basis=bad)
        with pytest.raises(ValueError):
            P.choose_setting(17, scale_axes=bad)
    with pytest.raises(ValueError):
        P.choose_setting(17, count_basis='cells', seedchoose=True)


def test_racket_backed_writer_regression(authority, tmp_path):
    """The corrected writer path is exercised with actual protected labels."""
    exporter = P._exporter()
    assert authority.runtime_identity['protected'] is True
    for setting in P.SETTINGS:
        four = P.build_episode(17, setting=setting, train=2, test=4, labeler=authority)
        one = P.build_episode(17, setting=setting, train=2, test=1, labeler=authority)
        full_export = exporter.export_episode(tmp_path, four)
        single_export = exporter.export_episode(tmp_path, one)
        assert full_export['turns'][0] == single_export['turns'][0]
        for entry in [full_export['public_archive'], *full_export['turns']]:
            path = tmp_path / entry['path']
            assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
            assert setting.name not in entry['path']
        changed = json.loads(json.dumps(four))
        changed['seed'] = 123456789
        changed['setting'] = {'private': 'changed'}
        changed['authority']['rule_text'] = 'PRIVATE CHANGED PROGRAM'
        changed['pairs']['test'][0]['output'] = [[9]]
        changed_export = exporter.export_episode(tmp_path, changed)
        for key in ('public_id', 'public_archive', 'turn_ids', 'turns'):
            assert changed_export[key] == full_export[key]
        for index, entry in enumerate(full_export['turns']):
            turn = json.loads((tmp_path / entry['path']).read_bytes())
            assert set(turn) == {'train', 'test'}
            assert turn['test'] == [{'input': four['pairs']['test'][index]['input']}]
