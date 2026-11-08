"""Focused tests for the proposed task-local public/private export boundary."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / 'workspace/parametric/export.py'
SPEC = importlib.util.spec_from_file_location('task_1e7eb285f158_export_tests', PATH)
export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export)


def episode(value=1):
    return {'train': [{'input': [[value]], 'output': [[2]]}],
            'test': [{'input': [[3]], 'output': [[4]]}],
            'seed': 17, 'settings': {'inset_depth': 1},
            'program_solution': '(rule! g)', 'certificate': {'private': True}}


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def write(self, episodes, name='out'):
        out = self.home / name
        manifest = export.write_export(episodes, out)
        return out, manifest

    def public(self, out):
        return {p.name: p.read_bytes() for p in (out / 'public').iterdir()}

    def test_private_changes_and_query_answer_do_not_change_public(self):
        first = episode()
        second = copy.deepcopy(first)
        second.update(seed=999, settings={'anything': 'hidden'}, certificate={'other': 'metadata'},
                      program_solution='(rule! flip-lr)')
        second['test'][0]['output'] = [[9]]
        a, _ = self.write([first], 'a')
        b, _ = self.write([second], 'b')
        self.assertEqual(self.public(a), self.public(b))
        payload = next(iter(self.public(a).values()))
        self.assertEqual(set(json.loads(payload)), {'train', 'test'})
        self.assertEqual(set(json.loads(payload)['test'][0]), {'input'})
        self.assertNotEqual((a / 'private/episodes.json').read_bytes(),
                            (b / 'private/episodes.json').read_bytes())

    def test_visible_demo_change_changes_id(self):
        a, _ = self.write([episode()], 'a')
        changed = episode()
        changed['train'][0]['output'] = [[8]]
        b, _ = self.write([changed], 'b')
        self.assertNotEqual(set(self.public(a)), set(self.public(b)))

    def test_duplicate_projection_fails_before_creating_destination(self):
        second = episode()
        second['seed'] = 1000
        with self.assertRaises(ValueError):
            self.write([episode(), second])
        self.assertFalse((self.home / 'out').exists())

    def test_duplicate_input_across_demo_and_query_rejected(self):
        item = episode()
        item['test'][0]['input'] = copy.deepcopy(item['train'][0]['input'])
        with self.assertRaises(ValueError):
            self.write([item])
        self.assertFalse((self.home / 'out').exists())

    def test_strict_grid_types_including_private_labels(self):
        for split, side in [('train', 'input'), ('train', 'output'),
                            ('test', 'input'), ('test', 'output')]:
            for value in (True, False, 1.0, -1, 10):
                with self.subTest(split=split, side=side, value=value):
                    item = episode()
                    item[split][0][side] = [[value]]
                    with self.assertRaises(ValueError):
                        self.write([item])
                    self.assertFalse((self.home / 'out').exists())

    def test_existing_destination_untouched(self):
        out = self.home / 'out'
        out.mkdir()
        (out / 'sentinel').write_bytes(b'preserve me')
        with self.assertRaises(FileExistsError):
            export.write_export([episode()], out)
        self.assertEqual(list(out.iterdir()), [out / 'sentinel'])
        self.assertEqual((out / 'sentinel').read_bytes(), b'preserve me')

    def test_hash_names_exact_bytes_sorted_records_and_private_provenance(self):
        out, manifest = self.write([episode(6), episode(1)])
        records = manifest['episodes']
        self.assertEqual([r['public_id'] for r in records], sorted(r['public_id'] for r in records))
        for name, payload in self.public(out).items():
            self.assertEqual(name, hashlib.sha256(payload).hexdigest() + '.json')
        for record in manifest['files']:
            self.assertEqual(hashlib.sha256((out / record['path']).read_bytes()).hexdigest(), record['sha256'])
        self.assertEqual(set(manifest), {'schema', 'episodes', 'files'})
        report = json.loads((out / 'private/report.json').read_text())
        self.assertEqual(report['racket_verification'], 'not_run')
        for p in (out / 'private/programs').iterdir():
            self.assertEqual(p.stem, hashlib.sha256(p.read_bytes()).hexdigest())

    def test_loader_ignores_global_prototype_name(self):
        fake = types.ModuleType('prototype')
        fake.MARKER = 'wrong'
        original = sys.modules.get('prototype')
        sys.modules['prototype'] = fake
        self.addCleanup(lambda: sys.modules.pop('prototype', None) if original is None else sys.modules.__setitem__('prototype', original))
        actual = self.home / 'prototype.py'
        actual.write_text('MARKER = \"adjacent\"\n')
        loaded = export._load_path(actual, 'prototype')
        self.assertEqual(loaded.MARKER, 'adjacent')
        self.assertIsNot(loaded, fake)
        with mock.patch.object(export, '_load_path', return_value=loaded) as loader:
            self.assertIs(export._load_prototype(), loaded)
        loader.assert_called_once_with(PATH.with_name('prototype.py').resolve(), 'prototype')


if __name__ == '__main__':
    unittest.main()
