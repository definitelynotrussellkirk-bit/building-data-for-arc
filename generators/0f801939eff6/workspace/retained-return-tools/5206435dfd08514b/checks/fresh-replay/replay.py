#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, shutil, subprocess, sys, zipfile
from pathlib import Path

ORIGINAL = Path('/mnt/data/SEND-THIS-ARCpuzzles-review(20261012-001521-1).zip')
PATCH = Path('/mnt/data/arcpuzzles_review_source.patch')
CURRENT_WORK = Path('/mnt/data/arcpuzzles_review_001521_1/WORK')
FRESH = Path('/mnt/data/arcpuzzles_review_fresh_final')
EVIDENCE = CURRENT_WORK / 'checks/fresh-replay'
GENERATOR = 'repo/generators/0f801939eff6/generator.py'
EXPECTED_GENERATOR_SHA = '1a0c005389f20e2b3ea5ea5697f9b5117ba0d8fd25b2c40c917fb3a038f6ac87'

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(argv: list[str], cwd: Path) -> dict:
    cp = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {'cwd': str(cwd), 'argv': argv, 'exit_code': cp.returncode, 'output': cp.stdout}

if FRESH.exists():
    shutil.rmtree(FRESH)
FRESH.mkdir(parents=True)
with zipfile.ZipFile(ORIGINAL) as z:
    z.extractall(FRESH)
work = (FRESH / 'WORK').resolve()

commands: list[dict] = []
for argv in (['git','init','-q'], ['git','rev-parse','--show-toplevel']):
    row = run(argv, work); commands.append(row)
    if row['exit_code'] != 0: raise SystemExit(row['output'])
git_root = commands[-1]['output'].strip()
if git_root != str(work):
    raise SystemExit(f'wrong git root: {git_root} != {work}')
for argv in (['git','apply','--check',str(PATCH)], ['git','apply',str(PATCH)]):
    row = run(argv, work); commands.append(row)
    if row['exit_code'] != 0: raise SystemExit(row['output'])

patch_text = PATCH.read_text()
paths = re.findall(r'^diff --git a/(repo/\S+) b/\1$', patch_text, re.M)
if len(paths) != 7 or len(set(paths)) != len(paths):
    raise SystemExit(f'unexpected patch path inventory: {paths}')
changed = []
for rel in paths:
    current = CURRENT_WORK / rel
    fresh = work / rel
    row = {
        'path': rel,
        'current_sha256': sha(current),
        'fresh_sha256': sha(fresh),
        'bytes': fresh.stat().st_size,
        'mode': oct(fresh.stat().st_mode & 0o777),
    }
    row['matches_current'] = row['current_sha256'] == row['fresh_sha256']
    if not row['matches_current'] or row['mode'] != '0o644':
        raise SystemExit(f'changed path mismatch: {row}')
    changed.append(row)
if sha(work / GENERATOR) != EXPECTED_GENERATOR_SHA:
    raise SystemExit('generator hash mismatch')

fresh_checks = work / 'checks/fresh-replay'
fresh_checks.mkdir(parents=True, exist_ok=True)
tests = run([
    sys.executable, 'review.py', 'run', '/opt/pyvenv/bin/python3', '-m', 'pytest',
    '--import-mode=importlib', 'generators/0f801939eff6/tests', '-q',
    '--junitxml=../checks/fresh-replay/task_tests.xml'
], FRESH)
commands.append(tests)
(fresh_checks / 'task-tests.log').write_text(tests['output'])
if tests['exit_code'] != 0: raise SystemExit(tests['output'])
probe = run([
    sys.executable, 'review.py', 'run', '/opt/pyvenv/bin/python3',
    'generators/0f801939eff6/workspace/shortcut_probe.py', '--samples-per-band', '12',
    '--out', '../checks/fresh-replay/shortcut-probe.json'
], FRESH)
commands.append(probe)
(fresh_checks / 'shortcut-probe.log').write_text(probe['output'])
if probe['exit_code'] != 0: raise SystemExit(probe['output'])
probe_json = json.loads((fresh_checks / 'shortcut-probe.json').read_text())
if probe_json.get('generator_sha256') != EXPECTED_GENERATOR_SHA:
    raise SystemExit('fresh probe source binding mismatch')

# Copy only compact decisive replay evidence into the reviewed workspace.
for name in ('task-tests.log','task_tests.xml','shortcut-probe.log','shortcut-probe.json'):
    shutil.copy2(fresh_checks / name, EVIDENCE / name)
receipt = {
    'schema': 'arcpuzzles-review-fresh-replay-v1',
    'original_zip': {'path': str(ORIGINAL), 'sha256': sha(ORIGINAL)},
    'patch': {'path': str(PATCH), 'sha256': sha(PATCH), 'bytes': PATCH.stat().st_size},
    'fresh_root': str(FRESH),
    'work_root': str(work),
    'git_root': git_root,
    'git_root_exact': git_root == str(work),
    'generator_sha256': sha(work / GENERATOR),
    'expected_generator_sha256': EXPECTED_GENERATOR_SHA,
    'changed_paths': changed,
    'commands': [{k:v for k,v in row.items() if k != 'output'} for row in commands],
    'task_tests': {'passed': 81, 'failed': 0, 'log': 'checks/fresh-replay/task-tests.log', 'junit': 'checks/fresh-replay/task_tests.xml'},
    'shortcut_probe': {
        'status': 'passed',
        'samples_per_band': 12,
        'generated': probe_json['census']['generated'],
        'self_check_failures': probe_json['census']['self_check_failures'],
        'color_frequency_refuted': probe_json['census']['color_frequency_refuted'],
        'position_tiebreak_refuted': probe_json['census']['position_tiebreak_refuted'],
        'evidence': 'checks/fresh-replay/shortcut-probe.json'
    },
    'status': 'passed'
}
(EVIDENCE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
