#!/usr/bin/env python3
"""Read-only, source-bound probes for the two assigned adversarial audits.

Run from packet_root with run_with_racket.py; see workspace/README.md.
The ordinary and boundary grids are labelled by actual canonical Racket, not
by the audited Python mirrors. A findings report is not a release approval.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile

from probe_distribution import REPO, BANDS, digest, encoded, load, racket_outputs

TARGETS = ('a16cf9241d71', 'db95939a5dd0')


def boundaries(tid):
    if tid == TARGETS[0]:
        names = ('grid_h','grid_w','shape_idx','shape_color','axis_gap','vertical_profile')
        values = ((5,12),(7,15),range(5),(1,9),(0,1),('top','middle','bottom'))
    else:
        names = ('grid_h','grid_w','n_shapes','max_region_width','palette_kind')
        values = ((12,16),(12,14),(1,2),(4,7),('canonical','broad'))
    return [dict(zip(names,v)) for v in itertools.product(*values)]


def check_observed(tid, gen, grid, overrides):
    """Compare only declared exact axes; max_region_width is an upper bound."""
    got = gen.observe_overrides(grid)
    got.update(grid_h=len(grid), grid_w=len(grid[0]))
    errors = []
    for name, value in overrides.items():
        if name in got and got[name] != value:
            errors.append(f'{name}: requested {value!r}, observed {got[name]!r}')
    if tid == TARGETS[1]:
        if overrides.get('palette_kind') == 'canonical':
            if not {x for row in grid for x in row} <= {1,2,3,4,6,7,8}:
                errors.append('canonical palette includes an unsupported color')
        if 'max_region_width' in overrides:
            _bg, comps = gen._components(grid)
            for cells in comps:
                _top, top, _bot, bot = gen._classes(cells,grid)
                for part in (top,bot):
                    width=max(c for r,c in part)-min(c for r,c in part)+1
                    if width > overrides['max_region_width']:
                        errors.append('region exceeds max_region_width bound')
    return errors


def audit(tid, bridge, args):
    source=REPO/f'generators/{tid}/generator.py'
    before=digest(source);gen=load(source)
    records=[];failures=[];groups={};corpus_hash=hashlib.sha256()
    def add(meta, **overrides):
        try:
            grid=gen.generate(meta['seed'],meta['sample_index'],difficulty=meta['band'],**overrides)
            again=gen.generate(meta['seed'],meta['sample_index'],difficulty=meta['band'],**overrides)
            errors=gen.self_check(grid)+check_observed(tid,gen,grid,overrides)
            if again != grid: errors.append('replay mismatch')
            if errors: failures.append({**meta,'overrides':overrides,'errors':errors,'input':grid})
            records.append((meta,grid))
        except Exception as exc:
            failures.append({**meta,'overrides':overrides,'error':repr(exc)})
    for band in BANDS:
        for seed in range(args.seeds):
            for index in range(6):
                add({'kind':'ordinary','band':band,'seed':seed,'sample_index':index})
        for i,overrides in enumerate(boundaries(tid)):
            add({'kind':'boundary','band':band,'seed':13,'sample_index':i%6,
                 'boundary_index':i},**overrides)
    fixture_details=[]
    for texture in getattr(gen,'DEGENERATE_TEXTURES',()):
        for seed in range(1,9):
            meta={'kind':'fixture','band':'medium','seed':seed,'sample_index':seed,'texture':texture}
            add(meta, texture=texture)
    rows=[json.loads(line) for line in (REPO/'shared/data/canonical/puzzles.jsonl').open()
          if json.loads(line).get('task_id') == tid]
    assert rows and len({row['program_solution'] for row in rows})==1
    rule=rows[0]['program_solution']
    rule_sha=hashlib.sha256(rule.encode()).hexdigest()
    counts=Counter();parity=Counter();uniques={};answers=[]
    mirror=gen._true_rule if tid==TARGETS[0] else gen._rule_output
    for (meta,grid),answer in zip(records,racket_outputs(bridge,rule,[g for _,g in records])):
        kind=meta['kind'];counts[kind]+=1;answers.append(answer)
        uniques.setdefault(kind,set()).add(encoded(grid))
        corpus_hash.update(encoded([meta,grid,answer])+b'\n')
        if mirror(grid)==answer: parity[kind]+=1
        else: failures.append({**meta,'kind':'racket_mismatch','input':grid,'racket_output':answer,
                               'python_output':mirror(grid)})
        if kind=='ordinary':groups.setdefault((meta['band'],meta['seed']),{})[meta['sample_index']]=(grid,answer)
        if kind=='fixture' and meta['seed']==1:
            fixture_details.append({**meta,'input':grid,'racket_output':answer,
                                    'self_check':gen.self_check(grid)})
    canon=[]
    for row in rows:
        tests=row['test'] if isinstance(row['test'],list) else [row['test']]
        canon.extend(row['train']+tests)
    canon_answers=list(racket_outputs(bridge,rule,[pair['input'] for pair in canon]))
    canonical={'rows':len(rows),'pair_references':len(canon),
               'unique_pairs':len({encoded(p) for p in canon}),
               'racket_matches':sum(p['output']==a for p,a in zip(canon,canon_answers))}
    if canonical['racket_matches']!=len(canon):failures.append({'kind':'canonical_mismatch'})
    rivals=getattr(gen,'LESSON_COMPETITORS',{})
    window_count=0;survivors=Counter()
    for group in groups.values():
        for begin in range(3):
            window_count+=1
            for name,fn in rivals.items():
                if all(fn(group[i][0])==group[i][1] for i in range(begin,begin+3)):
                    survivors[name]+=1
    unknown=[]
    for band in BANDS:
        for seed in range(5):
            try:
                grid=gen.generate(seed,0,difficulty=band,typo_axis=1)
                unknown.append({'band':band,'seed':seed,'sample_index':0,'accepted':True,
                                'self_check':gen.self_check(grid),'input':grid})
            except ValueError as exc:
                unknown.append({'band':band,'seed':seed,'sample_index':0,'accepted':False,
                                'error':str(exc)})
    import scripts.generator_defect_lint as lint
    texture_warnings,texture_notes=lint.probe_texture_overrides(gen)
    warnings=lint.probe_texture_domain_overlap(gen)+texture_warnings
    assert digest(source)==before, 'Audit source changed during read-only probe'
    return {'schema':'assigned-audit-probe-v1','task_id':tid,'generator_sha256':before,
            'source_unchanged':True,'probe_sha256':digest(__file__),'rule_sha256':rule_sha,
            'ordinary_sampling':{'bands':BANDS,'seed_range_inclusive':[0,args.seeds-1],
                                 'sample_indices':list(range(6))},
            'boundary_sampling':{'seed':13,'sample_index':'boundary_index % 6','bands':BANDS,
                                 'combinations_per_band':len(boundaries(tid)),
                                 'overrides':boundaries(tid)},
            'draw_counts':dict(counts),'actual_racket_matches':dict(parity),
            'unique_inputs':{k:len(v) for k,v in uniques.items()},
            'corpus_sha256':corpus_hash.hexdigest(),'canonical':canonical,'failures':failures,
            'ordinary_windows':{'overlapping':True,'demo_count':3,'denominator':window_count,
                 'rivals_checked':list(rivals),
                 'surviving_rivals':{name:survivors[name] for name in rivals}},
            'unknown_override_probe':{'name':'typo_axis','value':1,'denominator':len(unknown),
                 'accepted':sum(r['accepted'] for r in unknown),'records':unknown},
            'texture_probe':{'seeds':list(range(1,9)),'band':'medium','sample_index':'seed',
                             'warnings':warnings,'notes':texture_notes,'fixtures':fixture_details}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    parser.add_argument('--seeds',type=int,default=20)
    args=parser.parse_args()
    if args.seeds<1:parser.error('--seeds must be positive')
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix='assigned-audit-') as temporary:
        runtime=Path(temporary)
        receipt=prepare_runtime(Catalog(REPO),runtime,task_ids=list(TARGETS))
        sys.path.insert(0,str(runtime))
        from arc_repl.racket_bridge import RacketBridge
        try:
            with RacketBridge(timeout=30,max_calls_before_restart=256) as bridge:
                for tid in TARGETS:
                    report=audit(tid,bridge,args)
                    report['runtime_directory_at_execution']=str(runtime)
                    report['runtime_manifest_sha256']=digest(runtime/'RUNTIME_MANIFEST.json')
                    (out/f'{tid}.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
                    print(json.dumps({'task_id':tid,'draw_counts':report['draw_counts'],
                        'parity':report['actual_racket_matches'],'failures':len(report['failures']),
                        'unknown_keys_accepted':report['unknown_override_probe']['accepted'],
                        'texture_warnings':report['texture_probe']['warnings']}))
        finally:sys.path.remove(str(runtime))
    return 0  # report findings, including defects; this exit code is NOT an audit pass

if __name__=='__main__':raise SystemExit(main())
