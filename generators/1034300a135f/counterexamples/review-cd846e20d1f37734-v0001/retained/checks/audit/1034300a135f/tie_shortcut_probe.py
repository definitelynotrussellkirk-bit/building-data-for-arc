from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'repo' / 'shared' / 'runtime'))
PATH = ROOT / 'repo' / 'generators' / '1034300a135f' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_1034300a135f', PATH)
mod = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)

def reverse_tie_rival(grid):
    facts=mod._extract_facts(grid)
    ordered=sorted(facts['markers'], key=lambda m:(m['distance'],-m['row'],-m['col']))
    seq=[m['color'] for m in ordered]
    h,w=facts['height'],facts['width']; bg=facts['background']
    return [[seq[d] if d < len(seq) else bg for c in range(w)
             for d in [mod._edge_distance(r,c,h,w)]] for r in range(h)]

def pair(seed,index,band):
    g=mod.generate(seed,index,difficulty=band)
    return {'input':g,'output':mod.rule_mirror(g),'profile':mod.observe_overrides(g).get('scene_profile')}

examples=[]; census={}
for band in ('easy','medium','hard'):
    ambiguous=0
    first=None
    for lesson in range(300):
        seed=700000 + lesson
        start=lesson*11
        rows=[pair(seed,start+i,band) for i in range(4)]
        fits=all(reverse_tie_rival(row['input'])==row['output'] for row in rows[:3])
        differs=reverse_tie_rival(rows[3]['input'])!=rows[3]['output']
        if fits and differs:
            ambiguous+=1
            if first is None:
                first={'band':band,'seed':seed,'start_sample_index':start,
                       'profiles':[r['profile'] for r in rows],
                       'demos':rows[:3], 'query':rows[3],
                       'rival_query_output':reverse_tie_rival(rows[3]['input'])}
    census[band]={'lessons':300,'reverse_tie_rival_fits_demos_but_misses_query':ambiguous}
    if first: examples.append(first)

out={
 'task_id':mod.TASK_ID,
 'generator_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),
 'prior_return_used_as_lead':'review-b4a044e31c5fa03e:v0001',
 'rival':'sort by edge distance but reverse row-major order within equal-distance ties',
 'lesson_policy':'seed=700000+lesson; start_sample_index=lesson*11; 3 consecutive demos then 1 query',
 'census':census,
 'first_examples':examples,
 'semantic_hooks':{
   'strict_canonical_like':hasattr(mod,'strict_canonical_like'),
   'SEMANTIC_WITNESSES':hasattr(mod,'SEMANTIC_WITNESSES'),
   'lesson_identifiable':hasattr(mod,'lesson_identifiable'),
   'LESSON_COMPETITORS':hasattr(mod,'LESSON_COMPETITORS'),
 },
}
(Path(__file__).with_name('probe.json')).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if examples:
    (Path(__file__).with_name('input.json')).write_text(json.dumps([e['query']['input'] for e in examples],indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='first_examples'},indent=2,sort_keys=True))
print('examples',len(examples), [e['profiles'] for e in examples])
