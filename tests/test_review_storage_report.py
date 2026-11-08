"""Optional storage observations must work before packet extraction."""
import importlib.util
import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ENTRY = Path(__file__).resolve().parents[1] / 'src/arcpuzzles/review_workspace_files/review.py'


def load_entry():
    spec = importlib.util.spec_from_file_location('storage_entry', ENTRY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_storage_runs_as_one_file_without_packet_or_installation(tmp_path):
    script = tmp_path / 'storage-report.py'
    shutil.copyfile(ENTRY, script)
    run = subprocess.run([sys.executable, str(script), 'storage', '--label', 'Astra Pro fresh'],
                         cwd=tmp_path, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    report = json.loads(run.stdout)
    assert report['schema'] == 'arcpuzzles-storage-observation-v1'
    assert report['label'] == 'Astra Pro fresh'
    assert report['owned_trees'] == []
    assert not (tmp_path / 'WORK').exists()
    root = next(row for row in report['filesystems'] if row['path'] == '/')
    assert root['total_bytes'] > 0
    assert 0 <= root['available_bytes'] <= root['free_bytes'] <= root['total_bytes']


def test_default_only_reads_counters_and_never_invokes_commands(monkeypatch, capsys):
    module = load_entry()
    def unexpected(*args, **kwargs):
        pytest.fail('Storage observation invoked an external command')
    monkeypatch.setattr(module.subprocess, 'run', unexpected)
    assert module.main(['storage']) == 0
    assert json.loads(capsys.readouterr().out)['owned_trees'] == []


def test_explicit_owned_tree_counts_hardlinks_once_and_does_not_follow_symlinks(tmp_path):
    module = load_entry()
    owned = tmp_path / 'owned'
    owned.mkdir()
    payload = owned / 'payload'
    payload.write_bytes(b'x' * 8192)
    (owned / 'hardlink').hardlink_to(payload)
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'private').write_bytes(b'y' * 100000)
    (owned / 'link').symlink_to(outside, target_is_directory=True)
    row = module.scan_owned_tree(owned, max_entries=100, seconds=3)
    assert row['complete'] is True
    assert row['entries_seen'] == 4
    assert row['unique_inodes'] == 3
    assert row['regular_file_bytes'] == 8192
    assert (outside / 'private').read_bytes() == b'y' * 100000


def test_owned_scan_reports_partial_when_entry_budget_exhausted(tmp_path):
    module = load_entry()
    owned = tmp_path / 'owned'
    owned.mkdir()
    for i in range(10):
        (owned / str(i)).touch()
    row = module.scan_owned_tree(owned, max_entries=2, seconds=3)
    assert row['complete'] is False
    assert row['entries_seen'] == 2
    assert 'entry_budget' in row['limits_hit']


@pytest.mark.parametrize('path', ['/', '/workspace', '/tmp', '/opt', '/usr', '/root', '/home'])
def test_owned_scan_refuses_broad_system_or_workspace_roots(path):
    module = load_entry()
    with pytest.raises(ValueError, match='specific owned'):
        module.scan_owned_tree(Path(path), max_entries=10, seconds=1)


def test_owned_scan_refuses_symlink_root(tmp_path):
    module = load_entry()
    target = tmp_path / 'target'
    target.mkdir()
    link = tmp_path / 'link'
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        module.scan_owned_tree(link, max_entries=10, seconds=1)


def test_jsonl_checkpoint_binds_exact_uploaded_archive_without_extraction(tmp_path):
    script = tmp_path / 'review.py'
    shutil.copyfile(ENTRY, script)
    packet = tmp_path / 'packet.zip'
    import zipfile
    with zipfile.ZipFile(packet, 'w') as archive:
        archive.write(script, 'review.py')
    # The bootstrap reads the entry point into memory; WORK/ is never extracted.
    code = ('import sys,zipfile; p=sys.argv.pop(1); '
            'exec(compile(zipfile.ZipFile(p).read("review.py"),"review.py","exec"),'
            '{"__name__":"__main__","__file__":"review.py"})')
    run = subprocess.run([sys.executable, '-c', code, str(packet), 'storage',
                          '--model', 'GPT-5.6 Pro', '--freshness', 'fresh',
                          '--stage', 'before_extract', '--archive', str(packet), '--jsonl'],
                         cwd=tmp_path, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    assert len(run.stdout.splitlines()) == 1
    row = json.loads(run.stdout)
    assert row['model'] == 'GPT-5.6 Pro'
    assert row['stage'] == 'before_extract'
    assert row['archive']['sha256'] == hashlib.sha256(packet.read_bytes()).hexdigest()
    assert not (tmp_path / 'WORK').exists()
