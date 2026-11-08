#!/usr/bin/env python3
"""Replay private episodes in protected Racket and export one-query public views.

Run through review.py run from the packet root. This tool does not accept a
family or admit data to training. Existing output paths are never overwritten.
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('_rolling_verify_prototype', BASE / 'prototype.py')
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)

DEPENDENCY = {
    'step_a':'Trace to the first reached orange ledge and find its end in the episode direction.',
    'intermediate':'The exit column beyond that reached ledge (gc), an input-dependent path state.',
    'step_b':'Continue from that exit column to select and process the next ledge or termination.',
    'why_b_depends_on_a':'Changing the reached ledge length changes the exit column and therefore the next collision. Reusing the pre-roll column bypasses or changes the next ledge.',
}


def _dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8')


@contextlib.contextmanager
def _racket(root):
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    root = Path(root).resolve()
    runtime = root if (root / 'RUNTIME_MANIFEST.json').is_file() else root / 'shared/runtime'
    with _local_imports(runtime, BASE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            yield apply, identity
        finally:
            bridge.close()


def export_verified(episodes, destination, root):
    """Verify every claimed label before creating any export files."""
    from arcpuzzles.parametric_worker import _grid
    from reviewer_support import public_challenge_bytes
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    if type(episodes) is not list or not episodes:
        raise ValueError('at least one private episode is required')
    prepared, evaluations = [], 0
    with _racket(root) as (apply, identity):
        for episode in episodes:
            code = prototype.program(episode['settings'])
            if episode['program_solution'] != code:
                raise ValueError('episode program differs from its declared setting')
            for split in ('train','test'):
                for index, pair in enumerate(episode[split]):
                    actual = _grid(apply(code, _grid(pair['input'])))
                    evaluations += 1
                    if actual != _grid(pair['output']):
                        raise ValueError(f'Racket label mismatch at {split}[{index}]')
            teaching = prototype.teaching_check(episode['train'],episode['settings'])
            if teaching['survivors'] != [episode['settings']['direction']] or teaching['surviving_shortcuts']:
                raise ValueError('demonstrations do not refute the declared finite rival set')
            for query in range(len(episode['test'])):
                raw = public_challenge_bytes(prototype.public_turn(episode,query))
                prepared.append((raw, {'settings':episode['settings'], 'seed':episode['seed'], 'query_index':query,
                                       'file':'public/'+hashlib.sha256(raw).hexdigest()+'.json'}))
    if len({row[0] for row in prepared}) != len(prepared):
        raise ValueError('duplicate public views are not exported')
    destination.mkdir(parents=True)
    (destination/'public').mkdir()
    for raw, row in prepared:
        (destination/row['file']).write_bytes(raw)
    report = {'schema':'rolling-direction-replay-v1', 'status':'passed',
              'racket':identity, 'racket_evaluations':evaluations, 'episodes':len(episodes),
              'public_files':len(prepared), 'queries_per_public_view':1,
              'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BASE.iterdir())
                               if p.suffix in ('.py','.rkt') or p.name=='promotion.json'},
              'limits':'Finite labels and declared demonstration-only rivals; no acceptance or training admission.'}
    _dump(destination/'private.json', {'episodes':episodes, 'public_index':[row for _,row in prepared]})
    _dump(destination/'report.json', report)
    return report


def write_witness(qualification_path, destination, root, seed=17):
    """Bind a real wrong-intermediate Racket replay to exact qualified source."""
    qualification = json.loads(Path(qualification_path).read_text())
    if qualification.get('status') != 'qualified' or qualification.get('task_id') != 'ba32e05911b0':
        raise ValueError('a successful qualification for this family is required')
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    cases = []
    with _racket(root) as (apply, identity):
        for direction in prototype.DIRECTIONS:
            settings = {'direction':direction}
            ep = prototype.generate(seed,settings,2,4)
            grid = ep['test'][0]['input']
            code = prototype.program(settings)
            key = json.dumps(settings,sort_keys=True,separators=(',',':'))
            if hashlib.sha256(code.encode()).hexdigest() != qualification['programs'].get(key):
                raise ValueError('current program no longer matches qualification')
            if code.count('(trace r gc)') != 1:
                raise ValueError('unexpected canonical continuation source')
            alternative = code.replace('(trace r gc)','(trace (- r 1) col)')
            actual, counterfactual = apply(code,grid), apply(alternative,grid)
            if actual != prototype.predict(grid,direction) or counterfactual != prototype.predict(grid,direction,'reset_column'):
                raise ValueError('counterfactual Python/Racket mismatch')
            differences = [[r,c] for r in range(len(grid)) for c in range(len(grid[0])) if actual[r][c] != counterfactual[r][c]]
            if not differences:
                raise ValueError('counterfactual must change final output')
            events = [e for t in prototype.trace(grid,direction)[1] for e in t['events'] if e['kind']=='roll']
            cases.append({'input':grid, 'settings':settings, 'program':code,
                          'intermediate_value':{'first_reached_ledge':events[0], 'next_reached_ledge':events[1]},
                          'ablation':'wrong_intermediate', 'counterfactual_program':alternative,
                          'counterfactual_description':'After writing each roll, climb one row in the pre-roll column instead of continuing at gc. This is total and intentionally wrong.',
                          'output':actual, 'counterfactual_output':counterfactual,
                          'difference_cells':len(differences), 'difference_coordinates':differences})
    witness = {'schema':'arcpuzzles-sequential-dependency-witness-v1',
               'source_binding':qualification['source_binding'],
               'racket':{'backend':'racket','protected':True},
               'runtime_identity':identity, **DEPENDENCY, 'cases':cases}
    _dump(destination,witness)
    return witness


def main():
    from reviewer_support import find_root
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=17)
    parser.add_argument('--demos',type=int,choices=range(2,7),default=3)
    parser.add_argument('--qualification',type=Path)
    args = parser.parse_args()
    root = find_root(__file__)
    episodes = [prototype.generate(args.seed,{'direction':direction},args.demos,4) for direction in prototype.DIRECTIONS]
    report = export_verified(episodes,args.out,root)
    if args.qualification:
        witness = write_witness(args.qualification,args.out/'sequential-witness.json',root,args.seed)
        from arcpuzzles.review_sequential_replay import replay_witness
        replay = replay_witness(root,witness)
        replay['execution_role'] = 'reviewer self-replay; not owner acceptance'
        _dump(args.out/'sequential-replay.json',replay)
        report = {**report, 'witness_cases':len(witness['cases']),
                  'counterfactual_executions':4, 'independent_replay_executions':replay['evaluations']}
        _dump(args.out/'report.json',report)
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__ == '__main__':
    main()
