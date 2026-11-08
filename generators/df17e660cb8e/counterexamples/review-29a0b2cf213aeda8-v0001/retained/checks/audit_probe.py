from __future__ import annotations
import hashlib, importlib.util, json, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'repo'
sys.path.insert(0,str(ROOT/'shared/runtime'))
from reviewer_support import canonical_pairs, find_root


def load(task):
    path=ROOT/f'generators/{task}/generator.py'
    spec=importlib.util.spec_from_file_location(f'audit_{task}',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def digest(grid):
    return hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()


def audit_elbow():
    task='2dae2c34641b'; g=load(task); pairs=canonical_pairs(task,root=find_root(ROOT))
    result={'task_id':task,'generator_sha256':hashlib.sha256((ROOT/f'generators/{task}/generator.py').read_bytes()).hexdigest(),
            'canonical_pairs':len(pairs),'canonical_selfcheck_failures':0,'canonical_mirror_failures':0,
            'bands':{},'rival_disagreements':Counter()}
    for pair in pairs:
        result['canonical_selfcheck_failures'] += bool(g.self_check(pair['input']))
        result['canonical_mirror_failures'] += g.rule_mirror(pair['input']) != pair['output']
    all_inputs=set()
    for bi,band in enumerate(('easy','medium','hard')):
        row={'samples':0,'selfcheck_failures':0,'unique_inputs':set(),'pair_counts':Counter(),'bend_patterns':Counter()}
        for i in range(200):
            grid=g.generate(70000+bi*1000+i,i*11+bi,difficulty=band)
            row['samples']+=1; row['selfcheck_failures']+=bool(g.self_check(grid)); row['unique_inputs'].add(digest(grid)); all_inputs.add(digest(grid))
            obs=g.observe_overrides(grid); row['pair_counts'][str(obs['n_pairs'])]+=1; row['bend_patterns'][obs['bend_pattern']]+=1
            intended=g.rule_mirror(grid)
            for name,rival in g.LESSON_COMPETITORS.items():
                result['rival_disagreements'][name]+=rival(grid)!=intended
        row['unique_inputs']=len(row['unique_inputs']); row['pair_counts']=dict(row['pair_counts']); row['bend_patterns']=dict(row['bend_patterns'])
        result['bands'][band]=row
    result['unique_inputs']=len(all_inputs); result['rival_disagreements']=dict(result['rival_disagreements'])
    return result


def audit_waypoint():
    task='df17e660cb8e'; g=load(task); pairs=canonical_pairs(task,root=find_root(ROOT))
    result={'task_id':task,'generator_sha256':hashlib.sha256((ROOT/f'generators/{task}/generator.py').read_bytes()).hexdigest(),
            'canonical_pairs':len(pairs),'canonical_selfcheck_failures':0,'canonical_mirror_failures':0,
            'bands':{},'rival_disagreements':Counter(),'skip_six_disagreements':0}
    for pair in pairs:
        result['canonical_selfcheck_failures'] += bool(g.self_check(pair['input']))
        result['canonical_mirror_failures'] += g.rule_mirror(pair['input']) != pair['output']
    all_inputs=set()
    def skip_six(grid):
        order=[2,4,5,3]
        cells,errors=g._path_union(grid,order)
        return [r[:] for r in grid] if errors else g._paint_cells(grid,cells)
    for bi,band in enumerate(('easy','medium','hard')):
        row={'samples':0,'selfcheck_failures':0,'unique_inputs':set(),'intermediate_counts':Counter(),'orientations':Counter()}
        for i in range(200):
            grid=g.generate(90000+bi*1000+i,i*13+bi,difficulty=band)
            row['samples']+=1; row['selfcheck_failures']+=bool(g.self_check(grid)); row['unique_inputs'].add(digest(grid)); all_inputs.add(digest(grid))
            obs=g.observe_overrides(grid); row['intermediate_counts'][str(obs['n_intermediates'])]+=1; row['orientations'][obs['orientation']]+=1
            intended=g.rule_mirror(grid)
            for name,rival in g.LESSON_COMPETITORS.items():
                result['rival_disagreements'][name]+=rival(grid)!=intended
            result['skip_six_disagreements'] += skip_six(grid)!=intended
        row['unique_inputs']=len(row['unique_inputs']); row['intermediate_counts']=dict(row['intermediate_counts']); row['orientations']=dict(row['orientations'])
        result['bands'][band]=row
    result['unique_inputs']=len(all_inputs); result['rival_disagreements']=dict(result['rival_disagreements'])
    return result

out={'schema':'arc-review-audit-probe-v1','targets':[audit_elbow(),audit_waypoint()]}
Path('checks/audit-probe.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
