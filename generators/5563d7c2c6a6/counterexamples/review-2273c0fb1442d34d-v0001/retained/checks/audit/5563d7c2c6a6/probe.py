"""Replay audit5563d7c2c6a6; selected generator source stays unchanged."""
import hashlib, importlib.util, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
D=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'repo/shared/runtime'))
P=ROOT/'repo/generators/5563d7c2c6a6/generator.py'
spec=importlib.util.spec_from_file_location('audited_generator',P)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def singleton_rival(x):
    out=[row[:] for row in x]
    for r,row in enumerate(x):
        for c,v in enumerate(row):
            if v==2 and not any(0<=r+dr<len(x) and 0<=c+dc<len(row) and x[r+dr][c+dc]==2 for dr,dc in ((1,0),(-1,0),(0,1),(0,-1))):
                out[r][c]=1
    return out
xs=[g.generate(0,i,difficulty=None) for i in range(4)]
assert json.loads((D/'input.json').read_text())==xs[3]
query=json.loads((D/'racket.json').read_text())
other=json.loads((D/'demos_and_degenerate_racket.json').read_text())
assert query['generator_sha256']==hashlib.sha256(P.read_bytes()).hexdigest()
assert [singleton_rival(x)==other['results'][i]['output'] for i,x in enumerate(xs[:3])]==[True]*3
assert singleton_rival(xs[3])!=query['results'][0]['output']
assert singleton_rival(xs[3])==xs[3]
assert not other['results'][3]['valid_output']
changed=[(r,c) for r,row in enumerate(xs[3]) for c,v in enumerate(row) if v!=query['results'][0]['output'][r][c]]
summary={'seed':0,'difficulty':None,'overrides':{},'demo_indices':[0,1,2],'query_index':3,'generator_sha256':query['generator_sha256'],'executed_rule_hash':query['executed_rule_hash'],'rule_text_sha256':query['rule_text_sha256'],'demo_rival_matches':[True]*3,'query_rival_matches':False,'query_changed_cells':changed,'query_self_check':g.self_check(xs[3]),'no_objects_self_check':g.self_check([[0]*10 for _ in range(10)]),'no_objects_racket_error':other['results'][3]['error']}
(D/'verification.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
