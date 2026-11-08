"""Bounded read-only source audit; output only to this task's audit directory."""
from pathlib import Path
from collections import Counter
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[3] / 'repo'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import canonical_pairs, load_selected_generator
m, source, digest = load_selected_generator('50b436f101bb', root=ROOT)
def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n')
def shortcut(g):
    counts = Counter(v for row in g for v in row)
    bg = counts.most_common(1)[0][0]
    color = max((v for v in counts if v != bg), key=counts.get)
    cells = [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == color]
    t,b=min(r for r,c in cells),max(r for r,c in cells)
    l,r=min(c for r,c in cells),max(c for r,c in cells)
    return [[color if g[i][j]==color else bg for j in range(l+2,r-1)] for i in range(t+2,b-1)]
def clustered(g):
    counts=Counter(v for row in g for v in row);bg=counts.most_common(1)[0][0]
    rest={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg}; objects=[]
    while rest:
        seed=min(rest);rest.remove(seed);obj={seed};queue=[seed]
        while queue:
            r,c=queue.pop();near={p for p in rest if abs(p[0]-r)<=2 and abs(p[1]-c)<=2}
            rest-=near;obj|=near;queue.extend(near)
        if len({g[r][c] for r,c in obj})==1:objects.append(obj)
    obj=max(objects,key=len); color=g[next(iter(obj))[0]][next(iter(obj))[1]]
    t,b=min(r for r,c in obj),max(r for r,c in obj);l,r=min(c for r,c in obj),max(c for r,c in obj)
    return [[color if g[i][j]==color else bg for j in range(l+2,r-1)] for i in range(t+2,b-1)]
pairs=canonical_pairs('50b436f101bb',root=ROOT)
canonical=[]
for p in pairs:
    rival=shortcut(p['input'])
    canonical.append({**{k:p[k] for k in ('variant','split','pair_index')},'rival_matches_label':rival==p['output'],'rival_output':rival,'label':p['output']})
witness=next(p for p in pairs if shortcut(p['input'])!=p['output'])
generated=[]
for index in range(64):
    g=m.generate(17,index)
    generated.append({'seed':17,'sample_index':index,'overrides':{},'self_check':m.self_check(g),'shortcut_equals_python_rule_translation':shortcut(g)==clustered(g)})
g=m.generate(17,0)
bar=[[0]*15 for _ in range(15)]
for r in range(3):
    for c in range(7):bar[r+2][c+2]=2
write('input.json',{'inputs':[g,witness['input'],bar]})
write('rival.json',{'outputs':[shortcut(g),shortcut(witness['input']),shortcut(bar)]})
write('expected-canonical.json',witness['output'])
write('probes.json',{'source_path':str(source.relative_to(ROOT)),'source_sha256':digest,'review_index_exists':(source.parent/'evidence/review_index.json').exists(),'canonical':canonical,'generated':generated,'input_order':['generated seed=17 sample_index=0 overrides={}',['canonical',witness['variant'],witness['split'],witness['pair_index']],'handcrafted 15x15, background=0, 3x7 solid color2 at (2,2), 21 non-background cells'],'bar_self_check':m.self_check(bar),'rect_size_override_probe':{'seed':17,'sample_index':0,'overrides':[{'rect_size':7},{'rect_size':11}],'identical_grids':m.generate(17,0,rect_size=7)==m.generate(17,0,rect_size=11)},'texture_probe':{'seed':17,'sample_index':0,'overrides':[{'texture':'s7'},{'texture':'s11'}],'identical_grids':m.generate(17,0,texture='s7')==m.generate(17,0,texture='s11')}})
print(json.dumps({'generated_checked':len(generated),'generated_shortcut_matches':sum(x['shortcut_equals_python_rule_translation'] for x in generated),'canonical_shortcut_matches':sum(x['rival_matches_label'] for x in canonical),'canonical_count':len(canonical),'canonical_witness':[witness['variant'],witness['split'],witness['pair_index']],'bar_self_check':m.self_check(bar)}))
