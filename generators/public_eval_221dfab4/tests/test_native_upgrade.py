"""Native-only relocation and multicolor teaching regressions."""
from pathlib import Path
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
BASE = HOME / 'workspace/parametric'


def load(name):
    spec = importlib.util.spec_from_file_location('_upgrade221_' + name, BASE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_native_folder_is_resource_closed(tmp_path):
    from reviewer_support import find_root
    native = tmp_path / 'isolated-native'
    shutil.copytree(BASE, native, ignore=shutil.ignore_patterns('__pycache__', 'evidence'))
    code = """import adapter
for mode in ('slice', 'component'):
    e = adapter.generate(17, {'extension': mode}, 2, 4)
    assert len(e['train']) == 2 and len(e['test']) == 4
    assert e['program_solution'].startswith('(rule!')
print('native-only generation passed')
"""
    root = find_root(__file__)
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(root/'src'), str(root/'shared/runtime')]),
               PYTHONDONTWRITEBYTECODE='1')
    proc = subprocess.run([sys.executable, '-c', code], cwd=native, env=env,
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr


def test_native_and_standalone_implementations_are_identical():
    assert (BASE/'family.py').read_bytes() == (HOME/'generator.py').read_bytes()


def test_default_native_lessons_contain_multicolor_contacts():
    a = load('adapter')
    f = load('family')
    for seed in (0, 17, 43):
        e = a.generate(seed, {'extension':'component'}, 2, 4)
        # Every lesson teaches color contacts; even-seed queries preserve the old monochrome bank.
        for p in e['train'] + (e['test'] if seed%2 else []):
            g = p['input']; bg = f.frame(g)['bg']
            colors = {v for row in g for v in row} - {bg, 4}
            assert len(colors) >= 2, 'single-color grammar cannot teach color-sensitive connectivity'
            assert any(g[r][c] not in (bg,4) and g[rr][cc] not in (bg,4)
                       and g[r][c] != g[rr][cc]
                       for r in range(len(g)) for c in range(len(g[0]))
                       for rr,cc in ((r+1,c),(r,c+1)) if rr < len(g) and cc < len(g[0]))


def test_two_demos_reject_color_blind_component_shortcut():
    a, rivals = load('adapter'), load('rivals')
    for seed in range(24):
        e = a.generate(seed, {'extension':'component'}, 2, 4)
        predictions = [rivals.predict(p['input'], 'component') for p in e['train']]
        assert all('color_blind_components' in p for p in predictions)
        assert any(q['color_blind_components'] != p['output']
                   for p,q in zip(e['train'], predictions))


def test_native_query_bank_is_shuffled_before_prefix():
    a = load('adapter'); first_shapes=set()
    for seed in range(32):
        full = a.generate(seed, {'extension':'component'}, 2, 4)
        first_shapes.add((len(full['test'][0]['input']),len(full['test'][0]['input'][0])))
        for n in (1,2,3):
            short=a.generate(seed, {'extension':'component'}, 2, n)
            assert short['test']==full['test'][:n]
            assert short['private_query_bank']==full['test']
    assert len(first_shapes)==4, 'native consumer must not always ask the smallest query first'


@pytest.mark.parametrize('corruption', ['answer','settings','future','float','ragged','duplicate','bad_id'])
def test_public_verifier_rejects_corruption(corruption):
    a, audit=load('adapter'), load('audit')
    assert hasattr(audit,'validate_public_view'), 'reusable strict public verifier missing'
    view=a.public_view(a.generate(17, {'extension':'component'},2,4),0)
    from reviewer_support import public_challenge_id
    identifier=public_challenge_id(view)
    audit.validate_public_view(view,identifier)
    bad=copy.deepcopy(view)
    if corruption=='answer':bad['test'][0]['output']=[[9]]
    elif corruption=='settings':bad['settings']={'extension':'component'}
    elif corruption=='future':bad['test'].append({'input':[[1]]})
    elif corruption=='float':bad['test'][0]['input'][0][0]=1.0
    elif corruption=='ragged':bad['test'][0]['input'][0].pop()
    elif corruption=='duplicate':bad['test'][0]['input']=copy.deepcopy(bad['train'][0]['input'])
    elif corruption=='bad_id':identifier='0'*64
    with pytest.raises(ValueError):audit.validate_public_view(bad,identifier)
