"""Seed persistence regressions using only tiny, inert synthetic packets.

Run with: python -B -m unittest discover -s tests -p test_review_main_seed_journal.py
DRAW_SOURCE may select an alternate review_full_draw.py for red/green verification.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

A, B = '111111111111', '222222222222'
SEED_A, SEED_B = bytes(32), (1).to_bytes(32, 'big')
SEED_PATH = '.review/main-draw-seed.json'
PENDING_PATH = '.review/pending-main-draw.json'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':')).encode()


def load_draw():
    # Keep this test independent of optional production package dependencies.
    package = '_main_seed_journal_tests'
    parent = types.ModuleType(package)
    parent.__path__ = []
    packet = types.ModuleType(package + '.review_full_packet')
    packet.SCHEMA = 'arcpuzzles-full-packet-v2'
    packet.canonical_json = canonical
    sys.modules[package] = parent
    sys.modules[packet.__name__] = packet
    source = Path(os.environ.get('DRAW_SOURCE', str(
        Path(__file__).resolve().parents[1] / 'src/arcpuzzles/review_full_draw.py')))
    spec = importlib.util.spec_from_file_location(package + '.draw', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MainSeedJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'synthetic-packet'
        self.root.mkdir()
        self.draw = load_draw()
        # Matches the stock test_review_draw_recovery.py fixture shape.
        self.content = {
            'repo/catalog/runtime_files.json': b'[]',
            'repo/catalog/authority_files.json': b'{}',
            'repo/shared/data/canonical/puzzles.jsonl': b'{"synthetic_fixture":true}\n',
            'repo/REVIEW/questions/q.json': b'{"id":"q","version":1}',
        }
        rows = {}
        for task in (A, B):
            name = f'repo/generators/{task}/generator.py'
            self.content[name] = b'# Inert fixture; never executed.\n'
            rows[task] = {'approved': False, 'generator': name[5:],
                          'generator_sha256': hashlib.sha256(self.content[name]).hexdigest(),
                          'rule_task_id': task, 'rule_hash': '0123456789ab'}
        for name, raw in self.content.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        self.manifest = {
            'schema': 'arcpuzzles-full-packet-v2', 'main_ids': [A, B],
            'all_ids': [A, B], 'generators': rows,
            'questions': [{'id': 'q', 'version': 1,
                'sha256': hashlib.sha256(self.content['repo/REVIEW/questions/q.json']).hexdigest()}],
            'files': {name: hashlib.sha256(raw).hexdigest()
                      for name, raw in self.content.items()},
            'reviewer_solve': {'required': True, 'blind': {'required': True}},
        }
        self.manifest_path = self.root / 'PACKET-MANIFEST.json'
        self.manifest_path.write_bytes(canonical(self.manifest))

    def fail_source(self, name='repo/catalog/runtime_files.json'):
        (self.root / name).unlink()
        with patch.object(self.draw.os, 'urandom', return_value=SEED_A):
            with self.assertRaisesRegex(ValueError, 'Missing packet source'):
                self.draw.draw_main(self.root)
        return name

    def read_seed(self):
        return json.loads((self.root / SEED_PATH).read_text())

    def assert_complete(self, contract):
        self.assertEqual(contract['seed'], SEED_A.hex())
        self.assertEqual(contract['task_id'], A)
        self.assertEqual(contract, json.loads((self.root / 'ASSIGNMENT.json').read_text()))
        self.assertTrue((self.root / 'DUTIES.md').is_file())
        self.assertTrue((self.root / 'RESULTS.json').is_file())
        self.assertEqual(json.loads((self.root / 'BLIND_ASSIGNMENT.json').read_text())['task_id'], B)
        for name, digest in contract['baseline_sha256'].items():
            target = self.root / '.review/baseline' / name
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), digest)
            self.assertFalse(target.stat().st_mode & 0o222)
        self.assertFalse((self.root / PENDING_PATH).exists())
        self.assertFalse((self.root / SEED_PATH).exists())

    def test_missing_mapping_retains_first_seed_before_source_validation(self):
        self.fail_source()
        self.assertTrue((self.root / SEED_PATH).is_file(), 'first seed lost before pending journal')
        self.assertEqual(self.read_seed()['seed'], SEED_A.hex())
        self.assertEqual(self.read_seed()['packet_id'], hashlib.sha256(self.manifest_path.read_bytes()).hexdigest())
        self.assertFalse((self.root / PENDING_PATH).exists())
        self.assertFalse((self.root / '.review/baseline').exists())

    def test_retry_after_missing_mapping_does_not_reroll(self):
        name = self.fail_source()
        (self.root / name).write_bytes(self.content[name])
        with patch.object(self.draw.os, 'urandom', side_effect=AssertionError('unexpected reroll')):
            self.assert_complete(self.draw.draw_main(self.root))

    def test_corrupt_selected_source_retains_seed_and_still_blocks_copy(self):
        name = f'repo/generators/{A}/generator.py'
        (self.root / name).write_bytes(b'corrupt')
        with patch.object(self.draw.os, 'urandom', return_value=SEED_A):
            with self.assertRaisesRegex(ValueError, 'Packet source changed'):
                self.draw.draw_main(self.root)
        self.assertEqual(self.read_seed()['seed'], SEED_A.hex())
        self.assertFalse((self.root / '.review/baseline').exists())
        (self.root / name).write_bytes(self.content[name])
        with patch.object(self.draw.os, 'urandom', return_value=SEED_B):
            self.assert_complete(self.draw.draw_main(self.root))

    def test_missing_question_retains_first_seed(self):
        name = self.fail_source('repo/REVIEW/questions/q.json')
        self.assertEqual(self.read_seed()['seed'], SEED_A.hex())
        self.assertFalse((self.root / '.review/baseline').exists())
        (self.root / name).write_bytes(self.content[name])
        with patch.object(self.draw.os, 'urandom', return_value=SEED_B):
            self.assert_complete(self.draw.draw_main(self.root))

    def test_seed_only_journal_rejects_changed_packet(self):
        self.fail_source()
        before = (self.root / SEED_PATH).read_bytes()
        self.manifest['main_ids'].reverse()
        self.manifest_path.write_bytes(canonical(self.manifest))
        with patch.object(self.draw.os, 'urandom', side_effect=AssertionError('unexpected reroll')):
            with self.assertRaisesRegex(ValueError, 'packet'):
                self.draw.draw_main(self.root)
        self.assertEqual((self.root / SEED_PATH).read_bytes(), before)

    def test_seed_only_journal_rejects_conflicting_explicit_seed(self):
        name = self.fail_source()
        before = (self.root / SEED_PATH).read_bytes()
        with self.assertRaisesRegex(ValueError, 'seed'):
            self.draw.draw_main(self.root, SEED_B)
        self.assertEqual((self.root / SEED_PATH).read_bytes(), before)
        (self.root / name).write_bytes(self.content[name])
        self.assert_complete(self.draw.draw_main(self.root, SEED_A))

    def test_corrupt_seed_journal_never_uses_new_entropy(self):
        home = self.root / '.review'
        home.mkdir()
        packet_id = hashlib.sha256(self.manifest_path.read_bytes()).hexdigest()
        valid = {'schema': 'arcpuzzles-main-draw-seed-v1',
                 'packet_id': packet_id, 'seed': SEED_A.hex()}
        damaged = ['{truncated', '[]', json.dumps(dict(valid, schema='unknown')),
                   json.dumps(dict(valid, seed='00')), json.dumps(dict(valid, seed=None)),
                   json.dumps(dict(valid, seed=' ' + SEED_A.hex()))]
        for raw in damaged:
            with self.subTest(raw=raw):
                (self.root / SEED_PATH).write_text(raw)
                with patch.object(self.draw.os, 'urandom', side_effect=AssertionError('unexpected reroll')):
                    with self.assertRaises(ValueError):
                        self.draw.draw_main(self.root)
                self.assertEqual((self.root / SEED_PATH).read_text(), raw)
                self.assertFalse((self.root / 'ASSIGNMENT.json').exists())

    def pending_draw(self):
        with patch.object(self.draw, '_copy_draw_baseline', side_effect=OSError('injected copy stop')):
            with self.assertRaisesRegex(OSError, 'copy stop'):
                self.draw.draw_main(self.root, SEED_A)
        return json.loads((self.root / PENDING_PATH).read_text())

    def test_legacy_pending_without_seed_journal_resumes_original_seed(self):
        self.pending_draw()
        (self.root / SEED_PATH).unlink(missing_ok=True)
        with patch.object(self.draw.os, 'urandom', side_effect=AssertionError('unexpected reroll')):
            self.assert_complete(self.draw.draw_main(self.root))

    def test_pending_and_seed_journal_disagreement_is_rejected(self):
        self.pending_draw()
        path = self.root / SEED_PATH
        state = {'schema': 'arcpuzzles-main-draw-seed-v1',
                 'packet_id': hashlib.sha256(self.manifest_path.read_bytes()).hexdigest(),
                 'seed': SEED_B.hex()}
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, 'seed'):
            self.draw.draw_main(self.root)
        self.assertTrue((self.root / PENDING_PATH).is_file())

    def test_completed_draw_remains_idempotent_after_edits_and_explicit_new_seed(self):
        expected = self.draw.draw_main(self.root, SEED_A)
        (self.root / f'repo/generators/{A}/generator.py').write_bytes(b'reviewer repair')
        self.manifest_path.unlink()
        with patch.object(self.draw.os, 'urandom', side_effect=AssertionError('unexpected reroll')):
            self.assertEqual(self.draw.draw_main(self.root, SEED_B), expected)

    def test_seed_publish_failure_stops_before_validation_and_copy(self):
        replace = self.draw.os.replace
        def fail_seed(source, destination):
            if Path(destination).name == 'main-draw-seed.json':
                raise OSError('injected seed publication failure')
            return replace(source, destination)
        with patch.object(self.draw.os, 'replace', side_effect=fail_seed):
            with patch.object(self.draw, '_verify', side_effect=AssertionError('validated too early')):
                with self.assertRaisesRegex(OSError, 'seed publication'):
                    self.draw.draw_main(self.root, SEED_A)
        self.assertFalse((self.root / SEED_PATH).exists())
        self.assertFalse((self.root / '.review/baseline').exists())

    def test_seed_is_fsynced_before_first_source_verification(self):
        fsync, replace, verified = self.draw.os.fsync, self.draw.os.replace, self.draw._verify
        events = []
        def record_sync(descriptor):
            fsync(descriptor)
            events.append('file-sync' if stat.S_ISREG(os.fstat(descriptor).st_mode)
                          else 'directory-sync')
        def record_replace(source, destination):
            replace(source, destination)
            if Path(destination).name == 'main-draw-seed.json':
                events.append('seed-published')
        def verify(*args):
            self.assertTrue((self.root / SEED_PATH).is_file())
            published = events.index('seed-published')
            self.assertIn('file-sync', events[:published])
            self.assertIn('directory-sync', events[published + 1:])
            return verified(*args)
        with patch.object(self.draw.os, 'fsync', side_effect=record_sync):
            with patch.object(self.draw.os, 'replace', side_effect=record_replace):
                with patch.object(self.draw, '_verify', side_effect=verify):
                    self.assert_complete(self.draw.draw_main(self.root, SEED_A))

    def test_seed_directory_sync_failure_stops_validation_then_retry_reuses_seed(self):
        fsync = self.draw.os.fsync
        def fail_published_sync(descriptor):
            if ((self.root / SEED_PATH).exists()
                    and stat.S_ISDIR(os.fstat(descriptor).st_mode)):
                raise OSError('injected seed directory sync failure')
            return fsync(descriptor)
        with patch.object(self.draw.os, 'fsync', side_effect=fail_published_sync):
            with patch.object(self.draw, '_verify', side_effect=AssertionError('validated too early')):
                with self.assertRaisesRegex(OSError, 'directory sync'):
                    self.draw.draw_main(self.root, SEED_A)
        self.assertEqual(self.read_seed()['seed'], SEED_A.hex())
        with patch.object(self.draw.os, 'urandom', side_effect=AssertionError('unexpected reroll')):
            self.assert_complete(self.draw.draw_main(self.root))

    def test_seed_journal_symlink_is_rejected(self):
        (self.root / '.review').mkdir()
        target = self.root / 'external-state'
        target.write_bytes(b'unchanged')
        (self.root / SEED_PATH).symlink_to(target)
        with patch.object(self.draw.os, 'urandom', side_effect=AssertionError('unexpected reroll')):
            with self.assertRaisesRegex(ValueError, 'symlink'):
                self.draw.draw_main(self.root)
        self.assertEqual(target.read_bytes(), b'unchanged')

    def test_pending_still_rejects_packet_and_explicit_seed_conflicts(self):
        self.pending_draw()
        with self.assertRaisesRegex(ValueError, 'seed'):
            self.draw.draw_main(self.root, SEED_B)
        before = (self.root / PENDING_PATH).read_bytes()
        self.manifest['main_ids'].reverse()
        self.manifest_path.write_bytes(canonical(self.manifest))
        with self.assertRaisesRegex(ValueError, 'packet'):
            self.draw.draw_main(self.root)
        self.assertEqual((self.root / PENDING_PATH).read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
