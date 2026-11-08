from __future__ import annotations
import collections, hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]/'repo'
sys.path.insert(0,str(ROOT/'shared/runtime'))
DEST=Path(__file__).resolve().parent
p=ROOT/'generators/331074b4dcbc/generator.py'
spec=importlib.util.spec_from_file_location('audit_target',p); gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
def rival(grid):
    # Rival: effective tile period is five minus cyan rectangle height.
    seed=[]
    for v in grid[0]:
        if v==0: break
        seed.append(v)
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if r>0 and v==8]
    t=min(r for r,c in cells); b=max(r for r,c in cells); l=min(c for r,c in cells); rr=max(c for r,c in cells)
    period=5-(b-t+1)
    tile=[seed[i%len(seed)] for i in range(period)]
    out=[row[:] for row in grid]
    for r in range(t,b+1):
        for c in range(l,rr+1): out[r][c]=tile[(c-l)%period]
    return out
records=[]; pairs=[]; counts=collections.Counter(); provenance=[]
for band in (None,'easy','medium','hard'):
    for pi,profile in enumerate(gen.SCENE_PROFILES):
        for j in range(20):
            seed=331074+j; index=pi*100+j
            g=gen.generate(seed,index,difficulty=band,scene_profile=profile)
            facts=gen._analysis(g)['facts']; out=gen.rule_mirror(g)
            assert not gen.self_check(g,difficulty=band,meta={'overrides':{'scene_profile':profile}})
            assert not gen.strict_canonical_like(g)
            assert gen.observe_overrides(g)=={'scene_profile':profile}
            assert len(facts['seed'])+facts['rect'][2]==5
            assert rival(g)==out
            counts['targeted']+=1
            if band is None and j==0:
                pairs.append(g); provenance.append({'kind':'generated','seed':seed,'sample_index':index,'difficulty':band,'overrides':{'scene_profile':profile}})
    for j in range(100):
        g=gen.generate(331074+j,j,difficulty=band)
        assert rival(g)==gen.rule_mirror(g)
        counts['default']+=1
canonfile=ROOT/'shared/data/canonical/puzzles.jsonl'
row=next(json.loads(line) for line in canonfile.open() if json.loads(line).get('task_id')=='331074b4dcbc')
for split in ('train','test'):
    for index,pair in enumerate(row[split]):
        conv=lambda a:[[int(v) for v in r] for r in a]
        g=conv(pair['input']); out=conv(pair['output'])
        assert gen.self_check(g)==[] and gen.strict_canonical_like(g)==[]
        assert gen.rule_mirror(g)==out and rival(g)!=out
        counts['canonical_rival_failures']+=1
        pairs.append(g); provenance.append({'kind':'canonical','split':split,'pair_index':index,'seed':None,'sample_index':None,'difficulty':None,'overrides':None})
        records.append({'split':split,'pair_index':index,'input':g,'expected':out,'rival':rival(g),'self_check':gen.self_check(g),'strict':gen.strict_canonical_like(g)})
(DEST/'input.json').write_text(json.dumps({'inputs':pairs},indent=2)+'\n')
(DEST/'rival_outputs.json').write_text(json.dumps([rival(g) for g in pairs],indent=2)+'\n')
(DEST/'canonical_counterexamples.json').write_text(json.dumps(records,indent=2)+'\n')
(DEST/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
receipt={'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'canonical_sha256':hashlib.sha256(canonfile.read_bytes()).hexdigest(),'counts':dict(counts),'proof':'Each of all eight _PROFILE_SPECS has seed_len + rect_height = 5; rival therefore reproduces every generated output for every palette, seed, index and band. Canonical examples instead have seed_len == rect_height.','selected_official_apply_inputs':len(pairs)}
(DEST/'probe.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
