"""Retained bounded Racket witness for a natural undeclared count-threshold rival."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

WORK=Path(__file__).resolve().parents[2]
ROOT=WORK/'repo'
sys.path.insert(0,str(ROOT/'shared/runtime'))
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path


def sha(value):
    if not isinstance(value,bytes):value=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(value).hexdigest()


def objects(grid):
    seen=set(); result=[];h,w=len(grid),len(grid[0])
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r,c) in seen:continue
            color=grid[r][c];q=[(r,c)];seen.add((r,c));cells=[]
            while q:
                y,x=q.pop();cells.append((y,x))
                for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if 0<=yy<h and 0<=xx<w and (yy,xx) not in seen and grid[yy][xx]==color:
                        seen.add((yy,xx));q.append((yy,xx))
            result.append((color,cells))
    return result


def smallest_fit(grid):
    frames=[];counts=Counter();out=[row[:] for row in grid]
    for color,cells in objects(grid):
        if len(cells)==1:
            r,c=cells[0];out[r][c]=0;counts[color]+=1
        else:
            t,l=min(r for r,c in cells),min(c for r,c in cells)
            b,r=max(r for r,c in cells),max(c for r,c in cells)
            frames.append((((b-t-1)*(r-l-1)+1)//2,t,l,b,r))
    groups=sorted((count,color) for color,count in counts.items())
    for capacity,t,l,b,r in sorted(frames):
        if groups and groups[0][0]<=capacity:
            _,color=groups.pop(0)
            for y in range(t+1,b):
                for x in range(l+1,r):
                    if (y-t-1+x-l-1)%2==0:out[y][x]=color
    return out


def apply(bridge,program,grid):
    source=program.strip()
    assert source.startswith('(rule! (lambda (g)') and source.endswith(')')
    body=source[len('(rule!'):-1].strip()
    literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
    return bridge.eval_text(f'({body} {literal})')


def main():
    source=WORK/'checks/code-review/source-snapshot-c1fe.py'
    expected='c1fe4fd6daebdee855408ac273f812abd40c22f3218ca3a04aeeb9dbfe31d53e'
    assert sha(source.read_bytes())==expected
    spec=importlib.util.spec_from_file_location('reviewed_canonical_source',source)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    programs=set()
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row=json.loads(line)
            if row.get('task_id')==mod.TASK_ID:programs.add(row['program_solution'])
    assert len(programs)==1
    program=programs.pop()
    canonical=[]
    for pair in canonical_pairs(mod.TASK_ID,root=ROOT,labeled_only=True):
        pred=smallest_fit(pair['input'])
        canonical.append({'variant':pair['variant'],'split':pair['split'],'pair_index':pair['pair_index'],
                          'input_sha256':sha(pair['input']),'fits':pred==pair['output'],
                          'prediction_sha256':sha(pred)})
    with RacketBridge() as bridge:
        populations=[]
        for name,overrides in (('default',{}),('one_frame_override',{'n_frames':1})):
            pairs=[]
            for index in (2,3,4,5):
                grid=mod.generate(0,index,**overrides)
                answer=apply(bridge,program,grid)
                pred=smallest_fit(grid)
                frames,singles=mod._scene(grid)
                changed=[{'row':r,'col':c,'canonical':answer[r][c],'rival':pred[r][c]}
                         for r in range(len(grid)) for c in range(len(grid[0])) if answer[r][c]!=pred[r][c]]
                pairs.append({'seed':0,'sample_index':index,'input':grid,'output':answer,
                              'rival_output':pred,'input_sha256':sha(grid),
                              'mode':mod.observe_overrides(grid)['match_mode'],
                              'frame_capacities':sorted(f[5] for f in frames),
                              'singleton_counts':sorted(singles.values()),
                              'rival_fits':pred==answer,'changed_cells':changed})
            demos,query=pairs[:3],pairs[3]
            populations.append({'name':name,'overrides':overrides,'pairs':pairs,
                                'demos_fit_smallest_fit':all(p['rival_fits'] for p in demos),
                                'query_disagrees_smallest_fit':not query['rival_fits'],
                                'declared_lesson_hook_reasons':mod.lesson_identifiable(demos,query),
                                'rank_rival_fits_demos':all(mod.rank_pairing(p['input'])==p['output'] for p in demos),
                                'rank_rival_disagrees_query':mod.rank_pairing(query['input'])!=query['output']})
        runtime=bridge.runtime_identity
    report={'schema':'arc-smallest-fit-code-review-witness-v1','status':'ambiguity_confirmed',
            'reviewed_source_sha256':expected,'reviewed_source_snapshot':str(source),
            'probe_source_sha256':sha(Path(__file__).read_bytes()),'python':sys.executable,'command':sys.argv,
            'canonical_program':program,'canonical_program_sha256':sha(program.encode()),
            'racket_runtime':runtime,'canonical_fit':canonical,'populations':populations,
            'scope':'Eight bounded Racket applications for two four-pair source-bound witnesses, not a battery/sweep'}
    out=WORK/'checks/code-review/smallest-fit-witness.json'
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    default=populations[0]
    public={'train':[{'input':p['input'],'output':p['output']} for p in default['pairs'][:3]],
            'test':[{'input':default['pairs'][3]['input']}]}
    (WORK/'checks/code-review/smallest-fit-challenge.json').write_text(json.dumps(public,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'source_sha256':expected,'canonical_records':len(canonical),
                      'fits_all_canonical':all(p['fits'] for p in canonical),
                      'populations':[{'name':p['name'],'demos_fit':p['demos_fit_smallest_fit'],
                                      'query_disagrees':p['query_disagrees_smallest_fit'],
                                      'query_changed_cells':len(p['pairs'][3]['changed_cells']),
                                      'first_changed_cell':p['pairs'][3]['changed_cells'][0],
                                      'lesson_hook_reasons':p['declared_lesson_hook_reasons']} for p in populations]},indent=2))
    assert all(p['fits'] for p in canonical)
    assert default['demos_fit_smallest_fit'] and default['query_disagrees_smallest_fit']
    return 0


if __name__=='__main__':raise SystemExit(main())
