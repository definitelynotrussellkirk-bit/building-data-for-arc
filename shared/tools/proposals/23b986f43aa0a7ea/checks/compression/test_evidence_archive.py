"""CLI regression tests; all fixtures are temporary synthetic evidence."""
import gzip, hashlib, json, os
from pathlib import Path
import subprocess, sys, tempfile, unittest
TOOL=Path(__file__).resolve().parents[2]/'repo/generators/7944933e200f/workspace/evidence_archive.py'
class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='archive-test-',dir=Path(__file__).parent)
        self.root=Path(self.temp.name);self.work=self.root/'work';(self.work/'checks').mkdir(parents=True)
        self.raw=b'{"failed":true,"data":"'+b'abcd'*10000+b'"}\n'
        (self.work/'checks/failure.json').write_bytes(self.raw)
        self.manifest='checks/compressed/MANIFEST.json'
    def tearDown(self):self.temp.cleanup()
    def run_tool(self,*args,ok=True):
        result=subprocess.run([sys.executable,str(TOOL),*args],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        if ok:self.assertEqual(result.returncode,0,result.stderr)
        else:self.assertNotEqual(result.returncode,0,result.stdout)
        return result
    def pack(self):
        self.run_tool('pack','--work',str(self.work),'--manifest',self.manifest,'--path','checks/failure.json')
        return json.loads((self.work/self.manifest).read_text())
    def test_roundtrip_deterministic_and_existing_content_preserved(self):
        manifest=self.pack(); row=manifest['files'][0]; first=(self.work/row['compressed_path']).read_bytes()
        self.pack();self.assertEqual((self.work/row['compressed_path']).read_bytes(),first)
        self.run_tool('pack','--work',str(self.work),'--manifest','checks/independent/MANIFEST.json','--path','checks/failure.json')
        second=json.loads((self.work/'checks/independent/MANIFEST.json').read_text())
        self.assertEqual((self.work/second['files'][0]['compressed_path']).read_bytes(),first)
        self.run_tool('verify','--work',str(self.work),'--manifest',self.manifest)
        dest=self.root/'restored'
        self.run_tool('restore','--work',str(self.work),'--manifest',self.manifest,'--destination',str(dest))
        self.assertEqual((dest/'checks/failure.json').read_bytes(),self.raw)
        self.assertEqual((self.work/'checks/failure.json').read_bytes(),self.raw)
        self.run_tool('restore','--work',str(self.work),'--manifest',self.manifest,'--destination',str(dest))
        (dest/'checks/failure.json').write_bytes(b'keep me')
        self.run_tool('restore','--work',str(self.work),'--manifest',self.manifest,'--destination',str(dest),ok=False)
        self.assertEqual((dest/'checks/failure.json').read_bytes(),b'keep me')
    def test_corrupt_payload_rejected_even_with_forged_compressed_hash(self):
        manifest=self.pack();row=manifest['files'][0];path=self.work/row['compressed_path']
        raw=bytearray(path.read_bytes());raw[-8]^=1;path.write_bytes(raw)
        self.run_tool('verify','--work',str(self.work),'--manifest',self.manifest,ok=False)
        row['compressed_sha256']=hashlib.sha256(raw).hexdigest()
        (self.work/self.manifest).write_text(json.dumps(manifest))
        self.run_tool('verify','--work',str(self.work),'--manifest',self.manifest,ok=False)
    def test_manifest_traversal_rejected_before_restore(self):
        manifest=self.pack();manifest['files'][0]['original_path']='checks/../../escape.json'
        (self.work/self.manifest).write_text(json.dumps(manifest));dest=self.root/'restore'
        self.run_tool('restore','--work',str(self.work),'--manifest',self.manifest,'--destination',str(dest),ok=False)
        self.assertFalse(dest.exists());self.assertFalse((self.root/'escape.json').exists())
    def test_symlink_source_and_payload_rejected(self):
        (self.work/'checks/link.json').symlink_to(self.work/'checks/failure.json')
        self.run_tool('pack','--work',str(self.work),'--manifest',self.manifest,'--path','checks/link.json',ok=False)
        manifest=self.pack();path=self.work/manifest['files'][0]['compressed_path'];copy=self.root/'copy.gz';copy.write_bytes(path.read_bytes());path.unlink();path.symlink_to(copy)
        self.run_tool('verify','--work',str(self.work),'--manifest',self.manifest,ok=False)
    def test_expansion_size_and_aggregate_limit_rejected(self):
        manifest=self.pack()
        self.run_tool('verify','--work',str(self.work),'--manifest',self.manifest,'--max-bytes','10',ok=False)
        manifest['files'][0]['original_bytes']=10;manifest['original_bytes']=10
        (self.work/self.manifest).write_text(json.dumps(manifest))
        self.run_tool('verify','--work',str(self.work),'--manifest',self.manifest,ok=False)
    def test_absolute_path_and_payload_conflict_rejected(self):
        self.run_tool('pack','--work',str(self.work),'--manifest',self.manifest,'--path',str(self.work/'checks/failure.json'),ok=False)
        payload=self.work/'checks/compressed/payloads/failure.json.gz';payload.parent.mkdir(parents=True);payload.write_bytes(b'keep payload')
        self.run_tool('pack','--work',str(self.work),'--manifest',self.manifest,'--path','checks/failure.json',ok=False)
        self.assertEqual(payload.read_bytes(),b'keep payload')
        self.assertFalse((self.work/self.manifest).exists())
    def test_conflicting_manifest_not_overwritten(self):
        self.pack();before=(self.work/self.manifest).read_bytes()
        (self.work/'checks/another.json').write_text('{}')
        self.run_tool('pack','--work',str(self.work),'--manifest',self.manifest,'--path','checks/another.json',ok=False)
        self.assertEqual((self.work/self.manifest).read_bytes(),before)
if __name__=='__main__':unittest.main(verbosity=2)
