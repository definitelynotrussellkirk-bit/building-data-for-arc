"""Prototype-only regressions; canonical generator repair tests are separate."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SOURCE = Path(__file__).resolve().parents[1] / 'workspace/parametric/prototype.py'


def test_prototype_entrypoint_exists():
    assert SOURCE.is_file(), 'parametric prototype has not been implemented'


@pytest.fixture(scope='module')
def prototype():
    if not SOURCE.is_file():
        pytest.skip('entrypoint existence test reports the missing implementation')
    spec = importlib.util.spec_from_file_location('chevron_parametric_test', SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def bridge(prototype):
    with prototype.RacketBridge() as reference:
        yield reference


def fixture_grid(orientation=0, *, missing=True, shift=0):
    """Hand-built depth-three triangle; missing left depth two is the witness."""
    grid = [[(r+c) % 2 for c in range(12)] for r in range(12)]
    apex = (5+shift, 5)
    points = [(0, 0), (1, -1), (3, -3), (1, 1), (2, 2), (3, 3)]
    if not missing:
        points.append((2, -2))
    for dr, dc in points:
        if orientation == 1:
            dr = -dr
        elif orientation == 2:
            dr, dc = dc, dr
        elif orientation == 3:
            dr, dc = dc, -dr
        grid[apex[0]+dr][apex[1]+dc] = 3
    return grid


def test_default_exact_bytes_and_racket_canonical_labels(prototype, bridge):
    p = prototype
    source = p.canonical_rule()
    assert p.materialize_rule(p.DEFAULT).encode() == source.encode()
    assert p.digest(source) == 'b4c2540796af088ba41f486413b1be85ff6f8a9db373d30e6105bdc4529c7f25'
    pairs = p.canonical_pairs(p.TASK_ID, root=p.ROOT, labeled_only=True)
    assert len(pairs) == 8
    for pair in pairs:
        original = copy.deepcopy(pair['input'])
        output = p.execute_rule(bridge, source, pair['input'])
        assert output == pair['output']
        assert p.predict(pair['input'], p.DEFAULT) == output
        assert pair['input'] == original


@pytest.mark.parametrize('orientation', range(4))
def test_strict_edges_change_only_missing_boundary_and_keep_depth(prototype, bridge, orientation):
    p = prototype
    grid = fixture_grid(orientation)
    generator, _, _ = p.selected_generator()
    assert generator.self_check(grid) == []
    # Rotate these manually known coordinates with the input fixture.
    def pos(dr, dc):
        if orientation == 1:
            dr = -dr
        elif orientation == 2:
            dr, dc = dc, dr
        elif orientation == 3:
            dr, dc = dc, -dr
        return 5+dr, 5+dc
    for color in (2, 4, 6, 8):
        inclusive = p.execute_rule(bridge, p.materialize_rule(p.Setting(color, True)), grid)
        strict = p.execute_rule(bridge, p.materialize_rule(p.Setting(color, False)), grid)
        rr, cc = pos(2, -2)
        assert inclusive[rr][cc] == color
        assert strict[rr][cc] == grid[rr][cc]
        assert [(r,c) for r in range(12) for c in range(12) if inclusive[r][c] != strict[r][c]] == [(rr, cc)]
        for out, edges in ((inclusive, True), (strict, False)):
            assert out == p.predict(grid, p.Setting(color, edges))
            fr, fc = pos(3, 0)
            assert out[fr][fc] == color  # The far-depth interior is retained.
            br, bc = pos(4, 0)
            assert out[br][bc] == grid[br][bc]  # No extension beyond support.
            assert out[0][0] == grid[0][0]
            assert all(out[r][c] == 3 for r in range(12) for c in range(12) if grid[r][c] == 3)


@pytest.mark.parametrize('color,edges', [(0,True),(1,True),(3,True),(9,True),(True,True),(2.0,True),(2,1),(2,'false'),(2,None)])
def test_invalid_parameter_scalars_fail_closed(prototype, color, edges):
    with pytest.raises(ValueError):
        prototype.Setting(color, edges)


def test_changed_canonical_source_is_rejected(prototype):
    source = prototype.canonical_rule()
    with pytest.raises(ValueError, match='canonical'):
        prototype.materialize_rule(prototype.DEFAULT, source=source+' ')
    with pytest.raises(ValueError):
        prototype.materialize_rule({'fill_color': 8, 'fill_edges': True})


@pytest.fixture(scope='module')
def episodes(prototype, bridge):
    return [prototype.build_episode(271828+i, setting=s, bridge=bridge) for i,s in enumerate(prototype.SETTINGS)]


def test_eight_settings_have_complete_identifiable_racket_episodes(prototype, bridge, episodes):
    p = prototype
    generator, source, source_hash = p.selected_generator()
    assert len(episodes) == 8
    for episode in episodes:
        public, private, report = (episode[k] for k in ('public','private','report'))
        assert set(public) == {'train','test'}
        assert len(public['train']) == 3 and len(public['test']) == 4
        assert all(set(pair) == {'input','output'} for pair in public['train'])
        assert all(set(pair) == {'input'} for pair in public['test'])
        grids = [pair['input'] for pair in public['train']+public['test']]
        assert len({p.digest(g) for g in grids}) == 7
        assert len({p.digest(row['output']) for row in private['pairs']}) == 7
        assert report['status'] == 'PASS'
        assert report['generator_sha256'] == source_hash
        assert len(report['finite_rivals']) == 16
        assert all(row['status'] == ('survived_all' if row['chosen_program'] else 'refuted_by_demonstrations') for row in report['finite_rivals'])
        assert all(row['identified'] for row in report['query_checks'])
        assert len(report['query_checks']) == 4
        setting = p.Setting(**private['parameters'])
        for row, accepted in zip(private['pairs'], report['sampling']['accepted_pairs']):
            assert generator.generate(private['seed'], accepted['sample_index'], difficulty='medium') == row['input']
            assert p.digest(row['input']) == accepted['input_sha256']
            assert p.execute_rule(bridge, private['program'], row['input']) == row['output']
            assert row['output'] == p.predict(row['input'], setting)
            assert len(row['parameter_predictions']) == 8
            assert len(row['lesson_competitor_predictions']) == 8


def test_determinism_and_fresh_return_objects(prototype, bridge, episodes):
    p = prototype
    first = episodes[0]
    second = p.build_episode(271828, setting=p.SETTINGS[0], bridge=bridge)
    assert first == second
    second['public']['train'][0]['input'][0][0] = 9
    assert first != second
    assert first['private']['pairs'][0]['input'][0][0] != 9
    assert p.choose_setting(42) == p.choose_setting(42)


@pytest.mark.parametrize('kwargs', [{'train':2},{'train':True},{'train':3.0},{'test':0},{'test':False},{'test':4.0},{'max_attempts':0},{'seed':True}])
def test_invalid_episode_counts_fail_closed(prototype, kwargs):
    arguments = {'seed':0, **kwargs}
    with pytest.raises(ValueError):
        prototype.build_episode(**arguments)


def test_bounded_sampling_failure_is_explicit(prototype, bridge):
    with pytest.raises(prototype.EpisodeBuildError) as caught:
        prototype.build_episode(42, max_attempts=1, bridge=bridge)
    assert caught.value.evidence['status'] == 'FAIL'
    assert caught.value.evidence['sampling']['attempts'] == 1
    assert 'public' not in caught.value.evidence


def test_changed_generator_bytes_cannot_claim_recorded_source_hash(prototype, bridge, tmp_path, monkeypatch):
    generator, _, _ = prototype.selected_generator()
    copied_source = tmp_path/'generator.py'
    copied_source.write_text('changed bytes after the recorded source snapshot')
    monkeypatch.setattr(prototype, 'selected_generator',
                        lambda: (generator, copied_source, prototype.digest('original bytes')))
    with pytest.raises(ValueError, match='generator changed'):
        prototype.build_episode(271828, setting=prototype.SETTINGS[0], bridge=bridge)


def test_designed_hidden_edge_ambiguity_is_detected(prototype, bridge):
    result = prototype.diagnostic_probe(bridge)
    assert result['kind'] == 'diagnostic_probe'
    assert result['status'] == 'ambiguous'
    assert result['demonstration_matches'] == [True, True, True]
    assert result['query_matches'] == [False]
    assert result['borrowed_query_answers'] is False


def test_cli_public_private_split_and_existing_destination_refusal(prototype, tmp_path):
    out = tmp_path/'artifact'
    command = [sys.executable, str(SOURCE), '--seed','314159','--train','3','--test','4','--fill-color','6','--fill-edges','false','--out',str(out)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    public = json.loads((out/'public/episode-01.json').read_text())
    private = json.loads((out/'private/episode-01.json').read_text())
    assert set(public) == {'train','test'}
    assert private['parameters'] == {'fill_color':6,'fill_edges':False}
    assert all(set(pair) == {'input'} for pair in public['test'])
    assert len(list((out/'private/programs').glob('*.rkt'))) == 8
    report = json.loads((out/'private/report.json').read_text())
    for record in report['source_manifest']:
        assert prototype.digest((prototype.ROOT/record['path']).read_bytes()) == record['sha256']
    for record in report['programs']:
        assert prototype.digest((out/record['path']).read_bytes()) == record['sha256']
    assert subprocess.run(command, capture_output=True, text=True).returncode != 0
    invalid = subprocess.run([sys.executable,str(SOURCE),'--fill-color','3','--out',str(tmp_path/'bad')], capture_output=True, text=True)
    assert invalid.returncode != 0
    assert not (tmp_path/'bad').exists()
