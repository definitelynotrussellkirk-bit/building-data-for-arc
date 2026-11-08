#!/usr/bin/env python3
"""Replay this return's native witness and one relocated, isolated episode.

Run through review.py run. This is reviewer verification, never acceptance.
Only a small source closure is copied; temporary runtime/environment stay out
of the return. The relocated interpreter has no site packages or source paths
from the original checkout.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import venv

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_promotion import _ready
from arcpuzzles.review_sequential_replay import replay_witness
from arc_repl.racket_bridge import racket_runtime_status
from reviewer_support import find_root

ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent
TASK = "e07bbcbe6ba4"

PROBE = r'''
import hashlib, importlib.util, json, sys
from pathlib import Path
from arc_repl.racket_bridge import RacketBridge
root = Path.cwd().resolve()
home = root / 'generators/e07bbcbe6ba4/workspace/parametric'
spec = importlib.util.spec_from_file_location('relocated_adapter', home/'adapter.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
settings = {'distance_metric':'manhattan','origin_mode':'nearest_wall_reflection'}
episode = a.generate(23, settings, 2, 4)
assert len(episode['train']) == 2 and len(episode['test']) == 4
assert episode['identifiability']['passed']
assert any(len(p['input']) == len(p['input'][0]) == 30 for p in episode['test'])
with RacketBridge() as bridge:
    output = a._prototype.execute_rule(a.program(settings), episode['test'][3]['input'], bridge=bridge)
    assert output == episode['test'][3]['output']
    identity = bridge.runtime_identity
assert Path(identity['binary_path']).resolve().is_relative_to(root)
assert Path(identity['bridge_path']).resolve().is_relative_to(root)
assert Path(identity['prelude_path']).resolve().is_relative_to(root)
for name, module in list(sys.modules.items()):
    if name.split('.')[0] in ('arc_repl', 'puzzle_generators', 'reviewer_support'):
        if getattr(module, '__file__', None):
            assert Path(module.__file__).resolve().is_relative_to(root)
assert Path(a._prototype.__file__).resolve().is_relative_to(root)
print(json.dumps({'status':'passed','seed':23,'settings':settings,'demos':2,'queries':4,
    'racket':{'backend':identity['backend'],'protected':identity['protected'],
              'binary_sha256':identity['binary_sha256']},
    'private_episode_sha256':hashlib.sha256(json.dumps(episode,sort_keys=True).encode()).hexdigest(),
    'same_checkout_source_and_runtime':True,'independent_venv_without_site_packages':True}))
'''


def main():
    qualification = json.loads((HERE/'qualification/qualification.json').read_text())
    contract, binding = _ready(Catalog(ROOT), TASK)
    assert binding == qualification['source_binding']
    assert contract == qualification['contract']
    witness = json.loads((HERE/'sequential-dependency.json').read_text())
    assert witness['source_binding'] == binding
    replay = replay_witness(ROOT, witness)
    executable = Path(racket_runtime_status()['resolved_binary']).resolve()
    # The packet's Racket tree is self-contained at <runtime>/bin/racket.
    runtime = executable.parent.parent
    with tempfile.TemporaryDirectory(prefix='e07-relocated-') as folder:
        relocated = Path(folder)
        copies = [
            ('shared/runtime', ROOT/'shared/runtime'),
            ('shared/tools/comment_solutions.py', ROOT/'shared/tools/comment_solutions.py'),
            ('shared/data/canonical/puzzles.jsonl', ROOT/'shared/data/canonical/puzzles.jsonl'),
            ('runtime/racket', runtime),
        ]
        for name in ('adapter.py','prototype.py','promotion.json'):
            rel = f'generators/{TASK}/workspace/parametric/{name}'
            copies.append((rel, ROOT/rel))
        for rel, src in copies:
            dst = relocated/rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__'))
            else:
                shutil.copy2(src, dst)
        venv.EnvBuilder(with_pip=False).create(relocated/'venv')
        env = {'PATH':'/usr/bin:/bin', 'PYTHONPATH':str(relocated/'shared/runtime'),
               'PYTHONNOUSERSITE':'1', 'PYTHONDONTWRITEBYTECODE':'1',
               'RACKET_PATH':str(relocated/'runtime/racket/bin/racket')}
        process = subprocess.run([str(relocated/'venv/bin/python'), '-c', PROBE], cwd=relocated,
                                 env=env, capture_output=True, text=True, timeout=60)
        if process.returncode:
            raise RuntimeError(process.stderr[-5000:] + process.stdout[-1000:])
        relocated_result = json.loads(process.stdout)
    result = {'verification_context':'reviewer', 'status':'passed', 'owner_acceptance':False,
              'qualification_sha256':hashlib.sha256((HERE/'qualification/qualification.json').read_bytes()).hexdigest(),
              'source_binding_unchanged':True,'native_witness_replay':replay,
              'relocated_generation':relocated_result}
    (HERE/'handoff-verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'passed','witness_cases':len(replay['cases']),
                      'relocated_generation':relocated_result['status'],'owner_acceptance':False}))


if __name__ == '__main__':
    main()
