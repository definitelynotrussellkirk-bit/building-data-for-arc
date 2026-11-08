"""Read-only, original-ZIP reproduction of the five repository-suite failures.

Extract only the source closure required by the two unrelated archival tasks,
the three failing test files, package code and catalog metadata. Reuse declared
Python/Racket runtime executables; all ARCpuzzles imports point to the original
ZIP extraction. No repair-task source is extracted or inspected.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import zipfile

WORK = Path('/dev/shm/arcpuzzles-1f645dc2eeca/WORK')
ARCHIVE = Path('/workspace/scratch/1f645dc2eeca/upload/SEND-THIS-ARCpuzzles-review(20261010-230152).zip')
EXPECTED_ARCHIVE = 'f3f3f22554f8d700db98b89ab459d008d4aa5cbf59405a276bc23581bb82361e'
PYTHON = WORK.parent / 'runtime-python/bin/python'
RACKET = WORK / '.review/racket-runtime/racket/bin/racket'
OUT = Path(__file__).resolve().parent
TASKS = {'defba1ab4f90', 'd982cffd80f8'}
NODES = [
    'tests/test_archival_reference.py::test_archival_rule_access_matches_measured_historical_pairs[defba1ab4f90-8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0]',
    'tests/test_archival_reference.py::test_archival_rules_still_enforce_generator_self_checks[d982cffd80f8]',
    'tests/test_packet_racket_setup.py::test_system_runtime_must_pass_probe_on_unsupported_platform',
    'tests/test_review_resource_guard.py::ArchiveTests::test_extract_round_trip_and_existing_destination_refusal',
    'tests/test_review_resource_guard.py::ArchiveTests::test_extraction_write_failure_preserves_failed_receipt',
]


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(name, args, cwd, env):
    argv = [str(PYTHON), '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
            '--junitxml=' + str(OUT / (name + '.xml')), *args]
    receipt = {'argv': argv, 'cwd': str(cwd), 'environment': {
        key: env[key] for key in ['TMPDIR', 'PYTHONDONTWRITEBYTECODE',
        'PYTHONNOUSERSITE', 'PYTHONPATH', 'ARCPUZZLES_HOME', 'RACKET_PATH']},
        'started_at': time.time()}
    write(name + '.command.json', receipt)
    with (OUT / (name + '.stdout.txt')).open('w') as stream:
        result = subprocess.run(argv, cwd=cwd, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=120)
    receipt.update(exit_code=result.returncode,
                   elapsed_seconds=round(time.time() - receipt['started_at'], 3))
    write(name + '.command.json', receipt)
    print(name, result.returncode, receipt['elapsed_seconds'], flush=True)
    return receipt


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    archive_hash = digest(ARCHIVE)
    assert archive_hash == EXPECTED_ARCHIVE
    with tempfile.TemporaryDirectory(prefix='arc-original-failures-', dir='/dev') as temporary:
        root = Path(temporary)
        repo = root / 'WORK/repo'
        private_tmp = root / 'tmp'
        private_tmp.mkdir()
        hashes = []
        with zipfile.ZipFile(ARCHIVE) as packet:
            mapping = json.loads(packet.read('WORK/repo/catalog/runtime_files.json'))
            authorities = json.loads(packet.read('WORK/repo/catalog/authority_files.json'))
            names = set()
            for item in mapping:
                path, target = item['path'], item['target']
                if path.startswith('generators/') and Path(path).parts[1] not in TASKS:
                    continue
                if target.startswith('data/base/solutions/') and authorities.get(target) not in TASKS:
                    continue
                names.add('WORK/repo/' + path)
            names.update('WORK/repo/' + node.split('::')[0] for node in NODES)
            names.update({'WORK/repo/tests/conftest.py', 'WORK/repo/pyproject.toml',
                          'WORK/repo/shared/tools/arc_review_guard.py'})
            for info in packet.infolist():
                if any(info.filename.startswith('WORK/repo/' + prefix)
                       for prefix in ['src/', 'catalog/', *['generators/' + task + '/' for task in TASKS]]):
                    names.add(info.filename)
            for name in sorted(names):
                info = packet.getinfo(name)
                assert not info.is_dir()
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with packet.open(info) as source, destination.open('xb') as sink:
                    shutil.copyfileobj(source, sink)
                original_hash = digest(destination)
                current_hash = digest(WORK.parent / name)
                hashes.append({'path': name, 'bytes': info.file_size,
                               'original_sha256': original_hash, 'current_sha256': current_hash,
                               'identical': original_hash == current_hash})
        write('original-source-hashes.json', {
            'archive_sha256': archive_hash, 'all_sources_identical': all(row['identical'] for row in hashes),
            'file_count': len(hashes), 'uncompressed_bytes': sum(row['bytes'] for row in hashes),
            'files': hashes})
        assert all(row['identical'] for row in hashes)
        env = dict(os.environ, TMPDIR=str(private_tmp), PYTHONDONTWRITEBYTECODE='1',
                   PYTHONNOUSERSITE='1', PYTHONPATH=os.pathsep.join([str(repo/'src'), str(repo/'shared/runtime')]),
                   ARCPUZZLES_HOME=str(repo), RACKET_PATH=str(RACKET))
        env['PATH'] = str(RACKET.parent) + os.pathsep + env.get('PATH', '')
        write('environment.json', {
            'archive_sha256': archive_hash, 'python_executable': str(PYTHON),
            'racket_executable': str(RACKET),
            'python_version': subprocess.check_output([str(PYTHON), '--version'], text=True).strip(),
            'racket_version': subprocess.check_output([str(RACKET), '--version'], text=True).strip(),
            'isolated_repository': str(repo), 'shm_free_bytes_before': shutil.disk_usage('/dev/shm').free})
        baseline = run('original-five-private-dev', NODES, repo, env)
        assert shutil.disk_usage('/dev/shm').free > 4 * 1024 * 1024
        with tempfile.TemporaryDirectory(prefix='arc-guard-rerun-', dir='/dev/shm') as shared_temporary:
            clean_env = dict(env, TMPDIR=shared_temporary)
            clean = run('original-archive-tests-supported-temp', NODES[-2:], repo, clean_env)
        write('run-summary.json', {'original_five_exit_code': baseline['exit_code'],
                                  'supported_temp_archive_exit_code': clean['exit_code'],
                                  'scope': 'Five selected failures only; no full-suite rerun.',
                                  'all_selected_original_sources_identical_to_work': True})


if __name__ == '__main__':
    main()
