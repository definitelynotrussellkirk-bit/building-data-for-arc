"""Focused proposed-shear tests; production authority and approval stay unchanged."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id
SOURCE = Path(__file__).resolve().parents[1] / 'workspace/parametric/shear.py'
TMP_ROOT = find_root(__file__).parent / 'checks' / 'tmp'

def subject():
    assert SOURCE.is_file(), 'The requested task-local parametric shear prototype is missing'
    name = '_parametric_shear_tested'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, SOURCE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]

def witness():
    grid = [[0] * 9 for _ in range(8)]
    grid[1][4], grid[3][4], grid[5][4] = (2, 3, 4)
    grid[4][0], grid[4][8] = (5, 6)
    return grid

def nonzero(grid):
    return {(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v}

class ParametricShearTests(unittest.TestCase):

    def test_default_program_is_exact_canonical_authority(self):
        m = subject()
        root = find_root(__file__)
        rows = [json.loads(line) for line in (root / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(line).get('task_id') == '4326f5c2ded0']
        program = m.rule_program(m.Settings())
        self.assertTrue(len(rows) == 2)
        self.assertTrue(all((row['program_solution'] == program for row in rows)))
        self.assertTrue(hashlib.sha256(' '.join(program.split()).encode()).hexdigest()[:12] == '884d94dde3d6')
        for pair in canonical_pairs('4326f5c2ded0', root=root):
            self.assertTrue(m.apply_python(pair['input'], m.Settings()) == pair['output'])

    def test_literal_direction_strength_and_clipping(self):
        for direction, stride, expected in [('left', 1, {(1, 0, 2), (3, 2, 3), (5, 4, 4), (4, 7, 6)}), ('left', 2, {(3, 0, 3), (5, 4, 4), (4, 6, 6)}), ('right', 1, {(1, 8, 2), (3, 6, 3), (5, 4, 4), (4, 1, 5)}), ('right', 2, {(3, 8, 3), (5, 4, 4), (4, 2, 5)})]:
            with self.subTest(direction=direction, stride=stride, expected=expected):
                m = subject()
                grid = witness()
                before = copy.deepcopy(grid)
                output = m.apply_python(grid, m.Settings(direction, stride))
                self.assertTrue(nonzero(output) == expected)
                self.assertTrue(grid == before)
                self.assertTrue(len(output) == 8 and all((len(row) == 9 for row in output)))
                self.assertTrue(all((a is not b for a, b in zip(grid, output))))

    def test_invalid_parameters_rejected(self):
        for direction, stride in [('up', 1), ('LEFT', 1), ('left', True), ('left', 1.0), ('left', 0), ('left', 3)]:
            with self.subTest(direction=direction, stride=stride):
                with self.assertRaises(ValueError):
                    subject().Settings(direction, stride)

    def test_invalid_grids_rejected(self):
        for grid in [[], [[]], [[0, 1], [0]], [[True]], [[10]], [[0]], [[1] * 31]]:
            with self.subTest(grid=grid):
                with self.assertRaises(ValueError):
                    subject().apply_python(grid, subject().Settings())

    def test_sampling_is_deterministic_distinct_and_rng_isolated(self):
        m = subject()
        random.seed(923)
        before = random.getstate()
        samples = m.sample_inputs(17, n_train=3, n_test=4)
        self.assertTrue(random.getstate() == before)
        self.assertTrue(samples == m.sample_inputs(17, n_train=3, n_test=4))
        self.assertTrue(len(samples['train']) == 3 and len(samples['test']) == 4)
        encoded = [json.dumps(g) for g in samples['train'] + samples['test']]
        self.assertTrue(len(set(encoded)) == 7)
        self.assertTrue(any((len(g) == len(g[0]) == 30 for g in samples['test'])))
        self.assertTrue(any((max(len(g), len(g[0])) > 20 for g in samples['test'])))
        self.assertTrue(any((max((r for r, row in enumerate(g) if any(row))) - min((r for r, row in enumerate(g) if any(row))) > 20 for g in samples['test'])))
        samples['train'][0][0][0] = 9
        self.assertTrue(samples != m.sample_inputs(17, n_train=3, n_test=4))

    def test_exact_dimension_and_independent_count_overrides(self):
        for height, width in [(8, 9), (30, 30), (8, 30), (30, 9)]:
            with self.subTest(height=height, width=width):
                m = subject()
                samples = m.sample_inputs(99, n_train=2, n_test=6, height=height, width=width)
                self.assertTrue([len(samples[k]) for k in ('train', 'test')] == [2, 6])
                self.assertTrue(all((len(g) == height and all((len(row) == width for row in g)) for g in samples['train'] + samples['test'])))
                self.assertTrue(len({json.dumps(g) for g in samples['train'] + samples['test']}) == 8)

    def test_unsupported_generation_requests_fail_explicitly(self):
        for kwargs in [{'n_train': 0}, {'n_test': 0}, {'n_test': True}, {'n_test': 17}, {'height': 7}, {'width': 8}, {'width': 31}, {'height': 8.0}]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    subject().sample_inputs(1, **kwargs)

    def test_diagnostic_eliminates_declared_rivals_using_only_demonstrations(self):
        m = subject()
        grids = m.sample_inputs(1, n_train=1, n_test=4, height=8, width=9)
        for direction in ('left', 'right'):
            for stride in (1, 2):
                settings = m.Settings(direction, stride)
                episode = {role: [{'input': g, 'output': m.apply_python(g, settings)} for g in grids[role]] for role in ('train', 'test')}
                report = m.lesson_audit(episode, settings)
                self.assertTrue(report['identifiable'])
                self.assertTrue(report['surviving_parameters'] == [{'direction': direction, 'stride': stride}])
                self.assertTrue(report['surviving_shortcuts'] == [])
                corrupted_queries = copy.deepcopy(episode)
                for pair in corrupted_queries['test']:
                    pair['output'] = [[0 for _ in row] for row in pair['input']]
                self.assertTrue(m.lesson_audit(corrupted_queries, settings)['surviving_parameters'] == report['surviving_parameters'])
                self.assertTrue(m.lesson_audit(corrupted_queries, settings)['surviving_shortcuts'] == report['surviving_shortcuts'])

    def test_ambiguous_demonstrations_are_reported(self):
        m = subject()
        grid = [[0] * 9 for _ in range(8)]
        grid[5][4] = 2
        episode = {'train': [{'input': grid, 'output': copy.deepcopy(grid)}], 'test': [{'input': witness(), 'output': m.apply_python(witness(), m.Settings())}]}
        report = m.lesson_audit(episode, m.Settings())
        self.assertTrue(not report['identifiable'])
        self.assertTrue(len(report['surviving_parameters']) == 4)
        self.assertTrue(report['query_ambiguities'])

    def test_public_writer_names_and_bytes_ignore_all_private_metadata(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='parametric-shear-', dir=TMP_ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            m = subject()
            episode = {'train': [{'input': witness(), 'output': m.apply_python(witness(), m.Settings())}], 'test': [{'input': witness(), 'output': [[0] * 9 for _ in range(8)]}], 'metadata': {'seed': 17, 'parameters': {'direction': 'left', 'stride': 1}, 'program': 'secret'}}
            changed = copy.deepcopy(episode)
            changed['metadata'] = {'seed': 999, 'parameters': {'direction': 'right', 'stride': 2}, 'program': 'other'}
            changed['test'][0]['output'][0][0] = 8
            a, b = (tmp_path / 'a', tmp_path / 'b')
            m.write_batch([episode], a)
            m.write_batch([changed], b)
            left, right = (list((a / 'public').glob('*.json')), list((b / 'public').glob('*.json')))
            self.assertTrue([p.name for p in left] == [p.name for p in right] == [public_challenge_id(episode) + '.json'])
            self.assertTrue(left[0].read_bytes() == right[0].read_bytes() == public_challenge_bytes(episode))
            visible = json.loads(left[0].read_bytes())
            self.assertTrue(set(visible) == {'train', 'test'})
            self.assertTrue(set(visible['test'][0]) == {'input'})
            self.assertTrue(hashlib.sha256(left[0].read_bytes()).hexdigest() == left[0].stem)

    def test_duplicate_public_payload_is_rejected_before_writing(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='parametric-shear-', dir=TMP_ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            m = subject()
            e = {'train': [{'input': witness(), 'output': m.apply_python(witness(), m.Settings())}], 'test': [{'input': witness()}]}
            out = tmp_path / 'duplicate'
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                m.write_batch([e, copy.deepcopy(e)], out)
            self.assertTrue(not out.exists())

    def test_public_batch_is_sorted_and_existing_output_is_not_overwritten(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='parametric-shear-', dir=TMP_ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            m = subject()
            episodes = []
            for stride in (1, 2):
                episodes.append({'train': [{'input': witness(), 'output': m.apply_python(witness(), m.Settings('left', stride))}], 'test': [{'input': witness()}]})
            out = tmp_path / 'batch'
            receipt = m.write_batch(episodes, out)
            self.assertTrue(receipt['public_ids'] == sorted((public_challenge_id(e) for e in episodes)))
            with self.assertRaises(FileExistsError):
                m.write_batch(episodes, out)

    def test_real_racket_labels_all_settings_canonical_and_four_query_episodes(self):
        m = subject()
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge(timeout=10, startup_timeout=60) as bridge:
            for direction in ('left', 'right'):
                for stride in (1, 2):
                    settings = m.Settings(direction, stride)
                    episode = m.build_episode(71, settings=settings, n_train=3, n_test=4, bridge=bridge)
                    self.assertTrue(len(episode['train']) == 3 and len(episode['test']) == 4)
                    self.assertTrue(episode['metadata']['parameters'] == {'direction': direction, 'stride': stride})
                    self.assertTrue(episode['metadata']['labels']['backend'] == 'racket')
                    self.assertTrue(episode['metadata']['lesson_audit']['identifiable'])
                    self.assertTrue(all((p['output'] == m.apply_python(p['input'], settings) for p in episode['train'] + episode['test'])))
                    self.assertTrue(len({json.dumps(p['input']) for p in episode['train'] + episode['test']}) == 7)
            canonical = canonical_pairs('4326f5c2ded0', root=find_root(__file__))
            outputs = m.racket_labels([pair['input'] for pair in canonical], m.Settings(), bridge)
            self.assertTrue(outputs == [pair['output'] for pair in canonical])
if __name__ == '__main__':
    unittest.main()
