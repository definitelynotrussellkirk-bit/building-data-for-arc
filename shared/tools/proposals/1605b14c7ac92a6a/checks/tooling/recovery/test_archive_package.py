"""Bounded synthetic checks for sparse packaging; never loads real task bodies."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).parent))
import sparse_packet as sparse

SOURCE = Path(os.environ.get('ARC_PACKET_ZIP', str(Path(__file__).parents[1] / 'upload/SEND-THIS-ARCpuzzles-review(20261019-075521).zip')))
sha = lambda raw: hashlib.sha256(raw).hexdigest()


class ArchivePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generic tooling only; bytes are copied, never printed or analyzed.
        with zipfile.ZipFile(SOURCE) as z:
            cls.tooling = {n.removeprefix('WORK/'): z.read(n) for n in z.namelist()
                if n.startswith('WORK/repo/src/arcpuzzles/') and n.endswith('.py')}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='archive-package-test-')
        self.base = Path(self.tmp.name)
        self.files = {**self.tooling,
            'repo/generators/fake/generator.py': b'def generate():\n    return 1\n',
            'repo/generators/fake/notes.md': b'Synthetic note\n',
            'repo/shared/data/canonical/puzzles.jsonl': b'{"task_id":"fake","v":1}\n{"task_id":"other","v":0}\n',
            'repo/unmaterialized.txt': b'not extracted\n',
            'repo/materialized.txt': b'untouched\n'}
        self.manifest = {'schema': sparse.SCHEMA, 'files': {n:sha(v) for n,v in self.files.items()},
            'layout': {'workspace':'WORK', 'entry_files': {'START-HERE.md':sha(b'Start\n'),'review.py':sha(b'# Entry\n')}},
            'main_ids':['fake'], 'all_ids':['fake'], 'questions':[{'id':'q'}],
            'generators': {'fake': {'generator_sha256':sha(self.files['repo/generators/fake/generator.py']), 'rule_task_id':'fake'}}}
        self.archive = self.base/'source.zip'
        with zipfile.ZipFile(self.archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for n,v in self.files.items(): z.writestr('WORK/'+n,v)
            z.writestr('WORK/PACKET-MANIFEST.json',sparse.canonical(self.manifest))
            z.writestr('START-HERE.md',b'Start\n'); z.writestr('review.py',b'# Entry\n')
        self.contract={'schema':'arcpuzzles-full-assignment-v2', 'packet_id':sha(sparse.canonical(self.manifest)),
            'task_id':'fake','assignment_id':'review-'+'a'*16,'generator':self.manifest['generators']['fake'],
            'seed':'00'*32,'question':{'id':'q'}, 'baseline_sha256':{n:sha(v) for n,v in self.files.items()
                if n.startswith('repo/generators/fake/') or n=='repo/shared/data/canonical/puzzles.jsonl'}}
        self.full=self.base/'full'/'WORK'; self.work=self.base/'sparse'/'WORK'
        for root in [self.full,self.work]:
            root.mkdir(parents=True)
            for n,v in self.files.items():
                if root==self.work and n=='repo/unmaterialized.txt': continue
                p=root/n; p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
            (root/'PACKET-MANIFEST.json').write_bytes(sparse.canonical(self.manifest))
            (root/'ASSIGNMENT.json').write_bytes(sparse.canonical(self.contract))
            for n in self.contract['baseline_sha256']:
                p=root/'.review/baseline'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(self.files[n])
            for n in ['REVIEW.md','DECISIONS.md','QUESTION_ANSWER.md','FEEDBACK_TO_CODEX.md']:
                (root/n).write_text('Synthetic review\n')
            (root/'RESULTS.json').write_text(json.dumps({'completion_state':'in_progress','stopping_reason':'Synthetic test'}))
            (root/'repo/generators/fake/generator.py').write_bytes(b'def generate():\n    return 2\n')
            p=root/'repo/generators/fake/tests/test_new.py';p.parent.mkdir();p.write_bytes(b'assert 1 == 1\n')
        self.state=self.work.parent/'.recovery';self.state.mkdir()
        self.binding={'archive_sha256':sparse.file_hash(self.archive),'manifest_sha256':sha(sparse.canonical(self.manifest))}
        self.event={**self.binding,'schema':'arcpuzzles-sparse-extraction-v1','main_task_id':'fake','blind_task_id':'other',
            'question_id':'q','additional_task_ids':[], 'workspace':str(self.work),'previous_receipt':None,
            'files': {'WORK/'+n:sha(v) for n,v in self.files.items() if n!='repo/unmaterialized.txt'}}
        (self.state/'seed.json').write_bytes(sparse.canonical({**self.binding,'schema':'arcpuzzles-sparse-recovery-seed-v1','seed':self.contract['seed']}))
        self.event['files']['WORK/PACKET-MANIFEST.json']=self.binding['manifest_sha256']
        self.reference=self.write_event(self.event,1)

    def tearDown(self):
        for name in list(sys.modules):
            if name=='arcpuzzles' or name.startswith('arcpuzzles.'): del sys.modules[name]
        self.tmp.cleanup()

    def write_event(self,event,index):
        name=f'materialization-{index:06d}.json';raw=sparse.canonical(event)+b'\n'
        (self.state/name).write_bytes(raw)
        reference={'filename':name,'sha256':sha(raw)}
        (self.state/'extraction.json').write_bytes(sparse.canonical(reference))
        return reference

    def package(self, **kw):
        from archive_package import build_archive_return
        return build_archive_return(self.archive,self.work,self.base/'sparse.zip',
            receipt_sha256=self.reference['sha256'],**kw)

    def test_extension_exists(self):
        self.assertIsNotNone(importlib.util.find_spec('archive_package'), 'archive-backed extension missing')

    def test_byte_identical_to_official_full_tree(self):
        result=self.package()
        from arcpuzzles.review_full_return import build_full_return
        full=build_full_return(self.full,self.base/'full.zip')
        self.assertEqual(Path(result['zip']).read_bytes(),Path(full['zip']).read_bytes())
        self.assertEqual(result['archive_verification']['verified_source_files'],len(self.files)+3)

    def test_preserves_official_assembly_function(self):
        self.package()
        import archive_package
        import inspect
        import arcpuzzles.review_full_return as official
        expected=inspect.getsource(official.build_full_return).split('    payload = {"ASSIGNMENT.json": contract_bytes}',1)[1]
        actual=inspect.getsource(archive_package._assemble_return).split('    payload = {"ASSIGNMENT.json": contract_bytes}',1)[1]
        self.assertEqual(actual.replace('from arcpuzzles.review_curriculum import','from .review_curriculum import'),expected)

    def test_cli_exposes_explicit_provenance_arguments(self):
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('archive_package.py')),'--help'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('--receipt-sha256',result.stdout)
        self.assertIn('--verification-out',result.stdout)

    def test_bundle_and_command_evidence_equal_official(self):
        for work in [self.work,self.full]:
            p=work/'checks/a.log';p.parent.mkdir();p.write_text('Synthetic verification\n')
            supplied=json.loads((work/'RESULTS.json').read_text())
            supplied['verification_commands']=[{'cwd':'repo','argv':['python','-V'],'evidence_paths':['checks/a.log']}]
            (work/'RESULTS.json').write_text(json.dumps(supplied))
        result=self.package(bundle_evidence=True)
        from arcpuzzles.review_full_return import build_full_return
        full=build_full_return(self.full,self.base/'full.zip',bundle_evidence=True)
        self.assertEqual(Path(result['zip']).read_bytes(),Path(full['zip']).read_bytes())

    def test_selected_canonical_row_and_no_newline_equal_official(self):
        for work in [self.work,self.full]:
            (work/'repo/shared/data/canonical/puzzles.jsonl').write_bytes(b'{"task_id":"fake","v":2}\n{"task_id":"other","v":0}\n')
            (work/'repo/generators/fake/notes.md').write_bytes(b'line with literal \r inside and no final newline')
        result=self.package()
        from arcpuzzles.review_full_return import build_full_return
        full=build_full_return(self.full,self.base/'full.zip')
        self.assertEqual(Path(result['zip']).read_bytes(),Path(full['zip']).read_bytes())

    def test_seed_contract_binding_rejected(self):
        contract={**self.contract,'seed':'ff'*32}
        (self.work/'ASSIGNMENT.json').write_bytes(sparse.canonical(contract))
        with self.assertRaisesRegex(ValueError,'seed'):self.package()

    def test_cli_writes_separate_verification_receipt(self):
        out=self.base/'cli.zip';verification=self.base/'verification.json'
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('archive_package.py')),
            str(self.archive),str(self.work),'--out',str(out),'--receipt-sha256',self.reference['sha256'],
            '--verification-out',str(verification)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        receipt=json.loads(verification.read_bytes())
        self.assertEqual(receipt['return_zip_sha256'],sparse.file_hash(out))
        self.assertFalse(receipt['full_physical_tree_check_run'])

    def test_original_helper_version_is_explicitly_bound(self):
        import archive_package
        self.assertEqual(getattr(archive_package,'OFFICIAL_RETURN_SOURCE_SHA256',None),sha(self.tooling['repo/src/arcpuzzles/review_full_return.py']))

    def test_newly_hydrated_unchanged_original_is_accepted(self):
        (self.work/'repo/unmaterialized.txt').write_bytes(self.files['repo/unmaterialized.txt'])
        result=self.package()
        from arcpuzzles.review_full_return import build_full_return
        full=build_full_return(self.full,self.base/'full.zip')
        self.assertEqual(Path(result['zip']).read_bytes(),Path(full['zip']).read_bytes())

    def test_malformed_optional_solve_still_rejected(self):
        p=self.work/'solve';p.mkdir();(p/'summary.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'Invalid reviewer solve'):self.package()
        self.assertFalse((self.base/'sparse.zip').exists())

    def test_output_collision_never_overwrites(self):
        (self.base/'sparse.zip').write_bytes(b'existing user bytes')
        with self.assertRaises(FileExistsError):self.package()
        self.assertEqual((self.base/'sparse.zip').read_bytes(),b'existing user bytes')

    def test_actual_zip64_packet_helpers_load_from_verified_source(self):
        from archive_package import load_official
        with zipfile.ZipFile(SOURCE) as original:
            self.assertGreater(len(original.infolist()),65535)
            manifest,expected=sparse.verify_archive(original)
        with load_official(SOURCE,expected) as official:
            self.assertEqual(official.__name__,'arcpuzzles.review_full_return')
            self.assertTrue(str(official.__file__).startswith(str(SOURCE)+'/WORK/repo/src/'))
            self.assertEqual(sha(official.__loader__.get_source(official.__name__).encode()),
                             manifest['files']['repo/src/arcpuzzles/review_full_return.py'])

    def test_source_loader_rejects_helper_hash_substitution(self):
        from archive_package import load_official
        with zipfile.ZipFile(self.archive) as original:
            _,expected=sparse.verify_archive(original)
        expected['WORK/repo/src/arcpuzzles/catalog.py']='0'*64
        with self.assertRaisesRegex(ValueError,'Original helper source hash differs'):
            with load_official(self.archive,expected):pass

    def test_source_loader_rejects_overlay_package_already_loaded(self):
        from archive_package import load_official
        import types
        bad=types.ModuleType('arcpuzzles');bad.__file__=str(self.work/'repo/src/arcpuzzles/__init__.py')
        sys.modules['arcpuzzles']=bad
        with zipfile.ZipFile(self.archive) as original:
            _,expected=sparse.verify_archive(original)
        with self.assertRaisesRegex(ValueError,'different arcpuzzles'):
            with load_official(self.archive,expected):pass

    def test_deleted_materialized_source_rejected(self):
        (self.work/'repo/materialized.txt').unlink()
        with self.assertRaisesRegex(ValueError,'materialized'):self.package()

    def test_modified_materialized_helper_rejected(self):
        (self.work/'repo/materialized.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError,'source'):self.package()

    def test_modified_newly_hydrated_original_rejected(self):
        (self.work/'repo/unmaterialized.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError,'source'):self.package()

    def test_missing_candidate_rejected(self):
        (self.work/'repo/generators/fake/generator.py').unlink()
        with self.assertRaisesRegex(ValueError,'materialized|changed source'):self.package()

    def test_fabricated_baseline_for_new_source_rejected(self):
        p=self.work/'.review/baseline/repo/generators/fake/tests/test_new.py'
        p.parent.mkdir();p.write_bytes((self.work/'repo/generators/fake/tests/test_new.py').read_bytes())
        with self.assertRaisesRegex(ValueError,'baseline'):self.package()

    def test_changed_frozen_baseline_rejected(self):
        (self.work/'.review/baseline/repo/generators/fake/generator.py').write_text('changed')
        with self.assertRaisesRegex(ValueError,'baseline'):self.package()

    def test_out_of_scope_new_file_rejected(self):
        (self.work/'repo/forbidden.py').write_text('new')
        with self.assertRaisesRegex(ValueError,'Undeclared'):self.package()

    def test_ancestor_symlink_rejected(self):
        p=self.work/'repo/generators/fake/tests';q=self.base/'outside';p.rename(q);p.symlink_to(q,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'[Ss]ymlink'):self.package()

    def test_unrelated_canonical_row_rejected(self):
        (self.work/'repo/shared/data/canonical/puzzles.jsonl').write_bytes(b'{"task_id":"fake","v":1}\n{"task_id":"other","v":1}\n')
        with self.assertRaisesRegex(ValueError,'unrelated canonical'):self.package()

    def test_executable_candidate_rejected(self):
        (self.work/'repo/generators/fake/generator.py').chmod(0o755)
        with self.assertRaisesRegex(ValueError,'Unsafe changed source'):self.package()

    def test_receipt_head_mismatch_rejected(self):
        self.reference['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'receipt'):self.package()

    def test_cumulative_receipt_rollback_rejected(self):
        old=self.reference.copy();event={**self.event,'files':dict(self.event['files']),'previous_receipt':old}
        event['files'].pop('WORK/repo/materialized.txt')
        self.reference=self.write_event(event,2)
        (self.work/'repo/materialized.txt').unlink()
        with self.assertRaisesRegex(ValueError,'cumulative|inventory'):self.package()

    def test_corrupt_omitted_archive_source_rejected(self):
        other=self.base/'changed.zip'
        with zipfile.ZipFile(self.archive) as source,zipfile.ZipFile(other,'w') as target:
            for i in source.infolist():
                raw=source.read(i)
                if i.filename=='WORK/repo/unmaterialized.txt':raw=b'bad bytes'
                target.writestr(i,raw)
        self.archive=other
        with self.assertRaisesRegex(ValueError,'Hash mismatch|archive.*binding'):self.package()

    def test_official_validator_still_rejects_missing_document(self):
        (self.work/'REVIEW.md').unlink()
        with self.assertRaisesRegex(ValueError,'Missing review document'):self.package()

if __name__=='__main__':unittest.main()
