from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
REPO=WORK/'repo'
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
PIN={
 'source':'4189136b4e863e70bf07ee2466d865493554544a72273e4f3918da61da7f7c26',
 'assets':'2f009dcdf55dc5759719ae99edea702d4a08d65ca13f89f3a2c7342d2a8f55bf',
 'index':'91a8c1b52f1d0bdac99a47f9599a857a6017f8d5a13494da9dbca2912783f124',
 'record':'22e40567cbae47d1369a4c9b7a6154189bf8aaeed10e8aeaece92253f629a5a3',
 'probe_script':'68633b822dbad2f185cc5adcd8f97cb33631a600abf1cde6da7c2fcc2178fe53',
}
source=REPO/'generators/defba1ab4f90/generator.py'
assets_path=REPO/'generators/defba1ab4f90/counterexamples/review-a70ce13a9b78aaa3-v0001/audit_assets.json'
index_path=REPO/'generators/defba1ab4f90/evidence/review_index.json'
assert sha(source)==PIN['source']
assert sha(assets_path)==PIN['assets']
assert sha(index_path)==PIN['index']
assert sha(HERE/'retained_audit_probe.py')==PIN['probe_script']
index=json.loads(index_path.read_text())
audit=next(row for row in index['audits'] if row['return_id']=='review-a70ce13a9b78aaa3:v0001')
record=hashlib.sha256(json.dumps(audit,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert record==PIN['record']
assets=json.loads(assets_path.read_text())
verified_assets={}
for row in assets['files']:
    path=REPO/row['path']
    assert path.stat().st_size==row['bytes']
    assert sha(path)==row['sha256']
    verified_assets[row['path']]=row['sha256']
probe_path=HERE/'probe.json'
completed=subprocess.run([sys.executable,str(HERE/'retained_audit_probe.py'),'defba1ab4f90','--out',str(probe_path)],cwd=REPO,text=True,capture_output=True,timeout=90,check=False)
(HERE/'probe.stdout.log').write_text(completed.stdout)
(HERE/'probe.stderr.log').write_text(completed.stderr)
assert completed.returncode==0,(completed.stdout,completed.stderr)
actual=json.loads(probe_path.read_text())
retained_path=REPO/'generators/defba1ab4f90/counterexamples/review-a70ce13a9b78aaa3-v0001/retained/checks/audit/defba1ab4f90/probe.json'
retained=json.loads(retained_path.read_text())
actual_compare=dict(actual); retained_compare=dict(retained)
actual_compare.pop('generator_path',None); retained_compare.pop('generator_path',None)
assert actual_compare==retained_compare
assert actual['generator_sha256']==PIN['source']
assert actual['invalid_scalar_summary']=={'probes':11,'generate_accepted':11,'schedule_accepted':11}
assert actual['canonical_summary']=={'pairs':10,'accepted':10,'mirror_matches':10}
result={
 'schema':'arcpuzzles-ticket-audit-replay-v1',
 'ticket_id':HERE.name,
 'status':'completed',
 'bounded_claim_reproduced':True,
 'audit_resolution_before':audit['resolution'],
 'automatic_audit_clear':False,
 'identity':{**PIN,'verified_asset_count':len(verified_assets)},
 'probe':{
   'canonical_pairs':10,'canonical_accepted':10,'canonical_mirror_matches':10,
   'invalid_scalar_probes':11,'generate_accepted':11,'schedule_profile_accepted':11,
   'matches_retained_probe_except_absolute_source_path':True,
 },
 'limitations':['One exact retained scalar probe only; no defect-lint, semantic gate, battery, or source fix.'],
}
(HERE/'receipt.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'ticket_id':HERE.name,'status':'completed','reproduced':True},sort_keys=True))
