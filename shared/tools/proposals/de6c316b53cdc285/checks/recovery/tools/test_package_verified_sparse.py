"""Tiny synthetic packets exercising the unchanged official builder/parser."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'packet/WORK/repo/src'))
from arcpuzzles.review_full_return import build_full_return, validate_full_return
from package_verified_sparse import SourceView


def sha(b): return hashlib.sha256(b).hexdigest()
def canon(o): return json.dumps(o,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()


class SparseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.work = self.base/'WORK'; self.work.mkdir()
        self.sources = {'repo/generators/task/generator.py':b'original selected\n',
                        'repo/shared/present.txt':b'physical shared\n',
                        'repo/shared/archived.txt':b'opaque exact archived bytes\x00\xff'}
        self.manifest = {'schema':'arcpuzzles-full-packet-v2','files':{k:sha(v) for k,v in self.sources.items()},
                         'layout':{'workspace':'WORK','entry_files':{}},'main_ids':['task'],
                         'generators':{'task':{'generator_sha256':sha(self.sources['repo/generators/task/generator.py'])}},'questions':[{}]}
        raw = canon(self.manifest); self.put('PACKET-MANIFEST.json',raw)
        self.archive=self.base/'original.zip'
        with zipfile.ZipFile(self.archive,'w') as z:
            z.writestr('WORK/PACKET-MANIFEST.json',raw)
            for p,b in self.sources.items(): z.writestr('WORK/'+p,b)
        self.inventory={'schema':'arcpuzzles-materialized-sources-v1','archive_sha256':sha(self.archive.read_bytes()),'manifest_sha256':sha(raw),
                        'paths':['repo/generators/task/generator.py','repo/shared/present.txt']}
        self.contract={'schema':'arcpuzzles-full-assignment-v2','packet_id':sha(raw),'assignment_id':'review-0123456789abcdef',
                       'task_id':'task','generator':self.manifest['generators']['task'],'question':{},
                       'baseline_sha256':{'repo/generators/task/generator.py':sha(self.sources['repo/generators/task/generator.py'])}}
        self.put('ASSIGNMENT.json',canon(self.contract))
        for p in self.inventory['paths']: self.put(p,self.sources[p])
        self.put('.review/baseline/repo/generators/task/generator.py',self.sources['repo/generators/task/generator.py'])
        for p in ['REVIEW.md','DECISIONS.md','QUESTION_ANSWER.md','FEEDBACK_TO_CODEX.md']: self.put(p,b'Synthetic fixture.\n')

    def put(self,p,b):
        path=self.work/p; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(b)

    def run_build(self):
        with SourceView(self.work,self.archive,self.inventory) as view:
            result=build_full_return(view.root,self.base/'return.zip')
            with zipfile.ZipFile(result['zip']) as z: checked=validate_full_return(z,self.manifest)
            return result,checked,view.receipt()

    def test_exact_archive_read_and_official_hashes(self):
        with SourceView(self.work,self.archive,self.inventory) as view:
            self.assertEqual((view.root/'repo/shared/archived.txt').read_bytes(),self.sources['repo/shared/archived.txt'])
        result,checked,receipt=self.run_build()
        self.assertEqual(checked['task_id'],'task')
        self.assertEqual(receipt['fallback_files'],1)
        self.assertEqual(receipt['fallback_bytes'],len(self.sources['repo/shared/archived.txt']))
        self.assertEqual(receipt['fallback_inventory_sha256'],sha(canon([{'path':'repo/shared/archived.txt','sha256':self.manifest['files']['repo/shared/archived.txt'],'bytes':len(self.sources['repo/shared/archived.txt'])}])))

    def test_shared_tamper_rejected(self):
        self.put('repo/shared/present.txt',b'tampered')
        with self.assertRaisesRegex(ValueError,'Changed or missing shared packet source'): self.run_build()

    def test_physical_symlink_rejected(self):
        p=self.work/'repo/shared/present.txt'; p.unlink(); p.symlink_to(self.work/'REVIEW.md')
        with self.assertRaises((ValueError,OSError)): self.run_build()

    def test_new_source_rejected(self):
        self.put('repo/shared/new.txt',b'new')
        with self.assertRaisesRegex(ValueError,'Undeclared new source'): self.run_build()

    def test_deleted_materialized_source_rejected(self):
        (self.work/'repo/shared/present.txt').unlink()
        with self.assertRaisesRegex(ValueError,'materialized'): self.run_build()

    def test_missing_selected_source_rejected(self):
        (self.work/'repo/generators/task/generator.py').unlink()
        with self.assertRaises((ValueError,FileNotFoundError)): self.run_build()

    def test_baseline_never_falls_back(self):
        (self.work/'.review/baseline/repo/generators/task/generator.py').unlink()
        with self.assertRaisesRegex(ValueError,'Frozen baseline changed'): self.run_build()

    def test_duplicate_archive_rejected(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(self.archive,'a') as z: z.writestr('WORK/repo/shared/archived.txt',b'x')
        self.inventory['archive_sha256']=sha(self.archive.read_bytes())
        with self.assertRaisesRegex(ValueError,'duplicate'): self.run_build()

    def test_unsafe_archive_rejected(self):
        with zipfile.ZipFile(self.archive,'a') as z: z.writestr('../escape',b'x')
        self.inventory['archive_sha256']=sha(self.archive.read_bytes())
        with self.assertRaisesRegex(ValueError,'unsafe'): self.run_build()

    def test_archive_payload_must_match_manifest_hash(self):
        with zipfile.ZipFile(self.archive,'w') as z:
            z.writestr('WORK/PACKET-MANIFEST.json',canon(self.manifest))
            for p,b in self.sources.items():
                z.writestr('WORK/'+p,b'tampered archived bytes' if p.endswith('archived.txt') else b)
        self.inventory['archive_sha256']=sha(self.archive.read_bytes())
        with self.assertRaisesRegex(ValueError,'archive source hash mismatch'): self.run_build()

    def test_new_physical_shadow_must_pass_official_shared_hash(self):
        self.put('repo/shared/archived.txt',b'changed physical overlay')
        with self.assertRaisesRegex(ValueError,'Changed or missing shared packet source'): self.run_build()

    def test_archive_hash_binding_rejected(self):
        self.inventory['archive_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'archive hash differs'): self.run_build()

    def test_manifest_hash_binding_rejected(self):
        self.inventory['manifest_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'manifest hash differs'): self.run_build()


if __name__=='__main__': unittest.main()
