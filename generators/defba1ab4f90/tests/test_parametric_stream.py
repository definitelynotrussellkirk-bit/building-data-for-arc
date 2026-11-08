"""Parametric stream contract: exact authority, total routes and teaching evidence."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / 'workspace' / 'parametric'


def load():
    path = PARAMETRIC / 'adapter.py'
    assert path.is_file(), 'native stream adapter has not been implemented'
    spec = importlib.util.spec_from_file_location('tested_stream_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture():
    grid = [[0] * 14 for _ in range(12)]
    grid[0][5] = 2
    for r, start, color in [(2, 4, 1), (4, 6, 3), (4, 1, 1), (6, 4, 1)]:
        grid[r][start:start + 3] = [color] * 3
    return grid


def test_exact_canonical_authority_and_meaningful_alternate():
    a = load()
    from reviewer_support import canonical_pairs, find_root
    root = find_root(__file__)
    sources = {json.loads(line)['program_solution']
               for line in (root / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
               if json.loads(line).get('task_id') == 'defba1ab4f90'}
    assert sources == {a.program({'handedness': 'canonical'})}
    assert a.program({'handedness': 'reversed'}) not in sources
    for pair in canonical_pairs('defba1ab4f90', root=root):
        assert a.core.trace(pair['input'], {'handedness': 'canonical'})[0] == pair['output']


def test_literal_causal_witness_matches_hand_derived_path():
    a = load(); grid = fixture(); original = deepcopy(grid)
    out, events = a.core.trace(grid, {'handedness': 'canonical'})
    wanted = {(0, 5), (1, 5), (1, 6), (1, 7), (2, 7), (3, 7),
              (3, 6), (3, 5), (4, 5), (5, 5), (5, 6), (5, 7)}
    wanted.update((r, 7) for r in range(6, 12))
    assert {(r, c) for r, row in enumerate(out) for c, x in enumerate(row) if x == 2} == wanted
    assert [(e['row'], e['column'], e['color'], e['exit_column']) for e in events] == [(2, 5, 1, 7), (4, 7, 3, 5), (6, 5, 1, 7)]
    changed, _ = a.core.trace(grid, {'handedness': 'canonical'}, rival='always_blue')
    assert changed != out
    assert changed[11][9] == 2 and out[11][7] == 2
    assert grid == original


@pytest.mark.parametrize('demos', [2, 3, 6])
@pytest.mark.parametrize('seed', [0, 17])
def test_counts_matched_inputs_distinctness_and_teaching(seed, demos):
    a = load()
    left = a.generate(seed, {'handedness': 'canonical'}, demos, 4)
    right = a.generate(seed, {'handedness': 'reversed'}, demos, 4)
    assert left == a.generate(seed, {'handedness': 'canonical'}, demos, 4)
    assert len(left['train']) == demos and len(left['test']) == 4
    inputs = [p['input'] for p in left['train'] + left['test']]
    assert inputs == [p['input'] for p in right['train'] + right['test']]
    assert len({json.dumps(g) for g in inputs}) == demos + 4
    for settings, episode in [({'handedness': 'canonical'}, left), ({'handedness': 'reversed'}, right)]:
        cert = a.core.teaching_certificate(episode['train'], settings)
        assert cert['surviving_settings'] == [settings]
        assert not cert['surviving_rivals']
        for pair in episode['train'] + episode['test']:
            output, events = a.core.trace(pair['input'], settings)
            assert output == pair['output']
            assert len(events) >= 5
            assert {e['color'] for e in events} == {1, 3}
            assert all(output[r][c] == x for r, row in enumerate(pair['input']) for c, x in enumerate(row) if x in (1, 3))


def test_sequential_public_projection_has_no_private_or_future_data():
    a = load(); settings = {'handedness': 'canonical'}
    many = a.generate(7, settings, 3, 4)
    single = a.generate(7, settings, 3, 1)
    assert a.core.public_turn(many, 0) == a.core.public_turn(single, 0)
    visible = a.core.public_turn(many, 0)
    assert set(visible) == {'train', 'test'} and len(visible['test']) == 1
    assert set(visible['test'][0]) == {'input'}
    private = deepcopy(many)
    private.update(seed=123456, settings={'secret': 9}, program_solution='SECRET')
    for p in private['test']:
        p['output'] = [[9]]
    private['test'][1]['input'] = [[8]]
    assert a.core.public_turn(private, 0) == visible
    from reviewer_support import public_challenge_bytes, public_challenge_id
    assert public_challenge_id(visible) == public_challenge_id(a.core.public_turn(private, 0))
    assert b'SECRET' not in public_challenge_bytes(visible)
    visible['train'][0]['input'][0][0] = 8
    assert many['train'][0]['input'][0][0] != 8


def test_30_square_queries_have_substantive_distributed_content():
    a = load(); episode = a.generate(11, {'handedness': 'canonical'}, 2, 4)
    for pair in episode['test'][-2:]:
        grid = pair['input']
        assert (len(grid), len(grid[0])) == (30, 30)
        cells = [(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x in (1, 3)]
        assert len(cells) >= 90
        assert max(r for r, c in cells) - min(r for r, c in cells) >= 24
        assert max(c for r, c in cells) - min(c for r, c in cells) >= 24
        for mode in ('canonical', 'reversed'):
            out, events = a.core.trace(grid, {'handedness': mode})
            assert len(events) == 12
            assert sum(x == 2 for row in out for x in row) >= 40


@pytest.mark.parametrize('seed,demos,queries,settings', [
    (True, 3, 4, {'handedness': 'canonical'}), (1.5, 3, 4, {'handedness': 'canonical'}),
    ('1', 3, 4, {'handedness': 'canonical'}), (-1, 3, 4, {'handedness': 'canonical'}),
    (2**63, 3, 4, {'handedness': 'canonical'}), (0, True, 4, {'handedness': 'canonical'}),
    (0, 1, 4, {'handedness': 'canonical'}), (0, 7, 4, {'handedness': 'canonical'}),
    (0, 3, 0, {'handedness': 'canonical'}), (0, 3, 5, {'handedness': 'canonical'}),
    (0, 3, 4.0, {'handedness': 'canonical'}), (0, 3, 4, {}),
    (0, 3, 4, {'handedness': True}), (0, 3, 4, {'handedness': 'canonical', 'extra': 1}),
])
def test_malformed_calls_fail_closed(seed, demos, queries, settings):
    a = load()
    with pytest.raises((TypeError, ValueError)):
        a.generate(seed, settings, demos, queries)


def test_teaching_certificate_rejects_corrupt_demonstration():
    a = load(); settings = {'handedness': 'canonical'}
    episode = a.generate(9, settings, 2, 4)
    episode['train'][0]['output'][0][0] = 9
    with pytest.raises(ValueError):
        a.core.teaching_certificate(episode['train'], settings)


def test_all_declared_rules_and_rivals_execute_in_protected_racket():
    a = load()
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import find_root
    apply, identity, bridge = _real_evaluator(find_root(__file__) / 'shared/runtime')
    try:
        assert identity['backend'] == 'racket' and identity['protected'] is True
        for mode in ('canonical', 'reversed'):
            settings = {'handedness': mode}
            episode = a.generate(0, settings, 2, 4)
            for pair in episode['train'] + episode['test']:
                assert apply(a.program(settings), pair['input']) == pair['output']
            for rival in a.core.RIVALS:
                for pair in episode['train']:
                    assert apply(a.core.rival_program(settings, rival), pair['input']) == a.core.trace(pair['input'], settings, rival=rival)[0]
    finally:
        bridge.close()


def test_verifier_cli_writes_replayable_private_and_single_query_public_files(tmp_path):
    import os
    import subprocess
    import sys
    script = PARAMETRIC / 'verify.py'
    assert script.is_file(), 'reusable bounded verifier has not been implemented'
    out = tmp_path / 'checked'
    run = subprocess.run([sys.executable, str(script), '--seeds', '1', '--out', str(out)],
                         text=True, capture_output=True, timeout=45)
    assert run.returncode == 0, run.stdout + run.stderr
    report = json.loads((out / 'report.json').read_text())
    assert report['census']['episodes'] == 6
    assert report['census']['failures'] == []
    assert report['racket']['protected'] is True
    assert report['retained_episodes'] == 2
    witness = json.loads((out / 'sequential-dependency.json').read_text())
    assert witness['cases'][0]['output'] != witness['cases'][0]['counterfactual_output']
    # Exercise the real native witness reader as a serialization contract.
    # This diagnostic run has no qualified binding; native qualification is a
    # separate integration step, not certified by this constructed reader input.
    import hashlib
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    dependency = {key: witness[key] for key in
                  ('step_a', 'intermediate', 'step_b', 'why_b_depends_on_a')}
    dependency['witness_path'] = 'sequential-dependency.json'
    settings_key = json.dumps({'handedness': 'canonical'}, sort_keys=True, separators=(',', ':'))
    reader_context = {'source_binding': None, 'programs': {
        settings_key: hashlib.sha256(load().program({'handedness': 'canonical'}).encode()).hexdigest()}}
    checked = validate_sequential_witness(
        {'sequential_dependency': dependency}, reader_context,
        lambda name: (out / name).read_bytes())
    assert checked['cases'] == 1
    from reviewer_support import public_challenge_bytes, public_challenge_id
    paths = list((out / 'public').glob('*.json'))
    assert len(paths) == 8
    for path in paths:
        challenge = json.loads(path.read_text())
        assert len(challenge['test']) == 1
        assert set(challenge) == {'train', 'test'}
        assert path.name == public_challenge_id(challenge) + '.json'
        assert path.read_bytes() == public_challenge_bytes(challenge)
    second = subprocess.run([sys.executable, str(script), '--seeds', '1', '--out', str(out)],
                            text=True, capture_output=True, timeout=45)
    assert second.returncode != 0
    assert json.loads((out / 'report.json').read_text()) == report
