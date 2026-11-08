from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import canonical_pairs

TASK='545f743375cd'
root=Path(__file__).resolve().parents[3] / 'repo'
path=root/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_545',path)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

def branch_shortcut(grid):
    """Correct except it invents one orange cell when translation is all-out."""
    out=gen.rule_mirror(grid)
    if out == grid:
        out=[row[:] for row in out]
        for r,row in enumerate(out):
            for c,value in enumerate(row):
                if value == 0:
                    out[r][c]=7
                    return out
    return out

canonical=[]
for pair in canonical_pairs(TASK,root=root,labeled_only=True):
    facts=gen.semantic_observables(pair['input'])
    rival=branch_shortcut(pair['input'])
    canonical.append({
        'split':pair['split'],'pair_index':pair['pair_index'],
        'clip_profile':facts.get('clip_profile'),
        'in_bounds_target_count':facts.get('in_bounds_target_count'),
        'mirror_matches_label':gen.rule_mirror(pair['input']) == pair['output'],
        'shortcut_matches_label':rival == pair['output'],
        'input':pair['input'],'expected_output':pair['output'],'shortcut_output':rival,
    })

generated=[]
for band in ('easy','medium','hard'):
    for seed in range(30):
        for index in range(8):
            grid=gen.generate(seed,index,difficulty=band)
            facts=gen.semantic_observables(grid)
            generated.append({
                'band':band,'seed':seed,'sample_index':index,
                'clip_profile':facts.get('clip_profile'),
                'in_bounds_target_count':facts.get('in_bounds_target_count'),
                'shortcut_matches_mirror':branch_shortcut(grid)==gen.rule_mirror(grid),
            })
summary={
    'schema':'audit-probe-v1','task_id':TASK,
    'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'declared_clip_domain':gen.AXES['clip_profile']['valid'],
    'canonical_clip_counts':{p:sum(row['clip_profile']==p for row in canonical) for p in ('full','partial','all_out')},
    'generated_draws':len(generated),
    'generated_unique_inputs':len({json.dumps(gen.generate(row['seed'],row['sample_index'],difficulty=row['band'])) for row in generated}),
    'generated_clip_counts':{p:sum(row['clip_profile']==p for row in generated) for p in ('full','partial','all_out')},
    'shortcut_generated_matches':sum(row['shortcut_matches_mirror'] for row in generated),
    'shortcut_canonical_matches':sum(row['shortcut_matches_label'] for row in canonical),
    'canonical_pairs':canonical,
    'all_out_counterexample': (lambda row: {
        'passes_self_check': not bool(gen.self_check(row['input'])),
        'self_check_errors': gen.self_check(row['input']),
        'passes_strict_canonical_like': not bool(gen.strict_canonical_like(row['input'])),
        'strict_canonical_like_errors': gen.strict_canonical_like(row['input']),
        'belongs_declared_generated_clip_domain': row['clip_profile'] in str(gen.AXES['clip_profile']['valid']).split('|'),
        'clip_profile': row['clip_profile'],
        'canonical_split': row['split'],
        'canonical_pair_index': row['pair_index'],
    })(next(row for row in canonical if row['clip_profile'] == 'all_out')),
}
print(json.dumps(summary,indent=2))
