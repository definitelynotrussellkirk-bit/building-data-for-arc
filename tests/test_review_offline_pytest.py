"""Pinned pytest payload and offline installer cannot imply NumPy/Pillow availability."""
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from arcpuzzles import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from test_review_full_packet import _questions


def test_packaging_includes_only_verified_pinned_wheels(library, tmp_path, monkeypatch):
    from arcpuzzles import review_python_wheels as wheels
    _questions(library)
    cache = library / 'var/review/python-wheels';cache.mkdir(parents=True)
    path = cache / 'pytest-9.0.2-py3-none-any.whl';path.write_bytes(b'wheel fixture')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(wheels, 'WHEELS', {path.name: {'sha256': digest, 'bytes': path.stat().st_size, 'requirement': 'pytest==9.0.2'}})
    (cache / 'unlisted.whl').write_bytes(b'not shipped')
    result = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'packet.zip')
    with zipfile.ZipFile(result['zip']) as z:
        manifest = json.loads(z.read('PACKET-MANIFEST.json'))
        assert z.read('vendor/python/' + path.name) == b'wheel fixture'
        assert 'vendor/python/unlisted.whl' not in z.namelist()
        assert manifest['files']['vendor/python/' + path.name] == digest
        assert manifest['python_test_dependencies']['bundled'] is True
        assert manifest['python_test_dependencies']['numpy_pillow_bundled'] is False
    path.write_bytes(b'changed')
    with pytest.raises(ValueError, match='wheel|SHA'):
        build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'bad.zip')


def test_missing_cache_is_truthful_for_source_only_fixture(library, tmp_path):
    _questions(library)
    result = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'packet.zip')
    with zipfile.ZipFile(result['zip']) as z:
        manifest = json.loads(z.read('PACKET-MANIFEST.json'))
    assert manifest['python_test_dependencies']['bundled'] is False


def test_installer_refuses_system_python_and_corrupt_cache_before_pip(tmp_path, monkeypatch):
    from arcpuzzles import review_python_wheels as wheels
    def unexpected(*args, **kwargs):
        pytest.fail('Invalid setup must not invoke pip')
    monkeypatch.setattr(wheels.subprocess, 'run', unexpected)
    monkeypatch.setattr(wheels.sys, 'prefix', wheels.sys.base_prefix)
    with pytest.raises(ValueError, match='venv'):
        wheels.install(tmp_path)
    monkeypatch.setattr(wheels.sys, 'prefix', str(tmp_path / 'venv'))
    with pytest.raises((ValueError, FileNotFoundError)):
        wheels.install(tmp_path)


def test_installer_uses_only_verified_local_wheels_and_no_index(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from arcpuzzles import review_python_wheels as wheels
    path = tmp_path / 'pytest-9.0.2-py3-none-any.whl';path.write_bytes(b'fixture')
    monkeypatch.setattr(wheels, 'WHEELS', {path.name: {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size, 'requirement': 'pytest==9.0.2'}})
    monkeypatch.setattr(wheels.sys, 'prefix', str(tmp_path / 'venv'))
    calls = []
    def pip(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(wheels.subprocess, 'run', pip)
    assert wheels.install(tmp_path)['numpy_pillow_bundled'] is False
    assert len(calls) == 1
    assert calls[0][:5] == [wheels.sys.executable, '-m', 'pip', '--isolated', 'install']
    assert '--no-index' in calls[0] and '--no-deps' in calls[0]
    assert '--ignore-installed' in calls[0] and calls[0][-1] == str(path)
