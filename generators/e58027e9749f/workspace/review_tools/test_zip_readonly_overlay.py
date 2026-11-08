import hashlib
import importlib.util
import subprocess
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
import zipfile

# Load the adjacent helper without depending on pytest's import mode or cwd.
_HELPER = Path(__file__).with_name('zip_readonly_overlay.py').resolve()
_SPEC = importlib.util.spec_from_file_location('_task_zip_readonly_overlay', _HELPER)
_ADAPTER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_ADAPTER)
ArchiveView = _ADAPTER.ArchiveView
IntegrityError = _ADAPTER.IntegrityError
digest_file = _ADAPTER.digest_file


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='overlay-test-', dir=Path(__file__).parent)
        self.base = Path(self.tmp.name)
        self.work = self.base / 'WORK'
        self.work.mkdir()
        self.contents = {
            'WORK/repo/shared/original.txt': b'original never extracted\n',
            'WORK/repo/shared/real.txt': b'real immutable original\n',
            'WORK/repo/generators/chosen/generator.py': b'chosen source\n',
            'WORK/repo/generators/chosen/not-extracted.txt': b'protected selected source\n',
            'WORK/repo/shared/data/canonical/puzzles.jsonl': b'protected canonical\n',
            'WORK/repo/shared/data/base/related.json': b'assigned base original\n',
            'WORK/repo/shared/data/base/unrelated.json': b'unrelated base original\n',
            'WORK/checks/not-extracted.json': b'protected evidence\n',
            'WORK/.review/baseline/not-extracted': b'protected baseline\n',
            'START-HERE.md': b'outer entry\n',
        }
        self.manifest = {'files': {n[5:]: sha(v) for n,v in self.contents.items() if n.startswith('WORK/')},
                         'layout': {'entry_files': {'START-HERE.md': sha(self.contents['START-HERE.md'])}}}
        self.contents['WORK/PACKET-MANIFEST.json'] = json.dumps(self.manifest).encode()
        self.archive = self.base / 'source.zip'
        self.write_archive()
        self.materialized = {'START-HERE.md', 'WORK/PACKET-MANIFEST.json',
                             'WORK/repo/shared/real.txt', 'WORK/repo/generators/chosen/generator.py'}
        for name in self.materialized:
            target = self.base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.contents[name])
        self.inventory = self.base / 'EXTRACTION.json'
        self.inventory.write_text(json.dumps({'files': [
            {'path': n, 'sha256': sha(self.contents[n]), 'bytes': len(self.contents[n])}
            for n in sorted(self.materialized)]}))
        self.source_sha = digest_file(self.archive)
        self.inventory_sha = digest_file(self.inventory)
        self.views = []

    def write_archive(self):
        with zipfile.ZipFile(self.archive, 'w') as z:
            for name, data in self.contents.items():
                z.writestr(name, data)

    def view(self, **overrides):
        kwargs = dict(archive=self.archive, root=self.work, inventory=self.inventory,
                      source_sha256=self.source_sha, inventory_sha256=self.inventory_sha,
                      selected_task='chosen')
        kwargs.update(overrides)
        view = ArchiveView(**kwargs)
        self.views.append(view)
        return view.path()

    def tearDown(self):
        for view in self.views:
            view.close()
        self.tmp.cleanup()

    def test_never_extracted_original_reads_exactly_and_enumerates(self):
        root = self.view()
        target = root / 'repo/shared/original.txt'
        self.assertFalse(Path(str(target)).exists())
        self.assertTrue(target.is_file())
        self.assertEqual(target.read_bytes(), self.contents['WORK/repo/shared/original.txt'])
        self.assertEqual(target.stat().st_size, len(target.read_bytes()))
        found = {p.relative_to(root).as_posix() for p in (root/'repo').rglob('*') if p.is_file()}
        self.assertIn('repo/shared/original.txt', found)

    def test_tampered_materialized_original_remains_authoritative(self):
        root = self.view()
        physical = self.work / 'repo/shared/real.txt'
        physical.write_bytes(b'TAMPERED')
        self.assertEqual((root/'repo/shared/real.txt').read_bytes(), b'TAMPERED')
        self.assertNotEqual(sha((root/'repo/shared/real.txt').read_bytes()),
                            self.manifest['files']['repo/shared/real.txt'])
        # Newly materialized archive-only paths also become authoritative.
        physical = self.work / 'repo/shared/original.txt'
        physical.write_bytes(b'NEW REAL VERSION')
        self.assertEqual((root/'repo/shared/original.txt').read_bytes(), b'NEW REAL VERSION')

    def test_deleted_materialized_original_cannot_fallback(self):
        root = self.view()
        (self.work/'repo/shared/real.txt').unlink()
        for operation in [lambda: (root/'repo/shared/real.txt').exists(),
                          lambda: (root/'repo/shared/real.txt').is_file(),
                          lambda: (root/'repo/shared/real.txt').read_bytes(), self.view]:
            with self.assertRaisesRegex(IntegrityError, 'Materialized original missing'):
                operation()

    def test_archive_and_inventory_pin_mismatches_fail(self):
        with self.assertRaisesRegex(IntegrityError, 'Source ZIP'):
            self.view(source_sha256='0'*64)
        with self.assertRaisesRegex(IntegrityError, 'inventory SHA'):
            self.view(inventory_sha256='0'*64)

    def test_manifest_member_mismatch_fails_even_with_recomputed_outer_pin(self):
        self.contents['WORK/repo/shared/original.txt'] = b'archive corruption'
        self.write_archive()
        with self.assertRaisesRegex(IntegrityError, 'Archive member hash mismatch'):
            self.view(source_sha256=digest_file(self.archive))

    def test_protected_absent_files_never_fallback(self):
        root = self.view()
        for rel in ['repo/generators/chosen/not-extracted.txt',
                    'repo/shared/data/canonical/puzzles.jsonl',
                    'checks/not-extracted.json', '.review/baseline/not-extracted']:
            target = root/rel
            self.assertFalse(target.exists())
            with self.assertRaises(FileNotFoundError):
                target.read_bytes()

    def test_only_assigned_base_paths_require_physical_files(self):
        rel = 'repo/shared/data/base/related.json'
        (self.work/'ASSIGNMENT.json').write_text(json.dumps({'task_id': 'chosen',
            'baseline_sha256': {rel: sha(self.contents['WORK/'+rel])}}))
        root = self.view()
        self.assertFalse((root/rel).exists())
        with self.assertRaises(FileNotFoundError):
            (root/rel).read_bytes()
        unrelated = 'repo/shared/data/base/unrelated.json'
        self.assertEqual((root/unrelated).read_bytes(), self.contents['WORK/'+unrelated])

    def test_writes_are_real_and_new_sources_are_enumerated(self):
        root = self.view()
        target = root/'repo/shared/added.txt'
        target.write_text('real new source')
        self.assertEqual((self.work/'repo/shared/added.txt').read_text(), 'real new source')
        self.assertIn(target, list((root/'repo').rglob('*')))
        target = root/'repo/shared/original.txt'
        target.write_text('real replacement')
        self.assertEqual((self.work/'repo/shared/original.txt').read_text(), 'real replacement')

    @unittest.skipUnless(os.environ.get('ARCPUZZLES_TEST_SRC'), 'set ARCPUZZLES_TEST_SRC for official-builder smoke')
    def test_unmodified_official_builder_reads_view_and_rejects_shared_tamper(self):
        sys.path.insert(0, os.environ['ARCPUZZLES_TEST_SRC'])
        from arcpuzzles.review_full_packet import canonical_json
        from arcpuzzles.review_full_return import build_full_return
        baseline = {}
        for name, data in self.contents.items():
            if name.startswith('WORK/repo/generators/chosen/') or name == 'WORK/repo/shared/data/canonical/puzzles.jsonl':
                rel = name[5:]
                target = self.work/rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                frozen = self.work/'.review/baseline'/rel
                frozen.parent.mkdir(parents=True, exist_ok=True)
                frozen.write_bytes(data)
                baseline[rel] = sha(data)
        contract = {'packet_id': sha(canonical_json(self.manifest)), 'task_id': 'chosen',
                    'baseline_sha256': baseline}
        (self.work/'ASSIGNMENT.json').write_text(json.dumps(contract))
        root = self.view()
        # A normal immutable-source scan reaches missing-report checking.
        with self.assertRaisesRegex(ValueError, 'Missing review document: REVIEW.md'):
            build_full_return(root, self.base/'unused.zip')
        (self.work/'repo/shared/real.txt').write_bytes(b'TAMPERED')
        with self.assertRaisesRegex(ValueError, 'Changed or missing shared packet source: repo/shared/real.txt'):
            build_full_return(root, self.base/'unused.zip')

    def test_symlinks_and_parent_traversal_rejected(self):
        root = self.view()
        (self.work/'repo/shared/link').symlink_to(self.work/'repo/shared/real.txt')
        with self.assertRaisesRegex(IntegrityError, 'Symlink'):
            (root/'repo/shared/link').read_bytes()
        with self.assertRaisesRegex(IntegrityError, 'Parent traversal'):
            (root/'repo/../PACKET-MANIFEST.json').read_bytes()


class ImportIsolationTests(unittest.TestCase):
    def run_probe(self, body):
        prefix = """
import importlib.util
from pathlib import Path
import sys
spec = importlib.util.spec_from_file_location('adapter', sys.argv[1])
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
"""
        result = subprocess.run([sys.executable, '-B', '-c', prefix + body, str(_HELPER)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_preloaded_official_module_is_rejected_before_import(self):
        self.run_probe(r"""
import tempfile
import types
with tempfile.TemporaryDirectory() as directory:
    sys.modules['arcpuzzles.untrusted'] = types.ModuleType('arcpuzzles.untrusted')
    try:
        with adapter.official_import_context(Path(directory)):
            raise AssertionError('preloaded package was accepted')
    except adapter.IntegrityError as error:
        assert 'preloaded' in str(error).lower(), str(error)
""")

    def test_sourceless_bytecode_and_native_modules_are_rejected(self):
        self.run_probe(r"""
import importlib.machinery
import py_compile
import tempfile
with tempfile.TemporaryDirectory() as directory:
    source_root = Path(directory) / 'src'
    source_root.mkdir()
    outside = Path(directory) / 'input.py'
    outside.write_text("MARKER = 'sourceless-cache'\n")
    bytecode = source_root / 'arcpuzzles.pyc'
    py_compile.compile(str(outside), cfile=str(bytecode), doraise=True)
    sys.path.insert(0, str(source_root))
    import arcpuzzles
    assert arcpuzzles.MARKER == 'sourceless-cache'
    del sys.modules['arcpuzzles']
    sys.path.pop(0)
    for target in [bytecode, source_root / ('arcpuzzles' + importlib.machinery.EXTENSION_SUFFIXES[0])]:
        if not target.exists():
            target.write_bytes(b'native candidate must never be imported')
        try:
            with adapter.official_import_context(source_root):
                raise AssertionError('alternative executable module was accepted')
        except adapter.IntegrityError as error:
            assert 'executable' in str(error).lower(), str(error)
        target.unlink()
    (source_root / 'arcpuzzles').symlink_to(Path(directory), target_is_directory=True)
    try:
        with adapter.official_import_context(source_root):
            raise AssertionError('source symlink was accepted')
    except adapter.IntegrityError as error:
        assert 'symlink' in str(error).lower(), str(error)
""")

    def test_eligible_poisoned_bytecode_is_ignored_and_settings_are_restored(self):
        self.run_probe(r"""
import py_compile
import tempfile
with tempfile.TemporaryDirectory() as directory:
    source_root = Path(directory)
    package = source_root / 'arcpuzzles'
    package.mkdir()
    source = package / '__init__.py'
    source.write_text("MARKER = 'poisoned-cache'\n")
    py_compile.compile(str(source), doraise=True,
                       invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
    source.write_text("MARKER = 'verified-source'\n")
    # First establish that an ordinary import really takes the hostile cache.
    sys.path.insert(0, str(source_root))
    import arcpuzzles
    assert arcpuzzles.MARKER == 'poisoned-cache', arcpuzzles.MARKER
    del sys.modules['arcpuzzles']
    sys.path.pop(0)
    previous = (sys.pycache_prefix, sys.dont_write_bytecode, list(sys.path))
    with adapter.official_import_context(source_root):
        assert sys.dont_write_bytecode
        assert Path(sys.pycache_prefix).is_dir()
        assert not list(Path(sys.pycache_prefix).rglob('*.pyc'))
        import arcpuzzles
        assert arcpuzzles.MARKER == 'verified-source', arcpuzzles.MARKER
    assert (sys.pycache_prefix, sys.dont_write_bytecode, sys.path) == previous
""")


if __name__ == '__main__':
    unittest.main(verbosity=2)
