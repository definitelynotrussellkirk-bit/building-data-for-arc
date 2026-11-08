"""Run the unmodified official return builder on a verified in-memory packet.

Proposed launcher only. It does not grant approval or claim runtime replay.
Requires Linux with memfd sealing and /proc, Python 3.12+, and pyfakefs 6.2.0.
Use a fresh interpreter and an otherwise quiescent WORK directory.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from contextlib import contextmanager
from types import SimpleNamespace
import hashlib
import fcntl
import importlib
import io
import json
import linecache
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import zipfile
import zipimport


@dataclass(frozen=True)
class Record:
    raw: bytes
    mode: int = stat.S_IFREG | 0o644


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def _safe_name(name):
    if (type(name) is not str or not name or '\\' in name or ':' in name or '\0' in name
            or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts
            or PurePosixPath(name).as_posix() != name):
        raise ValueError(f'Unsafe packet-relative file path: {name!r}')
    return name


def _no_symlinks(path):
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError(f'Symlink path or ancestor: {candidate}')


def _digest_argument(value, label):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise ValueError(f'{label} must be a caller-pinned lowercase SHA-256')


@contextmanager
def sealed_source(source, expected_sha256):
    """Pin all imported/staged ZIP bytes in a kernel-sealed, anonymous snapshot."""
    _digest_argument(expected_sha256, 'source_sha256')
    _no_symlinks(source)
    if not hasattr(os, 'memfd_create') or not Path('/proc/self/fd').is_dir():
        raise RuntimeError('This adapter requires Linux memfd sealing and /proc/self/fd')
    descriptor = os.memfd_create('arcpuzzles-verified-source', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    with os.fdopen(descriptor, 'w+b') as snapshot:
        digest = hashlib.sha256()
        total = 0
        with source.open('rb') as original:
            if not stat.S_ISREG(os.fstat(original.fileno()).st_mode):
                raise ValueError('Source ZIP must be a regular file')
            while chunk := original.read(1024 * 1024):
                total += len(chunk)
                if total > 1024**3:
                    raise ValueError('Compressed source exceeds the 1GiB snapshot budget')
                digest.update(chunk)
                snapshot.write(chunk)
        if digest.hexdigest() != expected_sha256:
            raise ValueError('Original archive SHA-256 mismatch')
        snapshot.flush()
        snapshot.seek(0)
        # Linux UAPI values from linux/fcntl.h and asm-generic/fcntl.h.
        # Some embedded Python builds expose fcntl() without these named constants.
        seals = (getattr(fcntl, 'F_SEAL_WRITE', 0x0008) | getattr(fcntl, 'F_SEAL_GROW', 0x0004)
                 | getattr(fcntl, 'F_SEAL_SHRINK', 0x0002) | getattr(fcntl, 'F_SEAL_SEAL', 0x0001))
        fcntl.fcntl(snapshot.fileno(), getattr(fcntl, 'F_ADD_SEALS', 1033), seals)
        if fcntl.fcntl(snapshot.fileno(), getattr(fcntl, 'F_GET_SEALS', 1034)) & seals != seals:
            raise RuntimeError('Original ZIP snapshot could not be sealed')
        yield snapshot


@contextmanager
def verified_original(source, expected_sha256):
    """Verify an immutable archive snapshot, its inventory, and every member hash."""
    with sealed_source(source, expected_sha256) as stream:
        with zipfile.ZipFile(stream) as archive:
            infos = archive.infolist()
            if len(infos) > 100000 or sum(info.file_size for info in infos) > 1024**3:
                raise ValueError('Source exceeds this launcher\'s 100000-file / 1GiB memory budget')
            seen = set()
            for info in infos:
                name = _safe_name(info.filename)
                if name in seen:
                    raise ValueError(f'Duplicate original member: {name}')
                seen.add(name)
                kind = stat.S_IFMT(info.external_attr >> 16)
                if info.is_dir() or kind not in (0, stat.S_IFREG) or info.flag_bits & 1:
                    raise ValueError(f'Nonregular or encrypted original member: {name}')
            manifest_raw = archive.read('WORK/PACKET-MANIFEST.json')
            manifest = json.loads(manifest_raw)
            if (manifest.get('schema') != 'arcpuzzles-full-packet-v2'
                    or _canonical(manifest) != manifest_raw):
                raise ValueError('Original manifest schema or canonical bytes differ')
            expected = {'WORK/' + _safe_name(name): digest for name, digest in manifest['files'].items()}
            for name, digest in manifest.get('layout', {}).get('entry_files', {}).items():
                _safe_name(name)
                if name in expected:
                    raise ValueError(f'Conflicting original entry declaration: {name}')
                expected[name] = digest
            expected['WORK/PACKET-MANIFEST.json'] = _sha(manifest_raw)
            if seen != set(expected):
                raise ValueError('Original archive inventory differs from its manifest')
            for name, digest in expected.items():
                _digest_argument(digest, f'original hash for {name}')
                with archive.open(name) as member:
                    if hashlib.file_digest(member, 'sha256').hexdigest() != digest:
                        raise ValueError(f'Original member hash mismatch: {name}')
            yield archive, manifest, manifest_raw


def sealed_import_path(archive):
    return Path('/proc/self/fd') / str(archive.fp.fileno())


def _load_official(source):
    """Import only original ZIP code; do not patch any builder or validator."""
    if any(name == 'arcpuzzles' or name.startswith('arcpuzzles.') for name in sys.modules):
        raise ValueError('Use a fresh interpreter without preloaded arcpuzzles modules')
    prefix = str(source) + '/WORK/repo/src'
    sys.path.insert(0, prefix)
    modules = {name: importlib.import_module('arcpuzzles.' + name) for name in (
        'review_full_return', 'review_full_draw', 'review_solve', 'review_tickets', 'review_curriculum')}
    _verify_official_origins(prefix)
    # pyfakefs inspects tracebacks during open(); preload ZIP source lines while
    # real IO is active so linecache never recursively opens the ZIP in fakefs.
    for name, module in tuple(sys.modules.items()):
        if name == 'arcpuzzles' or name.startswith('arcpuzzles.'):
            linecache.getlines(module.__file__, module.__dict__)
    returned, draw = modules['review_full_return'], modules['review_full_draw']
    return SimpleNamespace(build_full_return=returned.build_full_return,
                           validate_full_return=returned.validate_full_return,
                           REQUIRED_DOCS=returned.REQUIRED_DOCS, draw_main=draw.draw_main,
                           base_paths=draw._base_paths,
                           source_prefix=prefix)


def _verify_official_origins(prefix):
    for name, module in tuple(sys.modules.items()):
        if name == 'arcpuzzles' or name.startswith('arcpuzzles.'):
            if not str(getattr(module, '__file__', '')).startswith(prefix + '/arcpuzzles/'):
                raise ValueError(f'Official module did not come from the original ZIP: {name}')


def snapshot_work(work):
    """Snapshot every actual regular file, preserving modes and detecting races."""
    _no_symlinks(work)
    if not work.is_dir():
        raise ValueError('WORK must be an existing directory')
    result = {}
    for directory, directories, files in os.walk(work, followlinks=False):
        for name in sorted(directories):
            candidate = Path(directory) / name
            if candidate.is_symlink():
                raise ValueError(f'Symlink directory in WORK: {candidate}')
        for name in sorted(files):
            candidate = Path(directory) / name
            before = candidate.lstat()
            if not stat.S_ISREG(before.st_mode):
                raise ValueError(f'Nonregular file in WORK: {candidate}')
            raw = candidate.read_bytes()
            after = candidate.lstat()
            identity = lambda value: (value.st_dev, value.st_ino, value.st_size,
                                      value.st_mtime_ns, value.st_mode)
            if identity(before) != identity(after):
                raise ValueError(f'WORK changed while reading: {candidate}')
            result[_safe_name(candidate.relative_to(work).as_posix())] = Record(raw, before.st_mode)
    return result


def validate_overlay(overlay, manifest, manifest_raw, inventory_raw, inventory_sha256):
    _digest_argument(inventory_sha256, 'inventory_sha256')
    if _sha(inventory_raw) != inventory_sha256:
        raise ValueError('Materialized-originals inventory SHA-256 mismatch')
    inventory = json.loads(inventory_raw)
    if inventory.get('schema') != 'arcpuzzles-materialized-original-paths-v1':
        raise ValueError('Unknown materialized-originals inventory schema')
    paths = inventory.get('paths')
    if not isinstance(paths, list) or not paths or len(set(paths)) != len(paths):
        raise ValueError('Materialized-originals inventory needs distinct original paths')
    for name in paths:
        _safe_name(name)
        if not name.startswith('WORK/'):
            raise ValueError(f'Inventory is not WORK-relative: {name}')
        relative = name.removeprefix('WORK/')
        if relative != 'PACKET-MANIFEST.json' and relative not in manifest['files']:
            raise ValueError(f'Inventory path is not in the original archive: {name}')
        if relative not in overlay:
            raise ValueError(f'Previously materialized original is missing: {name}')
    if overlay.get('PACKET-MANIFEST.json') is None or overlay['PACKET-MANIFEST.json'].raw != manifest_raw:
        raise ValueError('Actual PACKET-MANIFEST.json differs from original bytes')
    for name, record in overlay.items():
        if name in manifest['files'] and not name.startswith('repo/'):
            if _sha(record.raw) != manifest['files'][name]:
                raise ValueError(f'Original packet bootstrap changed: {name}')
    contract = json.loads(overlay['ASSIGNMENT.json'].raw)
    if contract.get('packet_id') != _sha(manifest_raw):
        raise ValueError('Actual assignment belongs to another original packet')
    for name, digest in contract['baseline_sha256'].items():
        _safe_name(name)
        if manifest['files'].get(name) != digest:
            raise ValueError(f'Baseline contract differs from original manifest: {name}')
        frozen = overlay.get('.review/baseline/' + name)
        if frozen is None or _sha(frozen.raw) != digest:
            raise ValueError(f'Authentic frozen baseline missing or changed: {name}')
        if name not in overlay:
            raise ValueError(f'Current selected baseline path is missing: {name}')
    return contract


def _memory_build(archive, overlay, official, *, bundle_evidence=False):
    import pyfakefs
    if pyfakefs.__version__ != '6.2.0':
        raise ValueError('This proposed launcher is verified only with pyfakefs==6.2.0')
    from pyfakefs.fake_filesystem_unittest import Patcher
    with Patcher(use_known_patches=False) as patcher:
        fs = patcher.fs
        for info in archive.infolist():
            mode = (info.external_attr >> 16) or (stat.S_IFREG | 0o644)
            fs.create_file('/memory-packet/' + _safe_name(info.filename), contents=archive.read(info),
                           st_mode=stat.S_IFREG | stat.S_IMODE(mode), apply_umask=False)
        # Compute the entire authentic baseline from original-only bytes.
        original_manifest = json.loads(archive.read('WORK/PACKET-MANIFEST.json'))
        assignment = json.loads(overlay['ASSIGNMENT.json'].raw)
        expected_baseline = {name: original_manifest['files'][name] for name in
            official.base_paths(Path('/memory-packet/WORK'), original_manifest, assignment['task_id'])}
        if assignment.get('baseline_sha256') != expected_baseline:
            raise ValueError('Assignment baseline is not the complete original draw baseline')
        frozen_names = {name.removeprefix('.review/baseline/') for name in overlay
                        if name.startswith('.review/baseline/')}
        if frozen_names != set(expected_baseline):
            raise ValueError('Frozen baseline inventory differs from the complete original baseline')
        for name, digest in expected_baseline.items():
            if _sha(overlay['.review/baseline/' + name].raw) != digest:
                raise ValueError(f'Frozen baseline differs from original source: {name}')
        for name, record in overlay.items():
            path = '/memory-packet/WORK/' + _safe_name(name)
            if fs.exists(path):
                fs.remove_object(path)
            fs.create_file(path, contents=record.raw, st_mode=record.mode, apply_umask=False)
        output = Path('/memory-return/review_response.zip')
        official.build_full_return(Path('/memory-packet/WORK'), output, bundle_evidence=bundle_evidence)
        raw = output.read_bytes()
    return raw


def package(source, source_sha256, work, inventory_path, inventory_sha256, out, *, bundle_evidence=False):
    """Build in memory, independently validate outside fakefs, then write a new ZIP."""
    source, work, inventory_path, out = map(Path, (source, work, inventory_path, out))
    for path in (source, work, inventory_path, out):
        _no_symlinks(path.absolute())
    source, work, inventory_path, out = (path.resolve() for path in (source, work, inventory_path, out))
    if out.exists():
        raise FileExistsError(out)
    if out == work or work in out.parents or not out.parent.is_dir():
        raise ValueError('Output must be outside WORK, in an existing directory')
    inventory_raw = inventory_path.read_bytes()
    overlay = snapshot_work(work)
    with verified_original(source, source_sha256) as (archive, manifest, manifest_raw):
        validate_overlay(overlay, manifest, manifest_raw, inventory_raw, inventory_sha256)
        official = _load_official(sealed_import_path(archive))
        raw = _memory_build(archive, overlay, official, bundle_evidence=bundle_evidence)
        _verify_official_origins(official.source_prefix)
        # This is a real, restored filesystem context. No fakefs is active here.
        with zipfile.ZipFile(io.BytesIO(raw)) as returned:
            checked = official.validate_full_return(returned, manifest)
        if snapshot_work(work) != overlay:
            raise ValueError('WORK changed during packaging; refusing a mixed-time return')
        created = False
        try:
            with out.open('xb') as destination:
                created = True
                destination.write(raw)
                destination.flush()
                os.fsync(destination.fileno())
        except BaseException:
            if created:
                out.unlink(missing_ok=True)
            raise
        # Validate the exact bytes on disk with the unmodified official reader.
        try:
            with zipfile.ZipFile(out) as returned:
                rechecked = official.validate_full_return(returned, manifest)
            if rechecked != checked or _sha(out.read_bytes()) != _sha(raw):
                raise ValueError('Written return differs from validated memory bytes')
        except BaseException:
            out.unlink(missing_ok=True)
            raise
    import pyfakefs
    return {'schema': 'arcpuzzles-memory-package-v1', 'status': 'official_static_packaging_passed',
            'zip': str(out), 'zip_sha256': _sha(raw), 'source_zip_sha256': source_sha256,
            'source_manifest_sha256': _sha(manifest_raw),
            'materialized_originals_sha256': inventory_sha256, 'actual_overlay_files': len(overlay),
            'original_declared_files': len(manifest['files']), 'pyfakefs_version': pyfakefs.__version__,
            'source_snapshot': 'Linux memfd with write/grow/shrink/seal seals; zipimport and staging use the same immutable bytes',
            'complete_original_baseline_required': True,
            'scope': 'Unmodified official builder and static validator; no runtime replay or test execution',
            'independent_static_validation_outside_fakefs': True, 'training_admitted': False,
            'official_result': checked}


def exercise_self_test(official, temporary_parent):
    """Tiny genuine draw: compare normal/fake filesystems and retain rejections."""
    with tempfile.TemporaryDirectory(prefix='memory-package-test-', dir=temporary_parent) as temp:
        base = Path(temp)
        work = base / 'WORK'
        task = 'fixture0001'
        generator = f'repo/generators/{task}/generator.py'
        canonical = 'repo/shared/data/canonical/puzzles.jsonl'
        question = {'schema': 'arcpuzzles-review-question-v1', 'id': 'fixture',
                    'version': 1, 'owner': 'ARCpuzzles', 'text': 'Fixture only'}
        originals = {
            generator: b'VERSION = 1\n',
            f'repo/generators/{task}/notes.md': b'Tiny synthetic test fixture.\n',
            canonical: _canonical({'task_id': task, 'program_solution': '(rule! (lambda (g) g))'}) + b'\n',
            'repo/shared/keep.py': b'UNCHANGED = True\n',
            'repo/src/sealed_probe.py': b'VALUE = \"verified-original\"\n',
            'repo/catalog/runtime_files.json': b'[]',
            'repo/catalog/authority_files.json': b'{}',
            'repo/REVIEW/questions/fixture.json': _canonical(question),
        }
        manifest = {'schema': 'arcpuzzles-full-packet-v2', 'all_ids': [task], 'main_ids': [task],
                    'questions': [question], 'files': {p: _sha(raw) for p, raw in originals.items()},
                    'generators': {task: {'generator': generator.removeprefix('repo/'),
                                         'generator_sha256': _sha(originals[generator]),
                                         'rule_task_id': task}}, 'layout': {'entry_files': {}}}
        originals['PACKET-MANIFEST.json'] = _canonical(manifest)
        source = base / 'fixture.zip'
        with zipfile.ZipFile(source, 'x', compression=zipfile.ZIP_DEFLATED) as z:
            for name, raw in sorted(originals.items()):
                info = zipfile.ZipInfo('WORK/' + name)
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                z.writestr(info, raw)
                target = work / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        official.draw_main(work, bytes(32))
        for name in official.REQUIRED_DOCS:
            (work / name).write_text('Synthetic test document.\n')
        (work / 'RESULTS.json').write_bytes(_canonical({'completion_state': 'complete',
                                                      'stopping_reason': 'Synthetic test only'}))
        (work / generator).write_bytes(b'VERSION = 2\n')
        expected_path = base / 'normal.zip'
        official.build_full_return(work, expected_path)
        expected = expected_path.read_bytes()
        overlay = {p.relative_to(work).as_posix(): Record(p.read_bytes(), p.stat().st_mode)
                   for p in work.rglob('*') if p.is_file()}
        with zipfile.ZipFile(source) as original:
            actual = _memory_build(original, overlay, official)
        assert actual == expected, 'Memory builder must produce exactly the official normal-filesystem ZIP bytes'
        with zipfile.ZipFile(io.BytesIO(actual)) as returned:
            checked = official.validate_full_return(returned, manifest)
        assert checked['patch_paths'] == [generator]
        outcomes = []
        for label, path, raw in (
            ('manifest', 'PACKET-MANIFEST.json', _canonical({**manifest, 'extra': 'tampered'})),
            ('baseline', '.review/baseline/' + generator, b'fabricated baseline\n'),
            ('shared_source', 'repo/shared/keep.py', b'changed shared source\n'),
            ('unauthorized_source', 'repo/shared/new.py', b'undeclared new source\n'),
        ):
            changed = dict(overlay)
            changed[path] = Record(raw)
            try:
                with zipfile.ZipFile(source) as original:
                    _memory_build(original, changed, official)
            except ValueError as error:
                outcomes.append({'mutation': label, 'rejected': True, 'reason': str(error)})
            else:
                raise AssertionError(f'Official verification did not reject {label}')
        # The inherited builder trusts its declared baseline key set; the adapter
        # additionally requires the complete original draw map and frozen set.
        altered_contract = json.loads(overlay['ASSIGNMENT.json'].raw)
        altered_contract['baseline_sha256'].pop(generator)
        shortened = dict(overlay)
        shortened['ASSIGNMENT.json'] = Record(_canonical(altered_contract))
        shortened['.review/baseline/' + generator] = Record(b'fabricated omitted baseline\n')
        invented = dict(overlay)
        invented['.review/baseline/repo/generators/' + task + '/new.py'] = Record(b'fabricated new baseline\n')
        for label, changed in [('shortened_baseline_map', shortened), ('invented_baseline', invented)]:
            try:
                with zipfile.ZipFile(source) as original:
                    _memory_build(original, changed, official)
            except ValueError as error:
                outcomes.append({'mutation': label, 'rejected': True, 'reason': str(error)})
            else:
                raise AssertionError(f'Adapter accepted {label}')
        # Check preflight against a pinned inventory made before any removals.
        inventory_raw = _canonical({'schema': 'arcpuzzles-materialized-original-paths-v1',
                                    'paths': sorted('WORK/' + name for name in originals)})
        inventory_sha = _sha(inventory_raw)
        validate_overlay(overlay, manifest, originals['PACKET-MANIFEST.json'], inventory_raw, inventory_sha)
        source_sha = _sha(source.read_bytes())
        original_source_bytes = source.read_bytes()
        with verified_original(source, source_sha) as (sealed_archive, verified_manifest, _):
            assert verified_manifest == manifest
            # Replacing and mutating the original pathname cannot change imported bytes.
            source.rename(base / 'replaced-original.zip')
            source.write_bytes(b'not a zip')
            source.write_bytes(b'mutated again')
            importer = zipimport.zipimporter(str(sealed_import_path(sealed_archive)) + '/WORK/repo/src')
            namespace = {}
            exec(importer.get_code('sealed_probe'), namespace)
            assert namespace['VALUE'] == 'verified-original'
            assert sealed_archive.read('WORK/' + generator) == originals[generator]
            try:
                os.pwrite(sealed_archive.fp.fileno(), b'X', 0)
            except PermissionError:
                pass
            else:
                raise AssertionError('Verified snapshot was writable after sealing')
        source.write_bytes(original_source_bytes)
        preflight = []
        for label, operation in (
            ('missing_materialized_source', lambda: validate_overlay(
                {k: v for k, v in overlay.items() if k != 'repo/shared/keep.py'},
                manifest, originals['PACKET-MANIFEST.json'], inventory_raw, inventory_sha)),
            ('missing_frozen_baseline', lambda: validate_overlay(
                {k: v for k, v in overlay.items() if k != '.review/baseline/' + generator},
                manifest, originals['PACKET-MANIFEST.json'], inventory_raw, inventory_sha)),
            ('inventory_pin', lambda: validate_overlay(
                overlay, manifest, originals['PACKET-MANIFEST.json'], inventory_raw, '0' * 64)),
        ):
            try:
                operation()
            except ValueError as error:
                preflight.append({'mutation': label, 'rejected': True, 'reason': str(error)})
            else:
                raise AssertionError(f'Preflight did not reject {label}')
        try:
            with verified_original(source, '0' * 64):
                raise AssertionError('Original archive digest mutation was accepted')
        except ValueError as error:
            preflight.append({'mutation': 'original_archive_pin', 'rejected': True, 'reason': str(error)})
        # A changed member with a newly computed ZIP pin still fails its manifest hash.
        altered_source = base / 'altered-source.zip'
        with zipfile.ZipFile(source) as original, zipfile.ZipFile(altered_source, 'x') as altered:
            for info in original.infolist():
                raw = original.read(info)
                if info.filename == 'WORK/repo/shared/keep.py':
                    raw += b'# unauthorized change\n'
                altered.writestr(info, raw)
        try:
            with verified_original(altered_source, _sha(altered_source.read_bytes())):
                raise AssertionError('Changed original source member was accepted')
        except ValueError as error:
            preflight.append({'mutation': 'original_member_hash', 'rejected': True, 'reason': str(error)})
        for unsafe in ('../escape', '/absolute', 'a//b', 'a' + chr(92) + 'b', 'a' + chr(0) + 'b'):
            try:
                _safe_name(unsafe)
            except ValueError:
                pass
            else:
                raise AssertionError(f'Unsafe path accepted: {unsafe!r}')
        link = work / 'bad-link'
        link.symlink_to(work / generator)
        try:
            snapshot_work(work)
        except ValueError:
            pass
        else:
            raise AssertionError('Actual symlink must fail before staging')
        finally:
            link.unlink()
        executable = dict(overlay)
        executable[generator] = Record(overlay[generator].raw, stat.S_IFREG | 0o755)
        try:
            with zipfile.ZipFile(source) as original:
                _memory_build(original, executable, official)
        except ValueError as error:
            preflight.append({'mutation': 'executable_source_mode', 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Staging did not preserve an unsafe executable mode')
        # A genuinely unextracted shared file is restored from the verified ZIP.
        partial = {k: v for k, v in overlay.items() if k != 'repo/shared/keep.py'}
        partial_inventory = _canonical({'schema': 'arcpuzzles-materialized-original-paths-v1',
            'paths': sorted('WORK/' + name for name in originals if name != 'repo/shared/keep.py')})
        validate_overlay(partial, manifest, originals['PACKET-MANIFEST.json'],
                         partial_inventory, _sha(partial_inventory))
        with zipfile.ZipFile(source) as original:
            assert _memory_build(original, partial, official) == expected
        (base / 'other').mkdir()
        alias_output = base / 'other' / '..' / 'WORK' / 'forbidden.zip'
        try:
            package(source, source_sha, work, base / 'not-read.json', inventory_sha, alias_output)
        except ValueError as error:
            preflight.append({'mutation': 'output_parent_alias_into_work', 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Lexical output alias wrote inside WORK')
        assert not (work / 'forbidden.zip').exists()
        try:
            package(source, source_sha, work, base / 'not-read.json', inventory_sha, expected_path)
        except FileExistsError:
            pass
        else:
            raise AssertionError('An existing output was accepted')
        assert _sha(source.read_bytes()) == source_sha
        assert expected_path.read_bytes() == expected
        assert (work / '.review/baseline' / generator).read_bytes() == originals[generator]
        return {'schema': 'arcpuzzles-memory-package-self-test-v1',
                'normal_vs_memory_zip_bytes_equal': True, 'independent_static_validation': True,
                'zip_sha256': _sha(actual), 'mutation_rejections': outcomes,
                'preflight_rejections': preflight, 'unsafe_paths_and_symlink_rejected': True,
                'partial_restore_matches_normal_bytes': True,
                'source_replacement_and_mutation_do_not_change_imported_bytes': True,
                'sealed_snapshot_rejects_writes': True, 'existing_output_is_not_overwritten': True,
                'production_packet_packaged': False, 'runtime_replay_exercised': False}



def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-zip', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True, help='Pinned SHA-256 of the supplied original ZIP')
    parser.add_argument('--work', type=Path, help='Actual WORK directory, including authentic assignment/baseline')
    parser.add_argument('--materialized-inventory', type=Path,
                        help='Frozen list of originally extracted WORK paths; never reconstruct this after deletion')
    parser.add_argument('--inventory-sha256', help='Pinned SHA-256 of the frozen materialized inventory')
    parser.add_argument('--out', type=Path, help='New ZIP path outside WORK in an existing directory')
    parser.add_argument('--bundle-evidence', action='store_true')
    parser.add_argument('--self-test', action='store_true', help='Tiny synthetic tests only; no actual return packaging')
    parser.add_argument('--self-test-root', type=Path, help='Existing writable directory for the tiny disposable fixture')
    args = parser.parse_args(argv)
    sys.dont_write_bytecode = True
    if args.self_test:
        if args.self_test_root is None:
            parser.error('--self-test requires --self-test-root')
        with verified_original(args.source_zip.absolute(), args.source_sha256) as (archive, _, _):
            official = _load_official(sealed_import_path(archive))
            report = exercise_self_test(official, args.self_test_root)
        report['source_zip_sha256'] = args.source_sha256
        report['launcher_sha256'] = _sha(Path(__file__).read_bytes())
    else:
        if any(value is None for value in (args.work, args.materialized_inventory, args.inventory_sha256, args.out)):
            parser.error('Packaging requires --work, --materialized-inventory, --inventory-sha256 and --out')
        report = package(args.source_zip, args.source_sha256, args.work, args.materialized_inventory,
                         args.inventory_sha256, args.out, bundle_evidence=args.bundle_evidence)
        report['launcher_sha256'] = _sha(Path(__file__).read_bytes())
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
