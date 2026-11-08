"""Focused prototype checks; these do not approve the production generator."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TEST_FILE = Path(__file__).resolve()
for ancestor in TEST_FILE.parents:
    helper = next((p for p in (ancestor/'shared/runtime', ancestor) if (p/'reviewer_support.py').is_file()), None)
    if helper is not None:
        sys.path.insert(0, str(helper))
        break
from reviewer_support import find_root, load_selected_generator
ROOT = find_root(TEST_FILE)
SELECTED, SOURCE, SOURCE_HASH = load_selected_generator('5bba6e671cec', root=ROOT)
PROTOTYPE = ROOT/'generators/5bba6e671cec/workspace/parametric/rotation.py'
SPEC = importlib.util.spec_from_file_location('parametric_rotation', PROTOTYPE)
p = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = p
SPEC.loader.exec_module(p)


class ParametricTests(unittest.TestCase):
    def test_exact_default_and_unique_programs(self):
        self.assertEqual(p.instantiate_rule(), p.canonical_rule())
        programs = [p.instantiate_rule(s) for s in p.SETTINGS]
        self.assertEqual(len(set(programs)), 4)
        self.assertIn('(modulo (+ i -2) n)', p.instantiate_rule(p.Setting('ccw', 2)))

    def test_parameter_validation_and_deterministic_episode_selection(self):
        for args in [('north', 1), ('cw', True), ('cw', 0), ('cw', 3)]:
            with self.assertRaises(ValueError):
                p.Setting(*args)
        for invalid in (True, 1.0, '2'):
            with self.assertRaises(ValueError):
                p.choose_setting(invalid)
        selected = [p.choose_setting(i) for i in range(40)]
        self.assertEqual(selected, [p.choose_setting(i) for i in range(40)])
        self.assertEqual(set(selected), set(p.SETTINGS))

    def test_modulo_aliases_and_global_zero_semantics(self):
        two = [[0, 4, 1], [0, 7, 1]]
        self.assertEqual(p.predict(two, p.Setting('cw', 1)), p.predict(two, p.Setting('ccw', 1)))
        self.assertEqual(p.predict(two, p.Setting('cw', 2)), two)
        self.assertEqual(p.predict(two, p.Setting('ccw', 2)), two)
        moved = p.predict(two, p.DEFAULT)
        self.assertEqual(moved, [[1, 4, 0], [1, 7, 0]])
        four = [[1, 4, 2], [7, 4, 7], [5, 4, 3]]
        self.assertEqual(p.predict(four, p.Setting('cw', 2)), p.predict(four, p.Setting('ccw', 2)))
        self.assertNotEqual(p.predict(four, p.Setting('cw', 1)), p.predict(four, p.Setting('ccw', 1)))

    def test_public_projection_does_not_alias_or_leak(self):
        episode = {'seed': 123, 'parameters': {'direction': 'cw'}, 'program': 'secret',
                   'pairs': [{'input': [[1]], 'output': [[2]], 'sample_index': i} for i in range(4)]}
        public = p.public_challenge(episode)
        self.assertEqual(set(public), {'train', 'test'})
        self.assertEqual(set(public['test'][0]), {'input'})
        self.assertEqual(len(public['train']), 3)
        public['train'][0]['input'][0][0] = 9
        self.assertEqual(episode['pairs'][0]['input'], [[1]])

    def test_discrimination_distinguishes_ambiguous_from_survived(self):
        inputs = [[[1, 4, 2], [1, 7, 2]], [[1, 4, 2], [1, 7, 2]],
                  [[1, 4, 2], [7, 4, 7], [5, 4, 3]]]
        pairs = [{'input': g, 'output': p.predict(g, p.DEFAULT)} for g in inputs]
        rivals = {'opposite': lambda g: p.predict(g, p.Setting('ccw', 1)), 'same': lambda g: p.predict(g)}
        score = p.score(pairs, [0, 1], [2], rivals)
        self.assertEqual(score['opposite']['status'], 'ambiguous')
        self.assertEqual(score['same']['status'], 'survived_all')

    def test_wrong_labels_fail_closed(self):
        grid = [[1, 4, 2], [7, 4, 7], [5, 4, 3]]
        episode = {'parameters': {'direction': 'cw', 'steps': 1}, 'pairs': [{'input': grid, 'output': grid}]*4}
        with self.assertRaises(ValueError):
            p.verify_python_labels(episode)

    def test_live_rival_inventory_requires_known_adapters(self):
        declared = p.declared_rival_bindings(p.DEFAULT)
        for namespace in ('CANONICAL_SHORTCUTS', 'SEMANTIC_RIVALS', 'LESSON_COMPETITORS'):
            self.assertEqual({r['name'] for r in declared if r['namespace'] == namespace}, set(getattr(p.generator(), namespace)))
        with patch.dict(p.generator().LESSON_COMPETITORS, {'unknown_future_rival': lambda g: g}):
            with self.assertRaisesRegex(ValueError, 'Unsupported live rival'):
                p.rivals(p.DEFAULT)

    def test_replay_requires_complete_asset_inventory_and_bounded_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            p.write_json(folder/'manifest.json', {'assets': {}})
            with self.assertRaisesRegex(ValueError, 'asset inventory'):
                p.rescore(folder, folder/'out.json')
            (folder/'private').mkdir()
            (folder/'public').mkdir()
            p.write_json(folder/'private/evidence.json', {'rotation_policy': 'invalid'})
            (folder/'public/challenges.jsonl').write_text('')
            assets = {n: p.digest((folder/n).read_bytes()) for n in ('private/evidence.json', 'public/challenges.jsonl')}
            p.write_json(folder/'manifest.json', {'assets': assets})
            with self.assertRaisesRegex(ValueError, 'rotation policy'):
                p.rescore(folder, folder/'out.json')

    def test_duplicate_audit_axes_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            for seeds, bands, starts in (([0, 0], ['medium'], [0]), ([0], ['medium', 'medium'], [0]), ([0], ['medium'], [0, 0])):
                with self.assertRaisesRegex(ValueError, 'duplicates'):
                    p.audit(Path(folder)/'not-created', seeds, bands, starts, 'require')
                self.assertFalse((Path(folder)/'not-created').exists())

    def test_saved_evidence_rescore_rejects_tamper(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            receipt = p.audit(folder/'audit', [0], ['medium'], [0], 'diagnostic')
            self.assertEqual(receipt['counts']['settings'], 4)
            self.assertEqual(receipt['counts']['cross_setting_witnesses'], 6)
            result = p.rescore(folder/'audit', folder/'replay.json')
            self.assertEqual(result['episodes_checked'], 4)
            evidence_path = folder/'audit/private/evidence.json'
            evidence = json.loads(evidence_path.read_text())
            self.assertTrue(all(e['selection'] == 'deterministic_seed_once' for e in evidence['episodes']))
            pristine = json.loads(evidence_path.read_text())
            evidence['episodes'][0]['pairs'][3]['output'][0][0] = (evidence['episodes'][0]['pairs'][3]['output'][0][0] + 1) % 10
            p.write_json(evidence_path, evidence)
            manifest_path = folder/'audit/manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['assets']['private/evidence.json'] = p.digest(evidence_path.read_bytes())
            p.write_json(manifest_path, manifest)
            with self.assertRaises(ValueError):
                p.rescore(folder/'audit', folder/'bad-replay.json')
            pristine['counts']['pairs'] += 1
            p.write_json(evidence_path, pristine)
            manifest['assets']['private/evidence.json'] = p.digest(evidence_path.read_bytes())
            p.write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, 'counts mismatch'):
                p.rescore(folder/'audit', folder/'bad-counts-replay.json')

    def test_racket_all_settings_and_rescore_tamper(self):
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge() as bridge:
            episode = p.make_episode(bridge, 11, setting=p.DEFAULT)
            grid = episode['pairs'][0]['input']
            for setting in p.SETTINGS:
                self.assertEqual(p.evaluate(bridge, p.instantiate_rule(setting), grid), p.predict(grid, setting))
            p.verify_episode(bridge, episode)
            episode['pairs'][0]['output'][0][0] = (episode['pairs'][0]['output'][0][0] + 1) % 10
            with self.assertRaises(ValueError):
                p.verify_episode(bridge, episode)


if __name__ == '__main__':
    unittest.main()
