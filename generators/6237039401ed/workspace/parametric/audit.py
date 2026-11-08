"""Bounded teaching census and protected-Racket parity/order witnesses.

Run from this independent checkout; writes one new evidence file.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    spec = importlib.util.spec_from_file_location('_623_window_audit', HOME / 'adapter.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    sys.path[:0] = [str(ROOT/'src'),str(ROOT/'shared/runtime')]
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from arcpuzzles import Catalog
    canonical = {v['program_solution'] for v in Catalog(ROOT).get('6237039401ed')['variants']}
    assert canonical == {module.program(module.SETTINGS[0])}
    census = 0
    for seed in range(8):
        for setting in module.SETTINGS:
            for demos in range(2,7):
                e = module.generate(seed,setting,demos,4)
                assert module.teaching_check(e,setting)['surviving_rivals'] == []
                census += 1
    bridge = RacketBridge(timeout=30); calls = 0
    def apply(program, grid):
        nonlocal calls
        module.validate_grid(grid)
        literal = "'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
        value = bridge.eval_text(f'({wrap_rule(program)} {literal})')
        module.validate_grid(value); calls += 1
        return value
    episodes, witnesses = [], []
    try:
        for setting in module.SETTINGS:
            episode = module.generate(20261024,setting,2,4)
            survivors = []
            for candidate in module.SETTINGS:
                predicted = [apply(module.program(candidate),p['input']) for p in episode['train']]
                if predicted == [p['output'] for p in episode['train']]: survivors.append(candidate)
            assert survivors == [setting]
            for pair in episode['test']:
                assert apply(module.program(setting),pair['input']) == pair['output']
            grid = [[5]*4 for _ in range(4)]
            correct = apply(module.program(setting),grid)
            wrong = apply(module.scan_rival_program(setting),grid)
            assert correct == module.transform(grid,setting)
            assert wrong == module.scan_rival(grid,setting)
            different = [[r,c] for r in range(4) for c in range(4) if correct[r][c] != wrong[r][c]]
            assert different
            episodes.append({'setting':setting,'seed':20261024,'episode':episode,
                             'teaching':module.teaching_check(episode,setting)})
            witnesses.append({'setting':setting,'input':grid,'reference_output':correct,
                              'paint_during_detection_output':wrong,'different_cells':different,
                              'reference_program':module.program(setting),
                              'counterfactual_program':module.scan_rival_program(setting)})
        result = {'schema':'arcpuzzles-window-membership-audit-v1','status':'passed',
            'task_id':'6237039401ed','python_episodes':census,'protected_racket_evaluations':calls,
            'runtime':bridge.runtime_identity,'episodes':episodes,'order_witnesses':witnesses,
            'source_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                            for p in [HOME/'adapter.py',HOME/'canonical.rkt',HOME/'promotion.json',Path(__file__),ROOT/'generators/6237039401ed/generator.py']],
            'limits':['Finite settings, named rivals and seed census; not unrestricted uniqueness.',
                      'The unchanged canonical sampler coverage audit remains open.',
                      'This audit alone grants no native acceptance or training admission.']}
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open('x') as handle: handle.write(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
        print(json.dumps({'status':'passed','python_episodes':census,'protected_racket_evaluations':calls,
                          'evidence':str(args.out)},indent=2))
    finally:
        bridge.shutdown()


if __name__ == '__main__': run()
