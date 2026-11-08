"""Findings-only source-bound e2bc audit. No task source writes."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['prepare', 'verify'])
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
repo, outdir = args.repo.resolve(), args.out.resolve()
outdir.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(repo / 'shared/runtime'))
source = repo / 'generators/e2bc70324918/generator.py'
spec = importlib.util.spec_from_file_location('audited_e2bc', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def save(name, value):
    (outdir / name).write_text(json.dumps(value, separators=(',', ':')) + '\n')

def endpoints(cells):
    cells = set(cells)
    return sorted((r,c) for r,c in cells
                  if sum((r+dr,c+dc) in cells for dr in (-1,0,1) for dc in (-1,0,1)
                         if dr or dc) == 1)

def roles(grid):
    objects = gen._components8(grid, 7)
    line_color, line = next((c,cs) for c,cs in objects if len(cs)>1 and len(endpoints(cs))==2)
    stamp_color = next(c for c,cs in objects if c != line_color)
    stamps = [cs for c,cs in objects if c == stamp_color]
    return line_color, line, stamp_color, stamps

def draw_line(g, a, b, color):
    r,c = a
    r2,c2 = b
    dr,dc = abs(r2-r),abs(c2-c)
    sr,sc = (1 if r<r2 else -1),(1 if c<c2 else -1)
    err = dr-dc
    while True:
        g[r][c] = color
        if (r,c) == (r2,c2):
            return
        twice = 2*err
        if twice > -dc:
            err -= dc
            r += sr
        if twice < dr:
            err += dr
            c += sc

def fixed_stencil_rival(grid):
    """Wrong rule: select single or plus stencil instead of copying glyph shape."""
    lc,line,sc,stamps = roles(grid)
    g = [[7]*len(grid[0]) for _ in grid]
    centers = [((min(r for r,c in cs)+max(r for r,c in cs))//2,
                (min(c for r,c in cs)+max(c for r,c in cs))//2) for cs in stamps]
    for i,a in enumerate(centers):
        for b in centers[i+1:]:
            draw_line(g,a,b,lc)
    offsets = [(0,0)] if len(stamps[0]) == 1 else [(0,0),(-1,0),(1,0),(0,-1),(0,1)]
    for r,c in endpoints(line):
        for dr,dc in offsets:
            if 0 <= r+dr < len(g) and 0 <= c+dc < len(g[0]):
                g[r+dr][c+dc] = sc
    return g

def observe(grid):
    lc,line,sc,stamps = roles(grid)
    ep = endpoints(line)
    dr,dc = ep[1][0]-ep[0][0],ep[1][1]-ep[0][1]
    orientation = 'horizontal' if dr == 0 else 'vertical' if dc == 0 else 'diagonal' if dc>0 else 'anti-diagonal'
    shape = gen._norm(stamps[0])
    cr = max(r for r,c in shape)//2
    cc = max(c for r,c in shape)//2
    missing = [(r+pr-cr,c+pc-cc) for r,c in ep for pr,pc in shape
               if not (0 <= r+pr-cr < len(grid) and 0 <= c+pc-cc < len(grid[0]))]
    return {'line_color':lc,'stamp_color':sc,'n_glyphs':len(stamps),
            'glyph_shape':shape,'line_endpoints':ep,'line_orientation':orientation,
            'out_of_bounds_endpoint_stamp_cells':missing}

if args.mode == 'prepare':
    canonical = [json.loads(line) for line in (repo/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
                 if json.loads(line)['task_id'] == gen.TASK_ID]
    assert len(canonical) == 2
    rules = {row['program_solution'] for row in canonical}
    assert len(rules) == 1
    rule = rules.pop()
    identity = {'task_id':gen.TASK_ID,'generator_version':gen.VERSION,
                'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'canonical_rule_hash':hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12],
                'raw_canonical_rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),
                'canonical_sources':[row['source'] for row in canonical]}
    records=[]
    for band in ['easy','medium','hard']:
        for seed in range(8):
            records.append({'kind':'default_generated','seed':seed,'sample_index':seed,
                            'difficulty':band,'overrides':{},'input':gen.generate(seed,seed,difficulty=band)})
    for overrides in [{},{'line_orientation':'horizontal'},{'line_orientation':'vertical'},
                      {'n_glyphs':2},{'n_glyphs':4}]:
        records.append({'kind':'controlled_generated','seed':17,'sample_index':0,
                        'difficulty':'medium','overrides':overrides,
                        'input':gen.generate(17,0,difficulty='medium',**overrides)})
    seen = {}
    canon_map=[]
    for row in canonical:
        for split in ['train','test']:
            pairs = row[split] if isinstance(row[split],list) else [row[split]]
            for index,pair in enumerate(pairs):
                key=json.dumps(pair['input'])
                if key not in seen:
                    seen[key]=len(records)
                    records.append({'kind':'canonical','source':row['source'],'split':split,'pair_index':index,
                                    'seed':None,'sample_index':None,'difficulty':None,'overrides':None,
                                    'input':pair['input'],'expected_output':pair['output']})
                else:
                    assert records[seen[key]]['expected_output'] == pair['output']
                canon_map.append({'source':row['source'],'split':split,'pair_index':index,'authority_index':seen[key]})
    training=next(row for row in canonical if row['source']=='training')
    pair=training['test'][0]
    mutation=copy.deepcopy(pair['input'])
    lc,line,_,_=roles(mutation)
    assert sorted(line) == [(12,c) for c in range(2,8)]
    for r,c in line:
        mutation[r][c]=7
    for c in range(2,8):
        assert mutation[14][c] == 7
        mutation[14][c]=lc
    records.append({'kind':'canonical_mutation','source':'training','split':'test','pair_index':0,
                    'seed':None,'sample_index':None,'difficulty':None,'overrides':None,
                    'mutation':'Move the six line-color cells from row12 to row14, columns2..7; no other edits.',
                    'input':mutation})
    for rec in records:
        rec['self_check']=gen.self_check(rec['input'])
        rec['observation']=observe(rec['input'])
        rec['rival_output']=fixed_stencil_rival(rec['input'])
    save('identity.json',identity)
    save('canonical-map.json',canon_map)
    save('records.json',records)
    save('input.json',[rec['input'] for rec in records])
    print(json.dumps({'identity':identity,'inputs':len(records),'canonical_rows':len(canonical),
                      'canonical_pairs':len(canon_map),'unique_canonical_inputs':len(seen),
                      'controls':[rec['observation'] for rec in records[24:29]],
                      'mutation_validator':records[-1]['self_check'],
                      'mutation_out_of_bounds':records[-1]['observation']['out_of_bounds_endpoint_stamp_cells']}))
else:
    identity=json.loads((outdir/'identity.json').read_text())
    records=json.loads((outdir/'records.json').read_text())
    receipt=json.loads((outdir/'racket.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == identity['generator_sha256'] == receipt['generator_sha256']
    assert receipt['executed_rule_hash'] == identity['canonical_rule_hash'] and receipt['rule_hash_matches_catalog']
    assert len(receipt['results']) == len(records)
    for rec,actual in zip(records,receipt['results']):
        assert actual['input'] == rec['input'] and actual['valid_output'] and actual['error'] is None
        rec['actual_racket_output']=actual['output']
        rec['rival_agrees']=rec['rival_output'] == actual['output']
        if 'expected_output' in rec:
            assert actual['output'] == rec['expected_output']
    generated=records[:29]
    assert all(not rec['self_check'] and rec['rival_agrees'] for rec in generated)
    assert all(rec['input'] == records[24]['input'] for rec in records[24:29])
    assert not records[-1]['self_check'] and len(records[-1]['observation']['out_of_bounds_endpoint_stamp_cells']) == 6
    shape_failures=[(i,rec) for i,rec in enumerate(records) if rec['kind']=='canonical' and not rec['rival_agrees']]
    assert len(shape_failures)==2
    assert records[31]['actual_racket_output'][2][10] == 8 and records[31]['rival_output'][2][10] == 7
    assert records[32]['actual_racket_output'][10][1] == 2 and records[32]['rival_output'][10][1] == 7
    assert sum(v == 2 for row in records[-1]['actual_racket_output'] for v in row) == 12
    save('finding-stencil.json',{'identity':identity,'generated_witness':records[0],
                                 'canonical_counterexamples':[{'authority_index':i,**rec} for i,rec in shape_failures]})
    save('finding-clipping.json',{'identity':identity,'authority_index':len(records)-1,
                                  'counterexample':records[-1],
                                  'stamp_color_cells_in_actual_output':sum(v==records[-1]['observation']['stamp_color']
                                      for row in records[-1]['actual_racket_output'] for v in row)})
    save('finding-controls.json',{'identity':identity,'cases':[{'authority_index':i,**rec}
                                                              for i,rec in enumerate(records) if 24<=i<29]})
    summary={'generated_default_count':24,'controlled_count':5,'generated_selfcheck_passes':29,
             'generated_rival_agrees':29,'unique_generated_inputs':len({json.dumps(r['input']) for r in generated}),
             'canonical_unique_count':4,'canonical_label_matches':4,
             'canonical_rival_disagreements':[i for i,_ in shape_failures],
             'canonical_self_checks':[r['self_check'] for r in records if r['kind']=='canonical'],
             'accepted_clipping_input':len(records)-1,'clipped_stamp_cells':6,
             'identical_controlled_inputs':True,'executed_rule_text_sha256':receipt['rule_text_sha256']}
    save('summary.json',summary)
    print(json.dumps(summary))
