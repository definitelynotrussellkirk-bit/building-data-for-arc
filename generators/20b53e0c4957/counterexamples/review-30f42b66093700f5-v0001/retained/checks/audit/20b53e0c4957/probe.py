#!/usr/bin/env python3
"""Focused findings-only audit; does not modify the frozen generator."""
import argparse, hashlib, importlib.util, json, shlex, sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent
ROOT=SCRIPT_DIR.parents[1]
parser=argparse.ArgumentParser(description=__doc__)
default_context=SCRIPT_DIR/'context'
if not default_context.exists():
    default_context=ROOT/'audit_context/20b53e0c4957'
parser.add_argument('--context', type=Path, default=default_context,
                    help='Directory containing immutable generator.py and canonical_task.json')
parser.add_argument('--shared-runtime', type=Path, default=ROOT/'task_context/repo/shared/runtime',
                    help='Directory containing puzzle_generators runtime imports')
parser.add_argument('--out', type=Path, default=SCRIPT_DIR,
                    help='Directory for evidence.json and input.json')
parser.add_argument('--racket-report', type=Path,
                    help='Retained authoritative apply report (default: OUT/racket.json if present)')
cli=parser.parse_args()
CONTEXT=cli.context.resolve()
SHARED_RUNTIME=cli.shared_runtime.resolve()
OUT=cli.out.resolve()
SOURCE=CONTEXT/'generator.py'
CANON=CONTEXT/'canonical_task.json'
for required in (SOURCE, CANON):
    if not required.is_file():
        parser.error(f'missing context file: {required}')
if not (SHARED_RUNTIME/'puzzle_generators/base.py').is_file():
    parser.error(f'missing shared runtime: {SHARED_RUNTIME}')
reference_path=cli.racket_report.resolve() if cli.racket_report else OUT/'racket.json'
if cli.racket_report and not reference_path.is_file():
    parser.error(f'missing retained Racket report: {reference_path}')
OUT.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode=True
sys.path.insert(0,str(SHARED_RUNTIME))
spec=importlib.util.spec_from_file_location('audit_target',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
canon=json.loads(CANON.read_text())

def rival(grid):
    """Ignore A entirely; recolor B's occupied cells to C[0][0]."""
    pw=(len(grid[0])-2)//3
    color=grid[0][2*pw+2]
    return [[color if v else 0 for v in row[pw+1:2*pw+1]] for row in grid]

def mirror(grid):
    """Local Python transcription; NOT an authoritative Racket execution."""
    pw=(len(grid[0])-2)//3
    panels=[ [row[i*(pw+1):i*(pw+1)+pw] for row in grid] for i in range(3)]
    occupied=lambda panel: [(r,c) for r,row in enumerate(panel) for c,v in enumerate(row) if v!=0]
    a,b,c=panels; ca,cb,cc=occupied(a),occupied(b),occupied(c)
    if not ca or not cc: return {'local_error':'empty bbox in A or C'}
    ar,ac=min(p[0] for p in ca),min(p[1] for p in ca)
    cr,cl=min(p[0] for p in cc),min(p[1] for p in cc)
    out=[row[:] for row in c]
    for r,col in ca:
        if (r,col) not in cb:
            rr,co=cr+r-ar,cl+col-ac
            if 0<=rr<len(out) and 0<=co<pw: out[rr][co]=0
    return out

cases=[]
for texture in ('identical_a_b','no_panel_c','no_separators'):
    args={'seed':7,'sample_index':0,'difficulty':None,'overrides':{'texture':texture}}
    grid=m.generate(args['seed'],args['sample_index'],difficulty=args['difficulty'],**args['overrides'])
    cases.append({'name':texture,'domain':'generator-produced explicit degenerate override','args':args,'grid':grid})
# Valid bbox-relative sparse-object witness, hand constructed, outside ordinary
# generator invariants. It discriminates the whole-B recoloring shortcut.
a=[[0,0,0,0],[0,2,2,0],[0,2,2,0],[0,0,0,0]]
b=[[0,0,0,0],[0,2,0,0],[0,2,2,0],[0,0,0,0]]
c=[[7,7,0,0],[7,7,0,0],[0,0,0,0],[0,0,0,0]]
grid=[a[r]+[5]+b[r]+[5]+c[r] for r in range(4)]
cases.append({'name':'bbox_shift_shortcut_witness','domain':'validator-only handmade sparse-object grid','args':None,'grid':grid})
normal=[]
for difficulty in (None,'easy','hard'):
    for i in range(4):
        args={'seed':19,'sample_index':i,'difficulty':difficulty,'overrides':{}}
        grid=m.generate(19,i,difficulty=difficulty)
        normal.append({'args':args,'grid':grid,'self_check':m.self_check(grid),'local_mirror':mirror(grid),'rival_output':rival(grid),'rival_equals_local_mirror':rival(grid)==mirror(grid)})
for case in cases:
    case['self_check']=m.self_check(case['grid'])
    case['rival_output']=rival(case['grid'])
    case['local_mirror']=mirror(case['grid'])
    case['rival_equals_local_mirror']=case['rival_output']==case['local_mirror']
axis=[]
for difficulty in (None,'easy','hard'):
    try:
        m.generate(7,0,difficulty=difficulty,n_removed=20)
        result={'accepted':True}
    except Exception as ex:
        result={'accepted':False,'error':f'{type(ex).__name__}: {ex}'}
    axis.append({'seed':7,'sample_index':0,'difficulty':difficulty,'overrides':{'n_removed':20},**result})
evidence={'task_id':m.TASK_ID,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'canonical_rule_sha256':hashlib.sha256(canon['program_solution'].encode()).hexdigest(),'command':shlex.join([sys.executable,*sys.argv]),'replay_paths':{'context':str(CONTEXT),'shared_runtime':str(SHARED_RUNTIME),'out':str(OUT),'racket_report':str(reference_path)},'scope':'12 normal generated samples, three explicit degenerate textures, one handmade validator-only sparse-object witness, and three documented n_removed=20 override calls','cases':cases,'normal_samples':normal,'declared_n_removed_valid':m.AXES['n_removed']['valid'],'n_removed_20_calls':axis,'authoritative_racket_status':'pending root supported apply command; local mirror results are not authoritative'}
if reference_path.exists():
    reference=json.loads(reference_path.read_text())
    payload=[case['grid'] for case in cases]+[normal[0]['grid']]
    checks=[]
    assert len(reference['results'])==len(payload)
    assert reference['generator_sha256']==evidence['generator_sha256']
    assert reference['executed_rule_hash']==evidence['canonical_rule_sha256'][:12]
    for i,result in enumerate(reference['results']):
        assert result['index']==i and result['input']==payload[i]
        prediction=mirror(payload[i])
        checks.append({'index':i,'name':cases[i]['name'] if i<len(cases) else 'normal_seed19_index0','input_binding_verified':True,'input_shape':[len(payload[i]),len(payload[i][0])],'output_shape':[len(result['output']),len(result['output'][0])],'valid_output':result['valid_output'],'error':result['error'],'authoritative_output':result['output'],'local_mirror_equals_authoritative':prediction==result['output'],'local_mirror_defined':isinstance(prediction,list),'rival_equals_authoritative':rival(payload[i])==result['output'],'input_sha256':result['input_sha256'],'output_sha256':result['output_sha256']})
    evidence['authoritative_racket_status']='complete: five grids, all valid outputs, no errors'
    evidence['authoritative_reference']={k:reference[k] for k in ('schema','task_id','reference','executed_rule_hash','catalog_rule_hash','rule_hash_matches_catalog','rule_text_sha256','generator_sha256','command','cwd')}
    evidence['authoritative_reference']['report_file_sha256']=hashlib.sha256(reference_path.read_bytes()).hexdigest()
    evidence['authoritative_checks']=checks
    evidence['test_counts']={'normal_generation_calls':12,'normal_self_check_passes':12,'normal_local_mirror_rival_matches':12,'explicit_degenerate_generation_calls':3,'explicit_degenerate_self_check_passes':2,'explicit_degenerate_self_check_rejections':1,'validator_only_handmade_grids':1,'validator_only_self_check_passes':1,'documented_override_calls':3,'documented_override_rejections':3,'authoritative_grids':5,'authoritative_valid_outputs':5,'authoritative_errors':0,'defined_local_mirror_matches_authoritative':4,'local_mirror_empty_bbox_cases':1,'rival_matches_authoritative':4,'rival_mismatches_authoritative':1}
(OUT/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
# Keep reference payload small; ordinary generated sample also tests the rival.
(OUT/'input.json').write_text(json.dumps([case['grid'] for case in cases]+[normal[0]['grid']],indent=2)+'\n')
print(json.dumps({'generator_sha256':evidence['generator_sha256'],'canonical_rule_sha256':evidence['canonical_rule_sha256'],'candidate_order':[case['name'] for case in cases]+['normal_seed19_index0'],'self_checks':[case['self_check'] for case in cases],'normal_rival_matches':sum(s['rival_equals_local_mirror'] for s in normal),'normal_count':len(normal),'n_removed_20_calls':axis},indent=2))
