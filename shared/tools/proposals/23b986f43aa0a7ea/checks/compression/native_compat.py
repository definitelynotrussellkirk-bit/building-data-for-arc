"""Synthetic integration with the unchanged official retention reader."""
from pathlib import Path
import hashlib, json, os, subprocess, sys, tempfile
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
TOOL=WORK/'repo/generators/7944933e200f/workspace/evidence_archive.py'
sys.path.insert(0,str(WORK/'repo/src'))
from arcpuzzles.review_retention import _compressed_dependencies, _verify_compressed_dependencies
with tempfile.TemporaryDirectory(prefix='native-compat-',dir=HERE) as temporary:
    work=Path(temporary);(work/'checks').mkdir();(work/'checks/example.json').write_text('{"retained_failure":true}\n')
    command=[sys.executable,str(TOOL),'pack','--work',str(work),'--path','checks/example.json']
    result=subprocess.run(command,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    assert result.returncode==0,result.stderr
    names={file.relative_to(work).as_posix() for file in work.rglob('*') if file.is_file()}
    selected,rows=_compressed_dependencies({'checks/compressed/MANIFEST.json'},names,lambda path:(work/path).read_bytes())
    _verify_compressed_dependencies(rows,lambda path:(work/path).read_bytes())
    assert len(rows)==1 and len(selected)==2
    receipt={'status':'native_retention_verified','schema':'review-large-evidence-v1','native_reader':'arcpuzzles.review_retention._compressed_dependencies + _verify_compressed_dependencies','synthetic_archives':1,'selected_manifest_and_payload_members':len(selected),'compressed_and_original_hashes_verified':True,'tool_sha256':hashlib.sha256(TOOL.read_bytes()).hexdigest(),'scope':'Synthetic compatibility only; temporary fixture removed. No production evidence changed.'}
(HERE/'native_compat.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,sort_keys=True))
