"""Focused public/private transport checks for the proposed parametric family."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / 'workspace/parametric/export.py'


def load_exporter():
    assert SOURCE.is_file(), 'task-local public/private exporter is missing'
    spec = importlib.util.spec_from_file_location('parametric_export_4512012999bb', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {'settings': {'alignment': 'match'}, 'seed': 23,
            'program_solution': '(rule! (lambda (g) g))',
            'train': [{'input': [[1]], 'output': [[1]]}],
            'test': [{'input': [[v]], 'output': [[v]]} for v in (2, 3, 4, 5)]}


class PublicTransport(unittest.TestCase):
    def test_public_identity_ignores_private_fields(self):
        exporter = load_exporter()
        source = episode()
        changed = copy.deepcopy(source)
        changed.update(settings={'alignment': 'contrast'}, seed=999,
                       program_solution='private changed program')
        changed['test'][0]['output'] = [[9]]
        original, mutated = exporter.plan_records([source]), exporter.plan_records([changed])
        self.assertEqual(original[0][:2], mutated[0][:2])
        public = json.loads(original[0][1])
        self.assertEqual(set(public), {'train', 'test'})
        self.assertTrue(all(set(pair) == {'input'} for pair in public['test']))

    def test_first_turn_equals_single_query_and_omits_future_inputs(self):
        exporter = load_exporter()
        source = episode()
        short = copy.deepcopy(source)
        short['test'] = short['test'][:1]
        self.assertEqual(exporter.one_query_bytes(source, 0), exporter.one_query_bytes(short, 0))
        visible = json.loads(exporter.one_query_bytes(source, 0))
        self.assertEqual(visible['test'], [{'input': [[2]]}])
        self.assertEqual(set(visible), {'train', 'test'})
        with self.assertRaises(ValueError):
            exporter.one_query_bytes(source, -1)
        with self.assertRaises(ValueError):
            exporter.one_query_bytes(source, True)

    def test_duplicate_visible_payload_fails_before_destination_creation(self):
        exporter = load_exporter()
        changed = episode()
        changed['seed'] = 900
        changed['test'][0]['output'] = [[8]]
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'new'
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                exporter.export_episodes([episode(), changed], output)
            self.assertFalse(output.exists())

    def test_strict_grid_boundaries_and_sorted_opaque_ids(self):
        exporter = load_exporter()
        large = episode()
        large['test'][0] = {'input': [[1] * 30 for _ in range(30)], 'output': [[1]]}
        records = exporter.plan_records([large, episode()])
        self.assertEqual([row[0] for row in records], sorted(row[0] for row in records))
        self.assertTrue(all(len(row[0]) == 64 and set(row[0]) <= set('0123456789abcdef') for row in records))
        for invalid in ([[True]], [[0] * 31], [[0], []], [[10]], []):
            source = episode()
            source['test'][0]['input'] = invalid
            with self.assertRaises(ValueError):
                exporter.plan_records([source])


class ProtectedWriter(unittest.TestCase):
    def test_rehashed_boolean_and_float_public_cells_are_rejected(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'export'
            exporter.export_episodes([episode()], output)
            original = (output / 'public.jsonl').read_bytes()
            for field in ('input', 'output'):
                for invalid in (True, 1.0):
                    with self.subTest(field=field, invalid=repr(invalid)):
                        public = json.loads(original)
                        public['train'][0][field] = [[invalid]]
                        (output / 'public.jsonl').write_bytes(exporter.json_bytes(public))
                        manifest = json.loads((output / 'manifest.json').read_bytes())
                        import hashlib
                        for row in manifest['files']:
                            row['sha256'] = hashlib.sha256((output / row['path']).read_bytes()).hexdigest()
                        (output / 'manifest.json').write_bytes(exporter.json_bytes(manifest))
                        with self.assertRaises(ValueError):
                            exporter.verify_export(output)

    def test_racket_labels_serialization_and_negative_verifier_cases(self):
        exporter = load_exporter()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'export'
            report = exporter.export_episodes([episode()], output)
            self.assertEqual(report['racket']['backend'], 'racket')
            self.assertIs(report['racket']['protected'], True)
            self.assertEqual(report['label_count'], 5)
            exporter.verify_export(output)
            with self.assertRaises(FileExistsError):
                exporter.export_episodes([episode()], output)
            public_file = next((output / 'public').glob('*.json'))
            public_file.write_bytes(public_file.read_bytes() + b' ')
            with self.assertRaises(ValueError):
                exporter.verify_export(output)
            public_file.write_bytes(public_file.read_bytes()[:-1])
            manifest = json.loads((output / 'manifest.json').read_bytes())
            hidden = json.loads((output / 'private.jsonl').read_text())
            hidden['train'][0]['output'] = [[8]]
            (output / 'private.jsonl').write_bytes(exporter.json_bytes(hidden))
            # Rehashing a modified private label must still fail public projection.
            import hashlib
            for row in manifest['files']:
                row['sha256'] = hashlib.sha256((output / row['path']).read_bytes()).hexdigest()
            (output / 'manifest.json').write_bytes(exporter.json_bytes(manifest))
            with self.assertRaisesRegex(ValueError, 'projection'):
                exporter.verify_export(output)

    def test_wrong_racket_label_fails_before_publication(self):
        exporter = load_exporter()
        bad = episode()
        bad['test'][2]['output'] = [[9]]
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'export'
            with self.assertRaisesRegex(ValueError, 'Racket label'):
                exporter.export_episodes([bad], output)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
