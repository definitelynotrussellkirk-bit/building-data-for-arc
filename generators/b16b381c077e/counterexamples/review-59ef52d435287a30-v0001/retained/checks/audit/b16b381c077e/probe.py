"""Focused source-bound audit. No shared/private runners or solve artifacts."""
from pathlib import Path
import sys,json,hashlib,importlib.util,collections
ROOT=Path(__file__).resolve().parents[3]/'repo'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'shared/runtime'))
from reviewer_support import canonical_pairs,canonical_path
spec=importlib.util.spec_from_file_location('audited_generator',ROOT/'generators/b16b381c077e/generator.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
rows=[json.loads(s) for s in canonical_path(ROOT).read_text().splitlines() if json.loads(s).get('task_id')==g.TASK_ID]
pairs=canonical_pairs(g.TASK_ID,root=ROOT)
rule=rows[0]['program_solution']
sha=lambda b:hashlib.sha256(b).hexdigest()
palette=lambda p:sorted(set(v for row in p for v in row)-{0})
def panels(grid):
    n=len(grid)
    return [[row[k*(n+1):k*(n+1)+n] for row in grid] for k in range(3)]
def d8(panel,kind):
    p=[list(row) for row in panel]
    if kind=='id':return p
    if kind=='rot90':return [list(row) for row in zip(*p[::-1])]
    if kind=='rot180':return [row[::-1] for row in p[::-1]]
    if kind=='rot270':return [list(row) for row in zip(*p)][::-1]
    if kind=='flip_h':return [row[::-1] for row in p]
    if kind=='flip_v':return p[::-1]
    if kind=='transpose':return [list(row) for row in zip(*p)]
    if kind=='anti_transpose':return [list(row)[::-1] for row in zip(*p)][::-1]
    raise ValueError(kind)
KINDS=('id','rot90','rot180','rot270','flip_h','flip_v','transpose','anti_transpose')
def matching(a,b):return [kind for kind in KINDS if d8(a,kind)==b]
def expected(grid):
    a,b,c=panels(grid)
    return d8(c,matching(a,b)[0])
def rival(grid):
    a,b,c=panels(grid)
    mask=lambda p:[[int(v!=0) for v in row] for row in p]
    kinds=matching(mask(a),mask(b))
    return d8(c,kinds[0])
inputs=[];records=[]
def retain(grid,**meta):
    ix=len(inputs);inputs.append(grid)
    f=g._analyze(grid)['facts']
    records.append({'index':ix,**meta,'validator':g.self_check(grid),'inferred_kind':f['kind'],'matching_kinds':f['matching_kinds'],'palette_A':palette(f['panel_a']),'palette_C':palette(f['panel_c']),'python_transform_output':expected(grid),'color_blind_rival_output':rival(grid)})
for p in pairs:
    retain(p['input'],origin='canonical',variant=p['variant'],split=p['split'],pair_index=p['pair_index'],canonical_output=p['output'])
seed=160999
stats={};first_rival=None
for band in ('easy','medium','hard'):
    counts=collections.Counter();kinds=collections.Counter();overlap=0;failures=[];rival_disagreements=0
    for index in range(200):
        grid=g.generate(seed,index,difficulty=band)
        f=g._analyze(grid)['facts'];errors=g.self_check(grid,difficulty=band)
        counts[len(grid)]+=1;kinds[f['kind']]+=1
        overlap+=bool(set(palette(f['panel_a']))&set(palette(f['panel_c'])))
        if errors:failures.append({'sample_index':index,'errors':errors})
        if rival(grid)!=expected(grid):
            rival_disagreements+=1
            if first_rival is None:first_rival=(grid,band,index)
        if index<7:retain(grid,origin='ordinary',seed=seed,sample_index=index,difficulty=band,overrides={})
    stats[band]={'draws':200,'panel_sizes':dict(counts),'kinds':dict(kinds),'shared_A_C_color':overlap,'canonical_panel_size_hits':sum(counts[n] for n in (3,4)),'validator_failures':failures,'color_blind_rival_disagreements':rival_disagreements}
# Joint exact axes: all seven transformations at all four supported sizes.
for panel in (3,4,5,6):
    for index,kind in enumerate(g._TRANSFORM_KINDS):
        retain(g.generate(271828,index,difficulty='hard',panel=panel,kind=kind,divider_color=9),origin='boundary',seed=271828,sample_index=index,difficulty='hard',overrides={'panel':panel,'kind':kind,'divider_color':9})
retain(g.generate(seed,0,difficulty='extreme'),origin='invalid_difficulty',seed=seed,sample_index=0,difficulty='extreme',overrides={})
if first_rival:
    grid,band,index=first_rival
    retain(grid,origin='color_blind_rival_witness',seed=seed,sample_index=index,difficulty=band,overrides={})
# Lawful reference input, deliberately outside the claimed generator size domain.
a=[[1,2],[0,0]];c=[[0,3],[4,0]]
retain(g._assemble((a,g._rot90(a),c),5),origin='reference_lawful_outside_generated_domain',construction={'panel':2,'kind':'rot90','divider_color':5,'A':a,'C':c})
result={'schema':'focused-audit-v1','task_id':g.TASK_ID,'source_sha256':sha((ROOT/'generators/b16b381c077e/generator.py').read_bytes()),'version':g.VERSION,'rule_sha256_utf8':sha(rule.encode()),'rule_sha256_whitespace_normalized':sha(' '.join(rule.split()).encode()),'declared_rule_hash':g.RULE_HASH,'canonical_row_sha256_sorted_json':sha(json.dumps(rows[0],sort_keys=True,separators=(',',':')).encode()),'canonical_pairs':len(pairs),'canonical_A_C_color_disjoint':sum(not(set(palette(panels(p['input'])[0]))&set(palette(panels(p['input'])[2]))) for p in pairs),'canonical_color_blind_rival_fits':sum(rival(p['input'])==p['output'] for p in pairs),'probe_seed':seed,'ordinary_samples_per_band':[0,199],'ordinary_stats':stats,'reference_batch_count':len(inputs),'records':records}
for name,obj in [('canonical_row.json',rows[0]),('input.json',{'inputs':inputs}),('probe.json',result)]:
    (OUT/name).write_text(json.dumps(obj,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('source_sha256','rule_sha256_utf8','rule_sha256_whitespace_normalized','canonical_A_C_color_disjoint','canonical_color_blind_rival_fits','ordinary_stats','reference_batch_count')},indent=2))
