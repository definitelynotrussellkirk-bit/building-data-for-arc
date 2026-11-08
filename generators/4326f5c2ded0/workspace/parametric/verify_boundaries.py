"""Reproducible, bounded real-Racket checks for the proposed shear family."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
import shear


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def diagnostic(height, width, cells):
    grid = [[0]*width for _ in range(height)]
    for r,c,color in cells:
        grid[r][c] = color
    return grid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    settings = [shear.Settings(d,s) for d in shear.DIRECTIONS for s in shear.STRIDES]
    first = diagnostic(8,11,[(1,1,2),(1,9,7),(3,5,3),(4,5,4),(5,5,5)])
    edge = diagnostic(8,9,[(4,0,1),(4,1,2),(4,2,3),(4,6,4),(4,7,5),(4,8,6),(5,4,9)])
    exact = {
        ('left',1):[(1,5,7),(3,3,3),(4,4,4),(5,5,5)],
        ('left',2):[(1,1,7),(3,1,3),(4,3,4),(5,5,5)],
        ('right',1):[(1,5,2),(3,7,3),(4,6,4),(5,5,5)],
        ('right',2):[(1,9,2),(3,9,3),(4,7,4),(5,5,5)],
    }
    edges = {
        ('left',1):[(0,2),(1,3),(5,4),(6,5),(7,6)],
        ('left',2):[(0,3),(4,4),(5,5),(6,6)],
        ('right',1):[(1,1),(2,2),(3,3),(7,4),(8,5)],
        ('right',2):[(2,1),(3,2),(4,3),(8,4)],
    }
    cases,witnesses = [],[]
    with RacketBridge(timeout=10,startup_timeout=60) as bridge:
        identity = bridge.runtime_identity
        for setting in settings:
            outputs = shear.racket_labels([first,edge],setting,bridge)
            key = (setting.direction,setting.stride)
            expected = [diagnostic(8,11,exact[key]),
                        diagnostic(8,9,[(4,c,v) for c,v in edges[key]]+[(5,4,9)])]
            if outputs != expected:
                raise AssertionError(f'hand-derived endpoint witness failed: {key}')
            witnesses.append({'parameters':asdict(setting),'inputs':[first,edge],'outputs':outputs,
                              'hand_derived_expected_match':True})
            for height,width in [(8,9),(30,30),(8,30),(30,9)]:
                episode = shear.build_episode(113,settings=setting,n_train=2,n_test=4,
                                               height=height,width=width,bridge=bridge)
                pairs = episode['train']+episode['test']
                if len({digest(p['input']) for p in pairs}) != 6:
                    raise AssertionError('duplicate inputs')
                if any(len(p['input']) != height or any(len(r) != width for r in p['input']) for p in pairs):
                    raise AssertionError('dimension override mismatch')
                if episode['metadata']['lesson_audit']['surviving_parameters'] != [asdict(setting)]:
                    raise AssertionError('parameter not identified from demonstrations')
                cases.append({'parameters':asdict(setting),'seed':113,'height':height,'width':width,
                              'n_train':2,'n_test':4,'inputs_sha256':[digest(p['input']) for p in pairs],
                              'outputs_sha256':[digest(p['output']) for p in pairs],
                              'reference_sha256':episode['metadata']['reference']['sha256'],
                              'lesson_audit':episode['metadata']['lesson_audit']})
        # Sampling a hidden setting once must be independent of requested counts.
        random_setting_cases = []
        for n_train,n_test in [(1,4),(4,1)]:
            e = shear.build_episode(991,n_train=n_train,n_test=n_test,bridge=bridge)
            random_setting_cases.append({'n_train':n_train,'n_test':n_test,
                                         'parameters':e['metadata']['parameters'],
                                         'identifiable':e['metadata']['lesson_audit']['identifiable']})
        if random_setting_cases[0]['parameters'] != random_setting_cases[1]['parameters']:
            raise AssertionError('counts changed the hidden setting')
    report = {'schema':'arcpuzzles-shear-boundaries-v1','status':'pass','task_id':shear.TASK_ID,
              'scope':'prototype only; finite declared rivals; no production battery or training admission',
              'source_sha256':hashlib.sha256(Path(shear.__file__).read_bytes()).hexdigest(),
              'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'runtime_identity':identity,'boundary_episodes':len(cases),
              'racket_pairs_executed':8+len(cases)*6+10,
              'witnesses':witnesses,'cases':cases,'count_independence':random_setting_cases}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','boundary_episodes','racket_pairs_executed','source_sha256')},sort_keys=True))


if __name__ == '__main__':
    main()
