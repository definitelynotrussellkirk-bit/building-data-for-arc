"""Retained audit reproducer. Run prepare, three public arcpuzzles apply calls, then finish.
Population comparisons below use structural predicates, NOT unrun Racket labels.
"""
from __future__ import annotations
import argparse, collections, hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(Path.cwd())
PACKET = ROOT.parent
TASKS = ('9e11fddfa38a', '4977f1fc4c50', '28268c57c367')


def load(task, source=None):
    source = source or ROOT/'generators'/task/'generator.py'
    spec = importlib.util.spec_from_file_location('audit_'+task, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, hashlib.sha256(source.read_bytes()).hexdigest()


def bbox_color(grid, color):
    cells = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color]
    top,bottom = min(r for r,c in cells), max(r for r,c in cells)
    left,right = min(c for r,c in cells), max(c for r,c in cells)
    return [row[left:right+1] for row in grid[top:bottom+1]]


def rarest(grid):
    counts = collections.Counter(v for row in grid for v in row)
    color = min(counts, key=lambda c:(counts[c],c))
    return bbox_color(grid,color)


def preserve_occupied(grid):
    n=len(grid); out=[row[:] for row in grid]
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v and grid[n-1-c][n-1-r] == 0:
                out[n-1-c][n-1-r] = v
    return out


def encoded(grid):
    return json.dumps(grid,separators=(',',':'))


def prepare():
    for task in TASKS:
        module, source_sha=load(task)
        pairs=canonical_pairs(task,root=ROOT)
        population=[]
        per_band={}
        for band in ('easy','medium','hard'):
            rows=[]
            for seed in range(100):
                g=module.generate(seed,0,difficulty=band)
                row={'input_sha256':hashlib.sha256(encoded(g).encode()).hexdigest(),
                     'seed':seed,'sample_index':0,'difficulty':band,
                     'validator_errors':module.self_check(g)}
                if task=='9e11fddfa38a':
                    n=len(g)
                    row['axis_cells']=sum(g[r][n-1-r]!=0 for r in range(n))
                    row['occupied_reflection_pairs']=sum(
                        bool(g[r][c] and g[n-1-c][n-1-r])
                        for r in range(n) for c in range(n) if (r,c)<(n-1-c,n-1-r))
                elif task=='4977f1fc4c50':
                    counts=collections.Counter(v for line in g for v in line)
                    color=min(counts,key=lambda c:(counts[c],c))
                    row['rarest_color_is_unique_frame']=bool(module._frame_info_for_color(g,color))
                else:
                    row.update(module.observe_overrides(g))
                    row['shared_ray_witness']=module.SEMANTIC_WITNESSES['shared_ray_preserves_and_crosses_obstacles'](g)
                rows.append(row);population.append(row)
            per_band[band]={'draws':len(rows),'validator_rejections':sum(bool(r['validator_errors']) for r in rows)}
        report={'task_id':task,'generator_sha256':source_sha,'generator_version':module.VERSION,
                'population':population,'per_band':per_band,
                'unique_inputs':len({r['input_sha256'] for r in population}),
                'population_label_policy':'Structural predicates and target self_check only; exact retained witness separately labeled by public Racket CLI.',
                'canonical_pair_count':len(pairs),
                'canonical_unique_pairs':len({encoded([p['input'],p['output']]) for p in pairs})}
        if task=='9e11fddfa38a':
            pair=next(p for p in pairs if p['split']=='test');g=pair['input'];rival=preserve_occupied
            report['origin']={'kind':'canonical_test','variant':pair['variant'],'pair_index':pair['pair_index']}
            report['documented_generator_domain']=False
            report['domain_note']='Canonical input is Racket-lawful but violates the generator no-occupied-mirror-pairs invariant.'
            report['rival_name']='preserve_occupied_when_echoing'
            report['axis_cells_total']=sum(r['axis_cells'] for r in population)
            report['collision_inputs']=sum(bool(r['occupied_reflection_pairs']) for r in population)
        elif task=='4977f1fc4c50':
            base=module.generate(0,0,difficulty='medium');g=[row[:] for row in base]
            used={v for row in g for v in row};new=next(v for v in range(1,10) if v not in used)
            old=g[0][0];g[0][0]=new;rival=rarest
            report['origin']={'kind':'constructed_valid_perturbation','seed':0,'sample_index':0,
                              'difficulty':'medium','overrides':{},'mutation':{'position':[0,0],'before':old,'after':new}}
            report['documented_generator_domain']=True
            report['domain_note']='Satisfies declared density, unique-frame and interior invariants and self_check. The extra singleton is not claimed to be in default constructive support.'
            report['rival_name']='crop_bbox_of_rarest_color'
            report['rarest_is_frame']=sum(r['rarest_color_is_unique_frame'] for r in population)
        else:
            seed=next(s for s in range(10000)
                      if module.schedule_profile(s,0)=='rich'
                      and len(module.generate(s,0,difficulty='medium'))*len(module.generate(s,0,difficulty='medium')[0])<=63)
            g=module.generate(seed,0,difficulty='medium');rival=module.CANONICAL_SHORTCUTS['nearest_source']
            report['origin']={'kind':'unmodified_default_sample','seed':seed,'sample_index':0,'difficulty':'medium','overrides':{}}
            report['documented_generator_domain']=True
            report['rival_name']='nearest_source'
            report['domain_note']='Unmodified natural rich sample, not a hand-written or override-only counterexample.'
            old,old_sha=load(task,PACKET/'.review/baseline/repo/generators'/task/'generator.py')
            old_grids=[old.generate(s,0,difficulty=b) for b in ('easy','medium','hard') for s in range(100)]
            def features(grid):
                wall=next(c for c in range(len(grid[0])) if all(row[c]==5 for row in grid))
                return {'offwall_gray':sum(v==5 for row in grid for v in row[:wall]),
                        'shared_source_row':any(sum(v not in (0,5) for v in row[:wall])>=2 for row in grid)}
            report['baseline_population']={'generator_sha256':old_sha,'draws':len(old_grids),
                'unique_inputs':len({encoded(g) for g in old_grids}),
                'seeds':[0,99],'indices':[0],'bands':['easy','medium','hard'],
                'offwall_gray_inputs':sum(features(g)['offwall_gray']>0 for g in old_grids),
                'shared_source_row_inputs':sum(features(g)['shared_source_row'] for g in old_grids)}
        report['canonical_rival_fit']=[{'variant':p['variant'],'split':p['split'],'pair_index':p['pair_index'],
                                       'match':rival(p['input'])==p['output']} for p in pairs]
        report['input']=g;report['rival_output']=rival(g);report['validator_errors']=module.self_check(g)
        folder=PACKET/'checks/audit'/task;folder.mkdir(parents=True,exist_ok=True)
        (folder/'input.json').write_text(json.dumps(g)+'\n')
        (folder/'prepared.json').write_text(json.dumps(report,indent=2)+'\n')
        print(task,report['origin'],'canonical fits',sum(p['match'] for p in report['canonical_rival_fit']),len(pairs),
              'validator',report['validator_errors'])


def finish():
    for task in TASKS:
        folder=PACKET/'checks/audit'/task
        report=json.loads((folder/'prepared.json').read_text())
        actual=json.loads((folder/'racket.json').read_text())
        report['racket_report']='checks/audit/'+task+'/racket.json'
        report['actual_output']=actual['results'][0]['output']
        report['authority']={k:v for k,v in actual.items() if k!='results'}
        expected,wrong=report['actual_output'],report['rival_output']
        report['rival_disagrees']=expected!=wrong
        report['different_dimensions']= [len(expected),len(expected[0])] != [len(wrong),len(wrong[0])]
        if not report['different_dimensions']:
            report['differing_cells']=[{'row':r,'col':c,'actual':v,'rival':wrong[r][c]}
                    for r,row in enumerate(expected) for c,v in enumerate(row) if v!=wrong[r][c]]
        if not report['rival_disagrees']:
            raise AssertionError(f'Witness does not distinguish rival: {task}')
        (folder/'counterexample.json').write_text(json.dumps(report,indent=2)+'\n')
        print(task,'Racket-verified disagreement',report.get('differing_cells','shape mismatch'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['prepare','finish']);args=parser.parse_args()
    (prepare if args.phase=='prepare' else finish)()
