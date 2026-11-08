from __future__ import annotations
import hashlib,json
from pathlib import Path
from reviewer_support import load_selected_generator,canonical_pairs,canonical_path
OUT=Path(__file__).resolve().parent
WORK=OUT.parents[2]
ROOT=WORK/'repo'
TASK='8a34b3906f3a'
GEN,SOURCE,SOURCE_HASH=load_selected_generator(TASK,root=ROOT)
def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def sha_grid(grid):
    return hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()
def transform(grid,*,geometric=False):
    output=[row[:] for row in grid]
    height,width=len(grid),len(grid[0])
    twice_center=height-1 if geometric else 2*(height//2)
    clipped=[]
    for row,cells in enumerate(grid):
        for col,value in enumerate(cells):
            if value!=2:continue
            rr,cc=row,col
            for turn in range(1,4):
                rr,cc=cc,twice_center-rr
                if 0<=rr<height and 0<=cc<width: output[rr][cc]=2
                else:clipped.append({'source':[row,col],'turn':turn,'destination':[rr,cc]})
    return output,clipped
pairs=canonical_pairs(TASK,root=ROOT)
canonical=[]
for pair in pairs:
    canonical.append({'variant':pair['variant'],'split':pair['split'],'pair_index':pair['pair_index'],
        'shape':[len(pair['input']),len(pair['input'][0])],
        'self_check':GEN.self_check(pair['input']),
        'python_rule_matches_known_output':transform(pair['input'])[0]==pair['output'],
        'geometric_center_rival_matches_known_output':transform(pair['input'],geometric=True)[0]==pair['output']})
rule_codes=[]
with canonical_path(ROOT).open() as stream:
    for line in stream:
        row=json.loads(line)
        if row.get('task_id')==TASK:rule_codes.append(row['program_solution'])
rule_hashes=[hashlib.sha256(' '.join(c.split()).encode()).hexdigest()[:12] for c in rule_codes]
counts={'generated_cases':0,'even_boards':0,'clipped_cases':0,'identity_outputs':0,'self_check_rejections':0}
clipped_calls=[]
for seed in range(256):
    grid=GEN.generate(seed,0,difficulty='medium')
    output,clipped=transform(grid)
    counts['generated_cases']+=1
    counts['even_boards']+=len(grid)%2==0
    counts['clipped_cases']+=bool(clipped)
    counts['identity_outputs']+=output==grid
    counts['self_check_rejections']+=bool(GEN.self_check(grid))
    if clipped:clipped_calls.append({'seed':seed,'sample_index':0,'difficulty':'medium','shape':[len(grid),len(grid[0])],'clipped_rotations':len(clipped)})
call={'seed':8,'sample_index':0,'difficulty':'medium','overrides':{}}
grid=GEN.generate(call['seed'],call['sample_index'],difficulty=call['difficulty'])
intended,clipped=transform(grid)
rival,_=transform(grid,geometric=True)
write('input.json',grid)
write('python-intended-output.json',intended)
write('rival-output.json',rival)
differing=[[r,c] for r in range(len(grid)) for c in range(len(grid[0])) if intended[r][c]!=rival[r][c]]
base=GEN.generate(0,0,difficulty='medium')
width_override=GEN.generate(0,0,difficulty='medium',grid_w=14)
unknown_override=GEN.generate(0,0,difficulty='medium',unknown_axis=123)
all_red=[[2]*9 for _ in range(9)]
report={'schema':'arcpuzzles-audit-python-probe-v1','task_id':TASK,
    'generator_sha256':SOURCE_HASH,'canonical_rule_hashes':rule_hashes,
    'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'execution_scope':'Pure Python only; selected generator via public load_selected_generator, canonical pairs via public canonical_pairs, rule text streamed by exact task ID from canonical_path. No pytest/Racket execution.',
    'canonical_checks':canonical,'declared_contract':{name:getattr(GEN,name,None) for name in ['RULE_HASH','EXAMPLES_NEEDED','SEMANTIC_RIVALS','LESSON_COMPETITORS','SEMANTIC_WITNESSES']},
    'bounded_probe':{'seed_start':0,'seed_stop_exclusive':256,'sample_index':0,'difficulty':'medium',**counts,'clipped_calls':clipped_calls},
    'witness':{'generate_call':call,'self_check':GEN.self_check(grid),'shape':[len(grid),len(grid[0])],
        'input_sha256':sha_grid(grid),'input_color_2_cells':[[r,c] for r,row in enumerate(grid) for c,v in enumerate(row) if v==2],
        'integer_center':[len(grid)//2,len(grid)//2],'geometric_center':[(len(grid)-1)/2,(len(grid)-1)/2],
        'clipped_rotations':clipped,'python_intended_color_2_cells':sum(v==2 for row in intended for v in row),
        'geometric_rival_color_2_cells':sum(v==2 for row in rival for v in row),
        'differing_cells':differing,'rival_name':'auditor-proposed geometric-center quarter-turn completion',
        'rival_is_generator_declared':False,'racket_confirmation':'pending','input_path':'input.json','python_intended_path':'python-intended-output.json','rival_path':'rival-output.json'},
    'override_witness':{'generate_call':{'seed':0,'sample_index':0,'difficulty':'medium','overrides':{'grid_w':14}},
        'declared_width_valid_range':GEN.AXES['grid_w']['valid'],'actual_shape':[len(width_override),len(width_override[0])],
        'identical_to_omission':width_override==base,'self_check':GEN.self_check(width_override),
        'unknown_override_also_identical':unknown_override==base},
    'validator_witness':{'construction':'9 rows, each containing 9 literal integers equal to 2',
        'self_check':GEN.self_check(all_red),'violated_declared_invariants':['background is 0','3-4 connected motifs in distinct non-zero colors at distinct positions']},
    'limitations':['The 256-case sample does not establish a population frequency.','No reference runtime was run by this probe; final confirmation is a separate public apply receipt.','The geometric-center rule is an auditor-proposed canonical-fitting rival, not an existing declaration.','No production or audit-target source was changed.']}
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_HASH,'Audit target changed during probe'
write('python-report.json',report)
print(json.dumps({'generator_sha256':SOURCE_HASH,'rule_hashes':rule_hashes,'canonical_pairs':len(canonical),'canonical_python_matches':sum(x['python_rule_matches_known_output'] for x in canonical),'canonical_rival_matches':sum(x['geometric_center_rival_matches_known_output'] for x in canonical),'bounded_counts':counts,'witness':report['witness'],'override_witness':report['override_witness'],'validator_witness':report['validator_witness']},indent=2))
