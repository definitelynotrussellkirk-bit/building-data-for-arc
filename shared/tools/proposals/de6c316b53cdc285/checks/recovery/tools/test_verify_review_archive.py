"""Focused synthetic fixtures; no review task material is loaded by these tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
import struct

SCRIPT = Path(__file__).with_name('verify_review_archive.py')


class VerifyTests(unittest.TestCase):
    def run_fixture(self, mutate=None, canonical=True):
        files = {'WORK/a.txt': b'alpha', 'review.py': b'entry', 'START-HERE.md': b'start'}
        sha = lambda b: hashlib.sha256(b).hexdigest()
        manifest = {'schema': 'arcpuzzles-full-packet-v2', 'files': {'a.txt': sha(files['WORK/a.txt'])},
                    'layout': {'workspace': 'WORK', 'entry_files': {k: sha(v) for k, v in files.items() if not k.startswith('WORK/')}}}
        raw = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':') if canonical else None).encode()
        rows = list(files.items()) + [('WORK/PACKET-MANIFEST.json', raw)]
        if mutate:
            mutate(rows)
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / 'fixture.zip'
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with zipfile.ZipFile(archive, 'w') as z:
                    for name, content in rows:
                        z.writestr(name, content)
            result = subprocess.run([sys.executable, str(SCRIPT), str(archive)], capture_output=True, text=True)
            self.assertTrue(result.stdout, result.stderr)
            return result.returncode, json.loads(result.stdout), sum(len(b) for _, b in rows)

    def test_valid_fixture_counts_and_bytes(self):
        code, receipt, size = self.run_fixture()
        self.assertEqual(code, 0, receipt)
        self.assertTrue(receipt['ok'])
        self.assertEqual(receipt['verified_workspace_files'], 1)
        self.assertEqual(receipt['verified_entry_files'], 2)
        self.assertEqual(receipt['actual_uncompressed_bytes'], size)
        self.assertEqual(len(receipt['archive_sha256']), 64)
        self.assertEqual(len(receipt['manifest_sha256']), 64)

    def test_changed_bytes(self):
        code, r, _ = self.run_fixture(lambda rows: rows.__setitem__(0, ('WORK/a.txt', b'changed')))
        self.assertNotEqual(code, 0)
        self.assertEqual(r['hash_mismatches'], ['WORK/a.txt'])

    def test_missing_member(self):
        code, r, _ = self.run_fixture(lambda rows: rows.pop(0))
        self.assertNotEqual(code, 0)
        self.assertEqual(r['missing_paths'], ['WORK/a.txt'])

    def test_duplicate_member(self):
        code, r, _ = self.run_fixture(lambda rows: rows.append(rows[0]))
        self.assertNotEqual(code, 0)
        self.assertEqual(r['duplicate_paths'], ['WORK/a.txt'])

    def test_path_traversal(self):
        code, r, _ = self.run_fixture(lambda rows: rows.append(('WORK/../outside', b'x')))
        self.assertNotEqual(code, 0)
        self.assertIn('WORK/../outside', r['unsafe_paths'])

    def test_extra_member(self):
        code, r, _ = self.run_fixture(lambda rows: rows.append(('WORK/unlisted', b'x')))
        self.assertNotEqual(code, 0)
        self.assertEqual(r['extra_paths'], ['WORK/unlisted'])

    def test_noncanonical_manifest(self):
        code, r, _ = self.run_fixture(canonical=False)
        self.assertNotEqual(code, 0)
        self.assertIn('manifest is not canonical JSON', r['errors'])

    def test_bad_archive_emits_failure_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'bad.zip'
            path.write_bytes(b'not a zip')
            p = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 1)
            self.assertFalse(json.loads(p.stdout)['ok'])

    def test_symlink_member_is_rejected(self):
        info = zipfile.ZipInfo('WORK/link')
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        code, r, _ = self.run_fixture(lambda rows: rows.append((info, b'a.txt')))
        self.assertNotEqual(code, 0)
        self.assertIn('WORK/link', r['malformed_members'])

    def test_duplicate_manifest_json_key_is_rejected(self):
        def mutate(rows):
            name, raw = rows[-1]
            rows[-1] = (name, b'{"layout":null,' + raw[1:])
        code, r, _ = self.run_fixture(mutate)
        self.assertNotEqual(code, 0)
        self.assertTrue(any('duplicate JSON object key' in e for e in r['errors']))

    def test_out_is_exclusive_and_never_overwrites_archive(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / 'bad.zip'
            archive.write_bytes(b'bad archive')
            output = Path(td) / 'receipt.json'
            command = [sys.executable, str(SCRIPT), str(archive), '--out', str(output)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 1)
            self.assertEqual(first.stdout, '')
            self.assertFalse(json.loads(output.read_text())['ok'])
            before = output.read_bytes()
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(output.read_bytes(), before)
            protected = subprocess.run(command[:-1] + [str(archive)], capture_output=True, text=True)
            self.assertEqual(protected.returncode, 2)
            self.assertEqual(archive.read_bytes(), b'bad archive')

    def test_corrupt_deflate_emits_failure_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'bad-deflate.zip'
            with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr('WORK/a', b'opaque content' * 20)
            data = bytearray(path.read_bytes())
            name_len, extra_len = struct.unpack_from('<HH', data, 26)
            data[30 + name_len + extra_len] = 255  # Invalid deflate block type.
            path.write_bytes(data)
            p = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 1)
            self.assertTrue(p.stdout, p.stderr)
            self.assertFalse(json.loads(p.stdout)['ok'])


if __name__ == '__main__':
    unittest.main()
