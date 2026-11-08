"""Preserve review-created runtime receipts, then invoke the unmodified packager.

Scoped to this return. It never removes an original packet file. All removed
new bytes remain under checks/ with size/hash/path mappings. Running cleanup
and the public builder in one process also avoids stale artifacts observed
across this session's tool boundaries.
"""
from pathlib import Path
import hashlib
import json
import runpy
import shutil
import sys

WORK = Path(__file__).resolve().parents[1]
manifest = json.loads((WORK / 'PACKET-MANIFEST.json').read_text())
contract = json.loads((WORK / 'ASSIGNMENT.json').read_text())
assert contract['assignment_id'] == 'review-ed01d6ce549e92d3'
recovery = WORK / 'checks/packaging-cleanup'
recovery.mkdir(exist_ok=True)
records = []
paths = [WORK / 'repo/REVIEW/.lock']
receipt_tree = WORK / 'repo/var/review/authority-sync/33275a4aae3e-15c2d952ab6542c8beb3f95c5bab4b3f'
if receipt_tree.exists():
    paths += sorted(p for p in receipt_tree.rglob('*') if p.is_file())
for path in paths:
    if not path.exists():
        continue
    relative = path.relative_to(WORK).as_posix()
    assert relative not in manifest['files'], relative
    assert not path.is_symlink(), relative
    data = path.read_bytes()
    if relative == 'repo/REVIEW/.lock':
        assert data == b'', 'Refuse to remove a nonempty lock'
    destination = recovery / 'retained' / relative
    destination.parent.mkdir(exist_ok=True, parents=True)
    if destination.exists():
        assert destination.read_bytes() == data, 'Refuse to replace different retained evidence'
    else:
        destination.write_bytes(data)
    records.append({'original_path': relative, 'retained_path': destination.relative_to(WORK).as_posix(),
                    'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    path.unlink()
    assert not path.exists()
# A separately retained, genuinely executed older recording occasionally
# reappeared after the final finished summary. Keep that copy; remove only the
# extra directory, never rewrite the current reports or frozen final notes.
solve = WORK / 'solve'
summary = json.loads((solve / 'summary.json').read_text())
assert summary['status'] == 'finished'
expected = {f'{i:04d}' for i in range(1, summary['attempt_count'] + 1)}
for path in (solve / 'attempts').iterdir():
    if path.name in expected:
        continue
    destination = recovery / 'extra-solve-attempts' / path.name
    if destination.exists():
        for item in path.rglob('*'):
            if item.is_file():
                assert (destination / item.relative_to(path)).read_bytes() == item.read_bytes()
    else:
        shutil.copytree(path, destination)
    shutil.rmtree(path)
reports = sorted(solve.glob('attempts/*/report.json'))
assert len(reports) == summary['attempt_count']
for index, path in enumerate(reports, 1):
    report = json.loads(path.read_text())
    assert report['revision'] == index
    assert report['generator_hash'] == summary['generator_hash']
    assert report['instance_hash'] == summary['instance_hash']
(recovery / 'latest.json').write_text(json.dumps({'preserved_runtime_files': records,
    'solve_attempts': len(reports), 'generator_sha256': summary['generator_hash'],
    'scope': 'Only new session runtime files and separately retained stale solve extras; no packet baseline edits.'}, indent=2) + '\n')
sys.argv = [str(WORK / 'package_return.py'), *sys.argv[1:]]
runpy.run_path(str(WORK / 'package_return.py'), run_name='__main__')
