"""Read-only source-bound audit: background-counting shortcut on dense frames."""
from __future__ import annotations
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / 'repo'
SOURCE = REPO / 'generators/22f494053811/generator.py'
RULE = REPO / 'shared/data/base/solutions/banks/9397d19eada0/medium_56_frame_majority_centers__22f494053811.json'
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('audited_generator', SOURCE)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def frames(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 8 or (r, c) in seen:
                continue
            queue = collections.deque([(r, c)])
            seen.add((r, c))
            component = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 8 and (nr,nc) not in seen:
                        seen.add((nr,nc)); queue.append((nr,nc))
            r1, r2 = min(p[0] for p in component), max(p[0] for p in component)
            c1, c2 = min(p[1] for p in component), max(p[1] for p in component)
            border = {(rr,cc) for rr in range(r1,r2+1) for cc in range(c1,c2+1)
                      if rr in (r1,r2) or cc in (c1,c2)}
            if r2-r1 >= 2 and c2-c1 >= 2 and set(component) == border:
                found.append((r1,c1,r2,c2))
    return found

def solve(grid, *, count_zero=False):
    out = [[0]*len(grid[0]) for _ in grid]
    for r1,c1,r2,c2 in frames(grid):
        for r in range(r1,r2+1):
            for c in range(c1,c2+1):
                if r in (r1,r2) or c in (c1,c2):
                    out[r][c] = 8
        values = [grid[r][c] for r in range(r1+1,r2) for c in range(c1+1,c2)
                  if grid[r][c] != 8 and (count_zero or grid[r][c] != 0)]
        if values:
            frequencies = collections.Counter(values)
            chosen = min(frequencies, key=lambda v: (-frequencies[v], v))
            out[(r1+r2)//2][(c1+c2)//2] = chosen
    return out

def main():
    rule_data = json.loads(RULE.read_text())
    rt = rule_data['racket_target']
    provenance = {
        'task_id': '22f494053811', 'source_path': str(SOURCE.relative_to(REPO)),
        'source_sha256': sha(SOURCE.read_bytes()), 'version': generator.VERSION,
        'rule_file': str(RULE.relative_to(REPO)), 'rule_file_sha256': sha(RULE.read_bytes()),
        'raw_code_sha256': sha(rt['raw_code'].encode()),
        'target_code_sha256': sha(rt['target_code'].encode()),
        'review_index_exists': (SOURCE.parent/'evidence/review_index.json').exists(),
        'task_tests_exist': (SOURCE.parent/'tests').exists(),
        'notes': (SOURCE.parent/'notes.md').read_text(),
        'associated_notes_bytes': (SOURCE.parent/'evidence/associated_notes.jsonl').stat().st_size,
    }
    write('source_binding.json', provenance)
    # Minimal nonidentity odd-width frame with a unique wrong zero plurality.
    witness = [[0]*9 for _ in range(7)]
    for r in range(1,4):
        for c in range(1,6):
            if r in (1,3) or c in (1,5):
                witness[r][c] = 8
    witness[2][2] = 1
    write('input.json', witness)
    write('rival.json', solve(witness, count_zero=True))
    write('expected.json', solve(witness))
    write('legality.json', {
        'construction': 'hand-authored, no generator seed/sample/overrides',
        'generator_self_check': generator.self_check(witness),
        'canvas': [7,9], 'frame_bbox_zero_based': [1,1,3,5],
        'interior': [1,0,0], 'nonzero_counts': {'1':1},
        'rival_counts_including_zero': {'0':2,'1':1},
        'center_zero_based': [2,3],
        'canonical_lawful_reason': 'Complete isolated cyan rectangle, >=3x3, one nonzero interior color. Canonical rule excludes 0 and 8; no ambiguity or tie among legal colors.',
        'generator_domain_reason': 'self_check returns []; canvas fits AXES bounds; 3x3 identity exclusion does not apply.',
    })
    cases=[]
    for difficulty in ('easy','medium','hard'):
        for seed in (0,17):
            for sample_index in (0,1):
                args={'seed':seed,'sample_index':sample_index,'difficulty':difficulty,'overrides':{}}
                grid=generator.generate(seed,sample_index,difficulty=difficulty)
                frame_boxes=frames(grid)
                inner=[grid[r][c] for r1,c1,r2,c2 in frame_boxes for r in range(r1+1,r2) for c in range(c1+1,c2)]
                cases.append({'generate_call':args,'input':grid,
                              'self_check':generator.self_check(grid),
                              'frame_count':len(frame_boxes),'interior_zero_count':inner.count(0),
                              'rival_output':solve(grid,count_zero=True),
                              'spec_output':solve(grid)})
    write('generated_cases.json', cases)
    write('generated_inputs.json', {'inputs':[c['input'] for c in cases]})
    original=rule_data['visible_context']['train']
    write('canonical_examples_analysis.json', [
        {'split':'train','index':i,'self_check':generator.self_check(c['input']),
         'spec_matches_stored_output':solve(c['input'])==c['output'],
         'rival_matches_stored_output':solve(c['input'],count_zero=True)==c['output']}
        for i,c in enumerate(original)])
    records=[{'label':'probe_initial_path_error',
              'argv':['python3','../checks/audit/22f494053811/probe.py'],
              'cwd':str(REPO),'exit_code':1,
              'reason':'Authored audit probe initially used HERE.parents[3] rather than parents[2]; source was not found, no audited source modified.',
              'evidence_paths':['WORK/checks/audit/22f494053811/probe_initial_failure.txt']}]
    for label,input_name,output_name in (
        ('witness','input.json','racket.json'),
        ('normal_generated_cases','generated_inputs.json','generated_racket.json')):
        argv=['python3','../run_with_racket.py','python3','-m','arcpuzzles','apply','22f494053811',
              '--input',f'../checks/audit/22f494053811/{input_name}',
              '--out',f'../checks/audit/22f494053811/{output_name}']
        p=subprocess.run(argv,cwd=REPO,text=True,capture_output=True)
        (HERE/f'{label}.stdout.txt').write_text(p.stdout)
        (HERE/f'{label}.stderr.txt').write_text(p.stderr)
        records.append({'label':label,'argv':argv,'cwd':str(REPO),'exit_code':p.returncode,
                        'evidence_paths':[f'WORK/checks/audit/22f494053811/{input_name}',
                                          f'WORK/checks/audit/22f494053811/{output_name}',
                                          f'WORK/checks/audit/22f494053811/{label}.stderr.txt',
                                          f'WORK/checks/audit/22f494053811/{label}.stdout.txt']})
        write('command_records.json',records)
        if p.returncode:
            raise RuntimeError(p.stderr)
    witness_result=json.loads((HERE/'racket.json').read_text())
    generated_result=json.loads((HERE/'generated_racket.json').read_text())
    write('comparison.json', {
        'witness_racket_error':witness_result['results'][0]['error'],
        'witness_racket_matches_expected':witness_result['results'][0]['output']==solve(witness),
        'witness_rival_matches_racket':witness_result['results'][0]['output']==solve(witness,count_zero=True),
        'generated_case_count':len(cases),
        'generated_racket_errors':[r['error'] for r in generated_result['results'] if r['error']],
        'all_generated_rival_matches_racket':all(r['output']==c['rival_output'] for r,c in zip(generated_result['results'],cases,strict=True)),
        'all_generated_self_check_pass':all(not c['self_check'] for c in cases),
        'all_generated_interiors_completely_nonzero':all(c['frame_count'] and c['interior_zero_count']==0 for c in cases),
        'executed_rule_hash':witness_result['executed_rule_hash'],
        'rule_text_sha256':witness_result['rule_text_sha256'],
        'source_unchanged_after_probe':sha(SOURCE.read_bytes())==provenance['source_sha256'],
        'rule_file_unchanged_after_probe':sha(RULE.read_bytes())==provenance['rule_file_sha256'],
    })
    print((HERE/'comparison.json').read_text())

if __name__=='__main__':
    main()
