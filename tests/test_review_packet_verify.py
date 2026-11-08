"""Maintainer release checks, independent of generator-quality admission."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

import pytest


def _packet(tmp_path, *, mutation=None):
    from arcpuzzles.review_full_packet import canonical_json
    content = {'repo/generators/t/generator.py': b'# fixture\n', 'vendor/racket.tgz': b'fixture'}
    if mutation == 'unsafe':content['../escaped'] = b'bad'
    manifest = {'schema': 'arcpuzzles-full-packet-v2',
                'files': {k: hashlib.sha256(v).hexdigest() for k, v in content.items()},
                'layout': {'workspace': 'WORK', 'entry_files': {'review.py': hashlib.sha256(b'entry').hexdigest(),
                                                            'START-HERE.md': hashlib.sha256(b'start').hexdigest()}},
                'all_ids': ['t'], 'main_ids': ['t'], 'generators': {'t': {'approved': True}}}
    path = tmp_path / 'packet.zip'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('WORK/PACKET-MANIFEST.json', canonical_json(manifest) if mutation != 'noncanonical' else json.dumps(manifest))
        z.writestr('review.py', b'entry');z.writestr('START-HERE.md', b'start')
        for name, raw in content.items():
            if mutation == 'missing' and name.startswith('vendor/'):continue
            if mutation == 'symlink' and name.startswith('vendor/'):
                info = zipfile.ZipInfo('WORK/' + name);info.create_system = 3;info.external_attr = 0o120777 << 16
                z.writestr(info, raw)
            else:z.writestr('WORK/' + name, raw if mutation != 'hash' else raw + b'changed')
        if mutation == 'extra':z.writestr('extra.py', b'unknown')
        if mutation == 'duplicate':
            with pytest.warns(UserWarning, match='Duplicate'):z.writestr('review.py', b'entry')
    return path, manifest


def test_every_member_is_checked_before_an_inventory_can_be_used(tmp_path):
    from arcpuzzles.review_packet_verify import inspect_packet
    p, m = _packet(tmp_path)
    found = inspect_packet(p)
    assert found['manifest'] == m
    assert found['member_count'] == 5
    assert found['zip_sha256'] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert found['packet_id'] == hashlib.sha256(json.dumps(m, sort_keys=True,
           ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


@pytest.mark.parametrize('mutation', ['unsafe', 'missing', 'extra', 'duplicate', 'symlink', 'hash', 'noncanonical'])
def test_changed_or_unsafe_archives_are_rejected(tmp_path, mutation):
    from arcpuzzles.review_packet_verify import inspect_packet
    p, _ = _packet(tmp_path, mutation=mutation)
    with pytest.raises(ValueError):inspect_packet(p)
    assert not (tmp_path.parent / 'escaped').exists()


def test_expected_zip_hash_rejects_the_wrong_artifact(tmp_path):
    from arcpuzzles.review_packet_verify import inspect_packet
    p, _ = _packet(tmp_path)
    with pytest.raises(ValueError, match='SHA-256'):inspect_packet(p, expected_sha256='f' * 64)


def test_existing_output_and_symlink_ancestors_are_not_overwritten(tmp_path):
    from arcpuzzles.review_packet_verify import verify_packet
    p, _ = _packet(tmp_path);out = tmp_path / 'existing';out.mkdir();note = out / 'note';note.write_text('keep')
    with pytest.raises(FileExistsError):verify_packet(p, out, task_id='t')
    assert note.read_text() == 'keep'
    alias = tmp_path / 'alias';alias.symlink_to(out, target_is_directory=True)
    with pytest.raises(ValueError, match='Symlink'):verify_packet(p, alias / 'new', task_id='t')
    assert not (out / 'new').exists()


def test_command_timeout_stops_its_delayed_child(tmp_path):
    from arcpuzzles.review_packet_verify_process import run_command
    marker = tmp_path / 'late'
    child = f'import time;from pathlib import Path;time.sleep(.7);Path({str(marker)!r}).write_text("bad")'
    parent = f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{child!r}]);time.sleep(5)'
    result = run_command([sys.executable, '-c', parent], cwd=tmp_path, env=dict(os.environ),
                         timeout=.15, log_root=tmp_path, name='timeout')
    assert result['timed_out'] is True and result['exit_code'] != 0
    time.sleep(.8)
    assert not marker.exists()


def test_normal_exit_also_closes_same_group_descendants(tmp_path):
    from arcpuzzles.review_packet_verify_process import run_command
    marker = tmp_path / 'late'
    child = f'import time;from pathlib import Path;time.sleep(.5);Path({str(marker)!r}).write_text("bad")'
    parent = f'import subprocess,sys;subprocess.Popen([sys.executable,"-c",{child!r}]);print("complete")'
    result = run_command([sys.executable, '-c', parent], cwd=tmp_path, env=dict(os.environ),
                         timeout=3, log_root=tmp_path, name='complete')
    assert result['exit_code'] == 0 and not result['timed_out']
    assert Path(result['stdout']['path']).read_text() == 'complete\n'
    time.sleep(.6)
    assert not marker.exists()


def test_output_limit_is_a_failure_even_when_the_leader_exits_zero(tmp_path):
    from arcpuzzles.review_packet_verify_process import run_command
    result = run_command([sys.executable, '-c', 'print("x" * 20000)'], cwd=tmp_path,
        env=dict(os.environ), timeout=3, log_root=tmp_path, name='large', max_output_bytes=1024)
    assert result['failure'] == 'output_limit'
    assert result['stdout']['bytes'] > 1024


def test_episode_check_rejects_wrong_types_duplicate_inputs_and_wrong_identity():
    from arcpuzzles.review_packet_verify_probe import check_episode
    row = {'generator_sha256': 'a' * 64, 'rule_hash': 'b' * 12}
    e = {'task_id': 't', 'seed': 17, 'executed_rule_hash': 'b' * 12,
         'provenance': {'generator_sha256': 'a' * 64},
         'train': [{'input': [[1]], 'output': [[2]]}], 'test': [{'input': [[3]], 'output': [[4]]}]}
    assert check_episode(e, 't', row, 1, 1, seed=17)['distinct_inputs'] == 2
    for kind in ['bool', 'float', 'duplicate', 'source', 'rule', 'count', 'seed']:
        bad = json.loads(json.dumps(e))
        if kind == 'bool':bad['test'][0]['output'] = [[False]]
        if kind == 'float':bad['test'][0]['input'] = [[3.0]]
        if kind == 'duplicate':bad['test'][0]['input'] = [[1]]
        if kind == 'source':bad['provenance']['generator_sha256'] = 'c' * 64
        if kind == 'rule':bad['executed_rule_hash'] = 'd' * 12
        if kind == 'count':bad['test'] = []
        if kind == 'seed':bad['seed'] = 18
        with pytest.raises(ValueError):check_episode(bad, 't', row, 1, 1, seed=17)


def test_linux_confinement_denies_an_owner_file_but_allows_the_cold_tree(tmp_path):
    from arcpuzzles import review_packet_verify_landlock as guard
    if sys.platform != 'linux':pytest.skip('Linux Landlock is required by this maintainer command')
    cold = tmp_path / 'cold';cold.mkdir();(cold / 'allowed').write_text('yes')
    denied = tmp_path / 'owner';denied.write_text('must not read')
    code = f'from pathlib import Path;assert Path({str(cold / "allowed")!r}).read_text()=="yes";print("cold-ready")'
    # A host venv's pyvenv.cfg is deliberately outside the permitted tree.
    # This stdlib-only confinement probe uses the resolved system interpreter.
    python = str(Path(sys.executable).resolve())
    result = subprocess.run([python, '-I', str(Path(guard.__file__)), str(cold), str(denied),
                             python, '-I', '-c', code], cwd=cold, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert 'cold-ready' in result.stdout and 'owner_read_denied' in result.stdout


def test_retention_failure_never_leaves_a_passing_receipt_or_discards_cold_work(tmp_path):
    from arcpuzzles.review_packet_verify import _finish_verification
    cold = tmp_path / 'cold';cold.mkdir();(cold / 'logs').mkdir()
    (cold / 'logs/one.stdout').write_text('proof')
    out = tmp_path / 'out';out.mkdir();(out / 'logs').mkdir()
    # Real filesystem conflict during evidence copy, after runtime checks passed.
    (out / 'logs/probe').write_text('cannot replace a user file')
    info = cold.stat();receipt = {'status': 'checks_passed', 'cold_root_retained': True}
    with pytest.raises(OSError):
        _finish_verification(cold, out, receipt, keep_checkout=False, cold_identity=(info.st_dev, info.st_ino))
    assert json.loads((out / 'verification.json').read_text())['status'] == 'failed'
    assert cold.is_dir() and (cold / 'logs/one.stdout').read_text() == 'proof'
    assert (out / 'logs/probe').read_text() == 'cannot replace a user file'


def test_successful_retention_keeps_live_log_links_after_scratch_cleanup(tmp_path):
    from arcpuzzles.review_packet_verify import _finish_verification
    cold = tmp_path / 'cold';cold.mkdir();(cold / 'logs').mkdir()
    for stream in ['stdout', 'stderr']:(cold / 'logs' / ('one.' + stream)).write_text(stream)
    out = tmp_path / 'out';out.mkdir();(out / 'logs').mkdir()
    receipt = {'status': 'checks_passed', 'cold_root_retained': True,
               'cold_probe': {'commands': [{s: {'path': str(cold / 'logs' / ('one.' + s))}
                                            for s in ['stdout', 'stderr']}]}}
    info = cold.stat()
    _finish_verification(cold, out, receipt, keep_checkout=False, cold_identity=(info.st_dev, info.st_ino))
    assert not cold.exists() and receipt['status'] == 'passed' and receipt['cold_root_retained'] is False
    for stream in ['stdout', 'stderr']:
        asset = receipt['cold_probe']['commands'][0][stream]
        assert Path(asset['path']).read_text() == stream
        assert asset['original_path'].startswith(str(cold))


@pytest.mark.parametrize('requested', [False, True])
def test_documented_pack_command_makes_extra_solve_work_opt_in(library, tmp_path, requested):
    from arcpuzzles.cli import main
    questions = library / 'REVIEW/questions';questions.mkdir(parents=True)
    (questions / 'q.json').write_text(json.dumps({'schema': 'arcpuzzles-review-question-v1',
        'id': 'q', 'version': 1, 'owner': 'ARCpuzzles', 'text': 'Optional question'}))
    packet = tmp_path / 'request.zip'
    args = ['--library', str(library), 'review', 'pack-full', '--out', str(packet)]
    if requested:args.append('--reviewer-solve')
    assert main(args) == 0
    with zipfile.ZipFile(packet) as z:m = json.loads(z.read('WORK/PACKET-MANIFEST.json'))
    assert bool(m.get('reviewer_solve', {}).get('required')) is requested
    assert not m.get('blind_solve', {}).get('required', False)
