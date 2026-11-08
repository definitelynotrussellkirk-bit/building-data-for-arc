"""Behavior tests for a separately proposed evaluation-inspired family."""
import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

HOME=Path(__file__).resolve().parents[1]
SOURCE=HOME/'workspace/parametric/occluded_rectangles.py'
if SOURCE.exists():
    spec=importlib.util.spec_from_file_location('occluded_rectangles', SOURCE)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
else:
    m=None

class OccludedRectanglesTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'bounded occlusion/crop prototype has not been implemented')

    def test_four_executed_queries_independent_of_demo_count(self):
        for paint in ('outline','filled'):
            episode=m.generate_episode(seed=17, paint=paint, n_train=1)
            self.assertEqual(len(episode['challenge']['train']),1)
            self.assertEqual(len(episode['challenge']['test']),4)
            inputs=[p['input'] for p in episode['challenge']['train']+episode['challenge']['test']]
            self.assertEqual(len({json.dumps(g) for g in inputs}),5)
            labels=m.racket_labels(inputs,paint)
            expected=[p['output'] for p in episode['challenge']['train']]+episode['private']['query_outputs']
            self.assertEqual(labels,expected)
            self.assertTrue(all(a==m.solve(g,paint) for a,g in zip(labels,inputs)))
            self.assertEqual(episode['certificate']['parameter_survivors'],[paint])
            self.assertEqual(episode['certificate']['rival_survivors'],[])
            self.assertEqual(episode['certificate']['evidence_scope'],'demonstrations_only')

    def test_context_changes_answer_without_changing_frame_interior(self):
        a,b=m.context_witness()
        self.assertEqual(m.frame_interior(a),m.frame_interior(b))
        self.assertNotEqual(m.solve(a,'outline'),m.solve(b,'outline'))
        self.assertNotEqual(a,b)
        for paint in ('outline','filled'):
            self.assertEqual(m.racket_labels([a,b],paint),[m.solve(a,paint),m.solve(b,paint)])

    def test_exact_controls_and_unknown_paint_rejected(self):
        for key in ('n_train','n_queries','max_attempts'):
            for value in (True,False,0,-1,1.5,'2',None):
                with self.subTest(key=key,value=value), self.assertRaises(ValueError):
                    m.generate_episode(**{key:value})
        for paint in ('striped',None,1):
            with self.assertRaises(ValueError): m.generate_episode(paint=paint)

    def test_retry_budget_is_global_and_bounded(self):
        with self.assertRaisesRegex(RuntimeError,'retry bound exhausted'):
            m.generate_episode(max_attempts=1,n_train=1,n_queries=4)
        for key in ('n_train','n_queries','max_attempts'):
            with self.assertRaises(ValueError): m.generate_episode(**{key:10**6})

    def test_batch_rejects_duplicate_inputs_even_if_demo_outputs_differ(self):
        a=m.generate_episode(seed=31,paint='outline')
        b=m.generate_episode(seed=31,paint='filled')
        self.assertNotEqual(m.public_challenge_id(a['challenge']),m.public_challenge_id(b['challenge']))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError,'duplicate input'):
                m.export_batch([a,b],Path(temporary)/'batch')
            self.assertFalse((Path(temporary)/'batch').exists())

    def test_certificate_does_not_consult_queries(self):
        episode=m.generate_episode(seed=9,paint='filled',n_train=2)
        changed=copy.deepcopy(episode['challenge']); changed['test']=[{'input':[[9]]}]
        self.assertEqual(m.certify(changed['train']),episode['certificate'])
        self.assertEqual(m.certify([])['parameter_survivors'],['outline','filled'])

    def test_export_replays_and_rejects_tampered_episode_before_writes(self):
        base=m.generate_episode(seed=42,paint='outline')
        mutations=[]
        for key,value in (('paint','filled'),('seed',True),('seed',43),('n_train',True),
                          ('n_queries',3),('max_attempts',False),('attempts',True),
                          ('rule_sha256','0'*64),('label_runtime','unexecuted')):
            e=copy.deepcopy(base); e['private'][key]=value; mutations.append((key,e))
        e=copy.deepcopy(base); e['private']['query_outputs'][0][0][0]=(e['private']['query_outputs'][0][0][0]+1)%10
        mutations.append(('query_label',e))
        e=copy.deepcopy(base); e['private']['query_outputs'][0][0][0]=False
        mutations.append(('bool_label',e))
        e=copy.deepcopy(base); e['certificate']['parameter_candidates'][0]=False
        mutations.append(('certificate',e))
        with tempfile.TemporaryDirectory() as temporary:
            for i,(name,e) in enumerate(mutations):
                target=Path(temporary)/str(i)
                with self.subTest(mutation=name),self.assertRaises(ValueError): m.export_batch([e],target)
                self.assertFalse(target.exists())

    def test_export_verifier_is_portable_and_rejects_label_or_byte_tampering(self):
        episode=m.generate_episode(seed=72,paint='filled',n_train=1,n_queries=4)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'export'; manifest=m.export_batch([episode],root)
            moved=Path(temporary)/'relocated'; shutil.move(root,moved)
            report=m.verify_export(moved)
            self.assertEqual(report['status'],'verified')
            self.assertEqual(report['queries'],4)
            row=manifest['rows'][0]; private=moved/row['private_path']
            original=private.read_bytes(); value=json.loads(original)
            value['certificate']['parameter_candidates'][0]=False
            private.write_text(json.dumps(value))
            with self.assertRaises(ValueError): m.verify_export(moved)
            private.write_bytes(original)
            public=moved/row['public_path']; public.write_bytes(public.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'canonical public bytes'): m.verify_export(moved)

    def test_cli_exposes_independent_query_budget_and_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'cli'
            run=subprocess.run([sys.executable,str(SOURCE),'--out',str(target),'--seed','86',
                '--n-train','1','--n-queries','2','--max-attempts','7'],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            manifest=json.loads(run.stdout); row=manifest['rows'][0]
            hidden=json.loads((target/row['private_path']).read_text())
            self.assertEqual((hidden['n_train'],hidden['n_queries'],hidden['max_attempts']),(1,2,7))
            check=subprocess.run([sys.executable,str(SOURCE),'--verify',str(target)],capture_output=True,text=True)
            self.assertEqual(check.returncode,0,check.stderr)
            self.assertEqual(json.loads(check.stdout)['queries'],2)

    def test_export_visible_ids_sorted_private_labels_separate_duplicates_rejected(self):
        episodes=[m.generate_episode(seed=s,paint=p) for s,p in ((7,'outline'),(3,'filled'))]
        with tempfile.TemporaryDirectory() as temporary:
            result=m.export_batch(episodes,Path(temporary)/'batch')
            ids=[row['id'] for row in result['rows']]
            self.assertEqual(ids,sorted(ids))
            for row in result['rows']:
                self.assertFalse(Path(row['public_path']).is_absolute())
                public=(Path(temporary)/'batch'/row['public_path']).read_bytes()
                self.assertEqual(public,m.public_challenge_bytes(next(e['challenge'] for e in episodes if m.public_challenge_id(e['challenge'])==row['id'])))
                self.assertTrue(all(set(p)=={'input'} for p in json.loads(public)['test']))
                private=json.loads((Path(temporary)/'batch'/row['private_path']).read_text())
                self.assertEqual(len(private['query_outputs']),4)
            with self.assertRaises(ValueError): m.export_batch([episodes[0],episodes[0]],Path(temporary)/'duplicate')

if __name__=='__main__': unittest.main()
