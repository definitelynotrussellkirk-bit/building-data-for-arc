from pathlib import Path
import importlib.util,sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'repo/shared/runtime'))
spec=importlib.util.spec_from_file_location('audit_target',ROOT/'repo/generators/5f9a2df57599/generator.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def rival(g):
    out=[r[:] for r in g]
    for cells in m._zero_components(g):
        rows=[r for r,c in cells]; cols=[c for r,c in cells]
        if max(rows)-min(rows)<4 and max(cols)-min(cols)<4 and min(rows)>0 and max(rows)<len(g)-1 and not (min(cols)==max(cols)==0 and max(rows)>min(rows)):
            for r,c in cells:out[r][c]=4
    return out
records=[];cases=[]
for d in ['easy','medium','hard']:
 for seed in range(100):
    index=17*seed+1
    try:
        g=m.generate(seed,index,difficulty=d)
        a=m._analysis(g)
        records.append(dict(seed=seed,sample_index=index,difficulty=d,profile=a['scene_profile'],validator=a['errors'],rival_matches_mirror=rival(g)==m.rule_mirror(g),small_rejected=[f for f in a['facts']['rejected'] if f['size']<=16 and not f['excluded_left_vertical']],gray_top=all(v==5 for v in g[0])))
    except Exception as e:records.append(dict(seed=seed,sample_index=index,difficulty=d,exception=repr(e)))
# Compact wrong-wall L + eligible one-cell region; gray remains one connected network.
g=[[5]*8 for _ in range(8)]
for r,c in [(1,1),(1,2),(2,1),(3,2)]:g[r][c]=0
(ROOT/'checks/audit/5f9a2df57599/compact_input.json').write_text(json.dumps(g))
(ROOT/'checks/audit/5f9a2df57599/census.json').write_text(json.dumps(records,indent=2))
parity_inputs=[]; parity_meta=[]
for d in ['easy','medium','hard']:
 for profile in m.GENERAL_PROFILES:
  for seed in [700,701]:
   index=17*seed+1; grid=m.generate(seed,index,difficulty=d,scene_profile=profile)
   parity_inputs.append(grid); parity_meta.append(dict(seed=seed,sample_index=index,difficulty=d,overrides=dict(scene_profile=profile),validator=m.self_check(grid),rival_output=rival(grid),mirror_output=m.rule_mirror(grid)))
for profile in m.PUBLIC_PROFILES:
 grid=m.generate(700,11901,scene_profile=profile)
 parity_inputs.append(grid); parity_meta.append(dict(seed=700,sample_index=11901,difficulty=None,overrides=dict(scene_profile=profile),validator=m.self_check(grid),rival_output=rival(grid),mirror_output=m.rule_mirror(grid)))
(ROOT/'checks/audit/5f9a2df57599/parity_input.json').write_text(json.dumps(parity_inputs))
(ROOT/'checks/audit/5f9a2df57599/parity_metadata.json').write_text(json.dumps(parity_meta,indent=2))
print(json.dumps({'records':len(records),'exceptions':sum('exception' in x for x in records),'rival_matches_mirror':sum(x.get('rival_matches_mirror',False) for x in records),'compact_validator':m.self_check(g),'compact_profile':m.observe_overrides(g),'small_rejected_examples':[(x['difficulty'],x['seed'],x['profile']) for x in records if x.get('small_rejected')][:15]},indent=2))
