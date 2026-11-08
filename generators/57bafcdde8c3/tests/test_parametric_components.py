"""Prototype-only regressions; run with unittest, no pytest dependency."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]
HERE = REPO / 'generators/57bafcdde8c3/workspace/parametric'
sys.path[:0] = [str(REPO / 'shared/runtime'), str(HERE)]

class PrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = HERE / 'components.py'
        if not path.is_file():
            return
        spec = importlib.util.spec_from_file_location('component_prototype', path)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def module(self):
        self.assertTrue((HERE / 'components.py').is_file(), 'component prototype must exist')
        return self.mod

    def test_threshold_color_connectivity_and_input_immutability(self):
        m = self.module()
        # Two diagonal 3s, touching unequal singletons 4/5, and a 0 triple.
        grid = [[1,1,1,1,1,1],[1,3,1,4,5,1],[1,1,3,1,1,1],
                [1,1,1,1,1,1],[0,0,0,1,1,1],[1,1,1,1,1,1]]
        before = copy.deepcopy(grid)
        want = copy.deepcopy(grid)
        want[4][:3] = [8,8,8]
        self.assertEqual(m.transform(grid, {'min_size':2,'connectivity':4}), want)
        self.assertEqual(m.transform(grid, {'min_size':3,'connectivity':8}), want)
        want[1][1] = want[2][2] = 8
        self.assertEqual(m.transform(grid, {'min_size':2,'connectivity':8}), want)
        self.assertEqual(m.transform(grid, {'min_size':4,'connectivity':4}), grid)
        self.assertEqual(grid, before)

    def test_strict_parameters_counts_and_sampling_exhaustion(self):
        m = self.module()
        for settings in ({}, {'min_size':True,'connectivity':4},
                         {'min_size':2.0,'connectivity':4}, {'min_size':5,'connectivity':4},
                         {'min_size':2,'connectivity':6}, dict(m.DEFAULT, extra=0)):
            with self.assertRaises(ValueError): m.program(settings)
        for key, bad in [('seed',True),('seed',2.0),('demos',1),('demos',True),
                         ('queries',0),('queries',4.0),('queries',9),('max_attempts',False)]:
            args = dict(seed=9, settings=m.DEFAULT, demos=3, queries=4, max_attempts=128)
            args[key] = bad
            with self.assertRaises(ValueError): m.generate(**args)
        with self.assertRaises(RuntimeError):
            m.generate(9, m.DEFAULT, demos=3, queries=4, max_attempts=1)
        for grid in ([[0,1]], [[True]], [[0],[0,1]], [[11]], []):
            with self.assertRaises(ValueError): m.transform(grid, m.DEFAULT)

    def test_canonical_default_exact_and_all_settings_change_behavior(self):
        m = self.module()
        selected = {json.loads(s)['program_solution'] for s in
                    (REPO/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
                    if json.loads(s).get('task_id') == m.TASK_ID}
        self.assertEqual(selected, {m.program(m.DEFAULT)})
        self.assertEqual(len({m.program(s) for s in m.SETTINGS}), 6)
        for setting in m.SETTINGS:
            ep = m.generate(17, setting, demos=3, queries=4)
            self.assertEqual(ep['settings'], setting)
            self.assertEqual(ep['certificate']['survivors'], [setting])
            self.assertEqual(len(ep['certificate']['queries']), 4)

    def test_determinism_counts_diverse_sizes_and_query_independence(self):
        m = self.module()
        random.seed(100)
        state = random.getstate()
        a = m.generate(61, m.DEFAULT, demos=3, queries=4)
        self.assertEqual(random.getstate(), state)
        b = m.generate(61, m.DEFAULT, demos=3, queries=4)
        self.assertEqual(a,b)
        shorter = m.generate(61, m.DEFAULT, demos=3, queries=1)
        self.assertEqual(a['train'],shorter['train'])
        pairs = a['train'] + a['test']
        self.assertEqual(len(pairs),7)
        self.assertEqual(len({json.dumps(p['input']) for p in pairs}),7)
        self.assertIn((13,13), {(len(p['input']),len(p['input'][0])) for p in pairs})
        self.assertTrue(any(len(p['input']) > 13 for p in pairs))
        changed = copy.deepcopy(a)
        changed['test'][0]['output'] = [[9]]
        self.assertEqual(m.fit_demos(changed['train']), a['certificate']['survivors'])
        with self.assertRaises(ValueError): m.certify(changed)

    def test_adapter_and_maximum_supported_counts(self):
        m = self.module()
        spec = importlib.util.spec_from_file_location('component_adapter', HERE/'adapter.py')
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        ep = adapter.generate(0, m.DEFAULT, 8, 8)
        self.assertEqual((len(ep['train']),len(ep['test'])),(8,8))
        self.assertEqual(ep['program_solution'],adapter.program(m.DEFAULT))
        self.assertEqual(len({json.dumps(p['input']) for p in ep['train']+ep['test']}),16)
        implicit = m.generate(19, demos=2, queries=1)
        self.assertIn(implicit['settings'],m.SETTINGS)
        self.assertEqual(implicit,m.generate(19,demos=2,queries=1))

    def test_certificates_reject_noninteger_output_labels(self):
        m = self.module()
        original = m.generate(17, m.DEFAULT, demos=2, queries=1)
        for partition in ('train', 'test'):
            changed = copy.deepcopy(original)
            changed[partition][0]['output'] = [
                [float(cell) for cell in row] for row in changed[partition][0]['output']]
            with self.subTest(partition=partition), self.assertRaises(ValueError):
                m.certify(changed)
        changed = copy.deepcopy(original)
        grid = changed['test'][0]['output']
        r,c = next((r,c) for r,row in enumerate(grid) for c,value in enumerate(row) if value in (0,1))
        grid[r][c] = bool(grid[r][c])
        with self.assertRaises(ValueError): m.certify(changed)

    def test_racket_semantics_and_public_writer_invariance(self):
        m = self.module()
        from reviewer_support import public_challenge_bytes, public_challenge_id
        with m.RacketRunner() as run:
            for settings in m.SETTINGS:
                grid = [[1]*8 for _ in range(8)]
                grid[0][0]=grid[1][1]=0
                grid[3][0:3]=[3,3,3]
                grid[5][0:4]=[4,4,4,4]
                self.assertEqual(run(m.program(settings),grid),m.transform(grid,settings))
            ep = m.generate(37, m.DEFAULT, demos=2, queries=4)
            ep['certificate'] = m.certify(ep, run)
            self.assertTrue(ep['certificate']['racket_checked'])
            other = m.generate(38, m.DEFAULT, demos=2, queries=4)
            other['certificate'] = m.certify(other, run)
            mutated=copy.deepcopy(ep)
            mutated['seed']=-999
            mutated['settings']={'private':'different'}
            mutated['program_solution']='private altered program'
            mutated['test'][0]['output']=[[9]]
            with tempfile.TemporaryDirectory() as tmp:
                a,b=Path(tmp)/'a',Path(tmp)/'b'
                m.write_batch([ep,other], a)
                m.write_batch([other,mutated], b)
                self.assertEqual((a/'public.jsonl').read_bytes(),(b/'public.jsonl').read_bytes())
                pa=sorted((a/'public').iterdir()); pb=sorted((b/'public').iterdir())
                self.assertEqual([x.name for x in pa],[x.name for x in pb])
                expected = a/'public'/(public_challenge_id(ep)+'.json')
                self.assertEqual(expected.read_bytes(), public_challenge_bytes(ep))
                self.assertEqual([json.loads(line) for line in (a/'public.jsonl').read_text().splitlines()],
                                 [json.loads(path.read_bytes()) for path in pa])
                self.assertEqual(pa[0].stem,hashlib.sha256(pa[0].read_bytes()).hexdigest())
                visible=json.loads(pa[0].read_bytes())
                self.assertEqual(set(visible),{'train','test'})
                self.assertTrue(all(set(p)=={'input'} for p in visible['test']))
                with self.assertRaises(FileExistsError): m.write_batch([ep],a)
                duplicate=Path(tmp)/'duplicate'
                with self.assertRaises(ValueError): m.write_batch([ep,mutated],duplicate)
                self.assertFalse(duplicate.exists())

if __name__ == '__main__': unittest.main()
