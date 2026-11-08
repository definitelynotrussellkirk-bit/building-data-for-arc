import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import warnings
import zipfile

from space_preflight import inspect_zip


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.tmp.name)
        self.archive = self.root / 'input.zip'

    def tearDown(self):
        self.tmp.cleanup()

    def write_zip(self, rows):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                for name, value in rows:
                    z.writestr(name, value)

    def fake_fs(self, free_blocks=1000, free_inodes=1000):
        return SimpleNamespace(f_frsize=4096, f_bsize=4096, f_bavail=free_blocks,
                               f_favail=free_inodes, f_files=2000)

    def test_implicit_directories_and_small_file_allocation(self):
        self.write_zip([('WORK/repo/a', b'x'), ('WORK/repo/b', b'')])
        with patch('space_preflight.os.statvfs', return_value=self.fake_fs()):
            result = inspect_zip(self.archive, self.root)
        self.assertEqual(result['estimated_new_inodes'], 4)
        self.assertEqual(result['rounded_file_allocation_bytes'], 4096)
        self.assertEqual(result['estimated_total_allocation_bytes'], 12288)
        self.assertFalse((self.root / 'WORK').exists())

    def test_empty_files_exhaust_inodes_despite_available_bytes(self):
        self.write_zip([(str(i), b'') for i in range(4)])
        with patch('space_preflight.os.statvfs', return_value=self.fake_fs(free_inodes=2)):
            result = inspect_zip(self.archive, self.root)
        self.assertTrue(result['bytes_fit_estimate'])
        self.assertFalse(result['inodes_fit'])
        self.assertEqual(result['capacity_status'], 'insufficient')

    def test_compressed_archive_is_not_expanded_capacity(self):
        self.write_zip([('large', b'0' * 200000)])
        with patch('space_preflight.os.statvfs', return_value=self.fake_fs(free_blocks=10)):
            result = inspect_zip(self.archive, self.root)
        self.assertLess(result['archive_bytes'], 1000)
        self.assertEqual(result['expanded_file_bytes'], 200000)
        self.assertFalse(result['bytes_fit_estimate'])

    def test_ambiguous_or_unsafe_paths_rejected(self):
        for rows in [[('../escape', b'')], [('x', b''), ('x', b'')],
                     [('x', b''), ('x/y', b'')]]:
            self.write_zip(rows)
            with self.assertRaises(ValueError):
                inspect_zip(self.archive, self.root)

    def test_reserves_require_exact_nonnegative_integers(self):
        self.write_zip([('one-byte', b'x')])
        invalid = [
            {'reserve_bytes': -4096, 'reserve_inodes': -1},
            {'reserve_bytes': True}, {'reserve_inodes': False},
            {'reserve_bytes': 1.5}, {'reserve_inodes': 1.0},
            {'reserve_bytes': '1'}, {'reserve_inodes': None},
        ]
        with patch('space_preflight.os.statvfs', return_value=self.fake_fs(free_blocks=0, free_inodes=0)):
            for kwargs in invalid:
                with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, 'reserve_'):
                    inspect_zip(self.archive, self.root, **kwargs)

    def test_dangling_symlink_ancestors_rejected_valid_directory_link_allowed(self):
        self.write_zip([('one-byte', b'x')])
        broken = self.root / 'dangling'
        broken.symlink_to(self.root / 'missing')
        with patch('space_preflight.os.statvfs', return_value=self.fake_fs()):
            for destination in [broken, broken / 'child']:
                with self.subTest(destination=destination), self.assertRaisesRegex(ValueError, 'dangling symlink'):
                    inspect_zip(self.archive, destination)
            real = self.root / 'real'
            real.mkdir()
            valid = self.root / 'valid-link'
            valid.symlink_to(real, target_is_directory=True)
            self.assertEqual(inspect_zip(self.archive, valid)['capacity_status'], 'estimated_fit')


if __name__ == '__main__':
    unittest.main()
