"""Bounded source-bound audit; authoritative outputs are supplied by CLI apply."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('audit_target', REPO / 'generators/4d730bbef8df/generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')

def centers(g):
    return [(r,c) for r in range(1,len(g)-1) for c in range(1,len(g[0])-1)
            if all(g[r+dr][c+dc] == 3 for dr,dc in ((0,0),(-1,0),(1,0),(0,-1),(0,1)))]

def anti_pairs(g):
    cs = centers(g)
    return [[a,b] for i,a in enumerate(cs) for b in cs[i+1:]
            if a[0]-b[0] == -(a[1]-b[1])]

def rival(g):
    """Only join crosses on top-left to bottom-right diagonals (dr = dc)."""
    out = [row[:] for row in g]
    cs = centers(g)
    for i,(r,c) in enumerate(cs):
        for rr,cc in cs[i+1:]:
            if rr-r != cc-c: continue
            sign = 1 if rr>r else -1
            for n in range(1,abs(rr-r)):
                if out[r+n*sign][c+n*sign] == 0: out[r+n*sign][c+n*sign] = 2
    return out

def prepare():
    searched = []
    for seed in range(64):
        grids = [gen.generate(seed, i) for i in range(4)]
        counts = [len(anti_pairs(g)) for g in grids]
        searched.append({'seed':seed, 'sample_indices':list(range(4)), 'anti_diagonal_pair_counts':counts})
        if counts[:3] == [0,0,0] and counts[3]>0:
            break
    else: raise RuntimeError('No witness found in bounded search')
    rule_rows = [json.loads(l) for l in (REPO/'shared/data/canonical/puzzles.jsonl').open() if '4d730bbef8df' in l]
    assert len(rule_rows)==1
    row = rule_rows[0]
    save('reference-rule.json', {'task_id':row['task_id'], 'program_solution':row['program_solution'],
                                'written_solution':row['written_solution']})
    save('source-hashes.json', {
        'generator_path':'repo/generators/4d730bbef8df/generator.py',
        'generator_sha256':hashlib.sha256((REPO/'generators/4d730bbef8df/generator.py').read_bytes()).hexdigest(),
        'canonical_rule_utf8_sha256':hashlib.sha256(row['program_solution'].encode()).hexdigest(),
        'canonical_rule_source':'repo/shared/data/canonical/puzzles.jsonl:4d730bbef8df',
        'retained_rule':'checks/audit/4d730bbef8df/reference-rule.json'})
    save('input.json', grids)
    save('rival.json', [rival(g) for g in grids])
    save('probe-result.json', {'seed':seed, 'sample_indices':list(range(4)), 'difficulty':None,
        'overrides':{}, 'generator_version':gen.VERSION, 'train_indices':[0,1,2], 'query_index':3,
        'centers':[centers(g) for g in grids], 'anti_diagonal_pairs':[anti_pairs(g) for g in grids],
        'self_check_results':[gen.self_check(g) for g in grids], 'search':searched,
        'validation':'Generator self_check only; authoritative CLI apply comparison pending.'})
    print(json.dumps({'seed':seed,'counts':counts,'search_seeds':len(searched),'validator_results':[gen.self_check(g) for g in grids]}))

def compare():
    ref = json.loads((HERE/'racket.json').read_text())
    rs = json.loads((HERE/'rival.json').read_text())
    grids = json.loads((HERE/'input.json').read_text())
    records = []
    for i,(entry,r) in enumerate(zip(ref['results'],rs)):
        out = entry['output']
        diff = [{'row':y,'col':x,'racket':out[y][x],'rival':r[y][x]}
                for y in range(len(out)) for x in range(len(out[0])) if out[y][x]!=r[y][x]]
        records.append({'sample_index':i,'role':'train' if i<3 else 'query',
                        'racket_valid_output':entry['valid_output'],'racket_error':entry['error'],
                        'rival_matches':not diff,'cell_diff':diff})
    episode = json.loads((HERE/'episode.jsonl').read_text())
    actual_pairs = episode['train'] + episode['test']
    same_inputs = [pair['input']==g for pair,g in zip(actual_pairs,grids)]
    same_outputs = [pair['output']==entry['output'] for pair,entry in zip(actual_pairs,ref['results'])]
    assert len(actual_pairs)==4 and all(same_inputs) and all(same_outputs)
    assert all(x['rival_matches'] for x in records[:3]) and not records[3]['rival_matches']
    result = {'finding':'Production 3-demo lesson leaves one diagonal orientation unrefuted',
        'seed':11,'sample_indices':[0,1,2,3],'difficulty':None,'overrides':{},
        'rival':'Connect only top-left to bottom-right diagonal center pairs (dr = dc).',
        'production_generation_exit_code':0, 'production_inputs_match_probe':same_inputs,
        'production_outputs_match_cli_apply':same_outputs,
        'rule_text_sha256':ref['rule_text_sha256'],'executed_rule_hash':ref['executed_rule_hash'],
        'rule_hash_matches_catalog':ref['rule_hash_matches_catalog'],
        'production_sampling':episode.get('sampling'), 'production_rejections':episode.get('rejections'),
        'comparisons':records}
    save('comparison.json', result)
    print(json.dumps({'demo_matches':[x['rival_matches'] for x in records[:3]],
                      'query_cell_diff':records[3]['cell_diff'],'production_same_inputs':same_inputs}))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='compare': compare()
    else: prepare()
