from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'repo'
PATH=REPO/'generators/c64bcbdda754/generator.py'
spec=importlib.util.spec_from_file_location('audit_c64',PATH)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

bands=(None,'easy','medium','hard')
active_rows=repeat_rows=grids=0
examples=[]
for bi,band in enumerate(bands):
    for i in range(150):
        g=gen.generate(10000+bi*1000+i, i*17+3, difficulty=band)
        grids+=1
        assert not gen.self_check(g), (band,i,gen.self_check(g))
        for r,row in enumerate(g):
            vals=[v for v in row if v]
            if not vals: continue
            active_rows+=1
            if len(vals)!=len(set(vals)):
                repeat_rows+=1
                if len(examples)<5: examples.append({'band':band,'i':i,'row':r,'values':vals})

counterexample=[
 [0,2,0,2,3,0,0,0],
 [0,0,4,0,4,4,0,0],
 [0,0,0,0,0,0,0,0],
 [7,0,7,8,0,0,0,0],
 [0,0,0,0,0,0,0,0],
]
report={
 'schema':'c64bcbdda754-audit-probe-v1',
 'source_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),
 'sample':{'grids':grids,'active_rows':active_rows,'rows_with_repeated_nonzero':repeat_rows,'examples':examples},
 'counterexample':counterexample,
 'counterexample_self_check':gen.self_check(counterexample),
}
(Path(__file__).parent/'support_probe.json').write_text(json.dumps(report,indent=2)+'\n')
(Path(__file__).parent/'counterexample_input.json').write_text(json.dumps({'input':counterexample},indent=2)+'\n')
print(json.dumps(report,indent=2))
