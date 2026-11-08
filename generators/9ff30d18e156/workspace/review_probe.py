"""Reproducible, source-bound Racket census and findings-only audit probes.

Run from packet_root via run_with_racket.py; this script stages an independent
runtime and loads canonical program_solution explicitly (not archival fallback).
Not a blind-solve tool: never run it during the fresh solve phase.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
PACKET = REPO.parent
TASK = '9ff30d18e156'
AUDITS = ['adfbfbdb73c3', '32287e53c19c']
sys.path.insert(0, str(REPO / 'src'))
from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime


def sha(data):
    return hashlib.sha256(data).hexdigest()


def norm(grid):
    return [[int(v) for v in row] for row in grid]


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canonical_pairs(task):
    test = task.get('test', [])
    test = [test] if isinstance(test, dict) else test
    return [('train', i, {'input': norm(p['input']), 'output': norm(p['output'])})
            for i, p in enumerate(task['train'])] + [
            ('test', i, {'input': norm(p['input']), 'output': norm(p['output'])})
            for i, p in enumerate(test) if 'output' in p]


def row_fill_mirror(grid):
    """Independent diagnostic comparator only; never used to supply labels."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for color in dict.fromkeys(v for v in row if v):
            cols = [c for c, v in enumerate(row) if v == color]
            if len(cols) >= 2:
                out[r][cols[0]:cols[-1]+1] = [color] * (cols[-1]-cols[0]+1)
    return out


def preserve_seeds_rival(grid):
    """The chamber SUMMARY's seed-preserving interpretation, independently BFS'd."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    priority = [v for v in grid[0] if v not in (0,5)]
    unseen = {(r,c) for r in range(1,h) for c in range(w) if grid[r][c] != 5}
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        queue, component = deque([first]), []
        while queue:
            r,c = queue.popleft()
            component.append((r,c))
            for n in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if n in unseen:
                    unseen.remove(n)
                    queue.append(n)
        present = {grid[r][c] for r,c in component}
        fill = next((v for v in priority if v in present), 0)
        for r,c in component:
            if grid[r][c] == 0:
                out[r][c] = fill
    return out


def reverse_tie_rival(grid):
    h, w = len(grid), len(grid[0])
    pw = (w-3)//4
    panels = [[row[i*(pw+1):i*(pw+1)+pw] for row in grid] for i in range(4)]
    order = sorted(range(4), key=lambda i:(sum(v not in (0,9) for row in panels[i] for v in row), -i))
    out = [[0]*(2*pw) for _ in range(2*h)]
    for dest, src in enumerate(order):
        dr, dc = (dest//2)*h, (dest%2)*pw
        for r, row in enumerate(panels[src]):
            for c, v in enumerate(row):
                if v not in (0,9):
                    out[dr+r][dc+c] = 8
    return out


def identity(task_id, task, gen_path, argv, runtime):
    code = task['program_solution'].encode()
    return {'task_id':task_id, 'generator_sha256':sha(gen_path.read_bytes()),
            'canonical_rule_sha256':sha(code), 'canonical_rule_hash12':sha(code)[:12],
            'canonical_record_sha256':sha(json.dumps(task,sort_keys=True,separators=(',',':')).encode()),
            'probe_sha256':sha(Path(__file__).read_bytes()),
            'reproduction':{'cwd':'packet_root', 'argv':argv},
            'actual_runtime_directory':str(runtime),
            'rule_authority':'shared/data/canonical/puzzles.jsonl:program_solution'}


def selected(task, mod, apply, out, info):
    canonical = []
    failures = []
    for split, index, pair in canonical_pairs(task):
        answer = apply(pair['input'])
        entry = {'split':split,'index':index,'validator_errors':mod.self_check(pair['input']),
                 'racket_matches_canonical':answer == pair['output'],
                 'rival_matches':{name:rival(pair['input']) == answer for name,rival in mod.SEMANTIC_RIVALS.items()}}
        canonical.append(entry)
        if answer != pair['output']:
            failures.append({'canonical_mismatch':entry})
    dump(out/'canonical.json', {**info,'pairs':canonical})
    old_path = PACKET / '.review/baseline/repo/generators' / TASK / 'generator.py'
    baseline = load_module(old_path, 'review_baseline')
    stats = {}
    for phase, gen, gen_hash in [('before',baseline,sha(old_path.read_bytes())), ('final',mod,info['generator_sha256'])]:
        counts = Counter()
        colors, inputs, outputs = set(), set(), set()
        records = {}
        witness_saved = set()
        local_failures = []
        with (out/f'{phase}-census.jsonl').open('w') as handle:
            for band in ('easy','medium','hard'):
                for seed in range(20):
                    for index in range(8):
                        grid = gen.generate(seed,index,difficulty=band)
                        answer = apply(grid)
                        errors = gen.self_check(grid)
                        rivals = {name:rival(grid) == answer for name,rival in mod.SEMANTIC_RIVALS.items()}
                        entry = {'phase':phase,'generator_sha256':gen_hash,'difficulty':band,'seed':seed,'sample_index':index,
                                 'input':grid,'racket_output':answer,'self_check_errors':errors,'rival_matches':rivals}
                        handle.write(json.dumps(entry,separators=(',',':'))+'\n')
                        records[band,seed,index] = {'input':grid,'output':answer}
                        counts['draws'] += 1
                        counts['validator_failures'] += bool(errors)
                        counts['identity_outputs'] += grid == answer
                        counts['mirror_mismatches'] += row_fill_mirror(grid) != answer
                        counts['strict_canonical_like'] += not mod.strict_canonical_like(grid)
                        for name, match in rivals.items():
                            counts['rival_matches:'+name] += match
                            if phase == 'final' and not match and name not in witness_saved:
                                witness_saved.add(name)
                                dump(out/f'generated-counterexample-{name}.json', {**info,**entry,
                                    'rival_name':name,'rival_output':mod.SEMANTIC_RIVALS[name](grid),
                                    'documented_generator_domain':True,'actually_generated':True})
                        inputs.add(json.dumps(grid))
                        outputs.add(json.dumps(answer))
                        colors.update(v for row in grid for v in row)
                        if errors or grid == answer or row_fill_mirror(grid) != answer:
                            local_failures.append(entry)
            lessons, identifiable = 0, 0
            # These 240 windows overlap in the 480 recorded draws; not 960 new inputs.
            for band in ('easy','medium','hard'):
                for seed in range(20):
                    for start in range(4):
                        demos = [records[band,seed,i] for i in range(start,start+3)]
                        query = records[band,seed,start+3]
                        lessons += 1
                        identifiable += not mod.lesson_identifiable(demos,query)
        stats[phase] = {'generator_sha256':gen_hash,**dict(counts),
                        'unique_inputs':len(inputs),'unique_outputs':len(outputs),'colors':sorted(colors),
                        'seed_range':[0,19],'sample_index_range':[0,7],'bands':['easy','medium','hard'],
                        'overlapping_lesson_windows':lessons,'lessons_refuting_both_named_rivals':identifiable,
                        'scope':'finite named rivals only; not universal identifiability'}
        dump(out/f'{phase}-failures.json',local_failures)
        if phase == 'final':
            failures.extend(local_failures)
            if identifiable != lessons:
                failures.append({'unidentified_final_lessons':lessons-identifiable})
    # Compact human-readable witnesses, backed by the real Racket runtime.
    for name, grid in [('whole_row',[[0]*8,[2,0,2,0,3,0,3,0],[0]*8]),
                       ('exactly_two',[[0]*8,[2,0,2,0,2,0,0,0],[0]*8])]:
        answer = apply(grid)
        rival = mod.SEMANTIC_RIVALS[name](grid)
        assert answer != rival
        assert not mod.self_check(grid)
        dump(out/f'compact-counterexample-{name}.json', {**info,'input':grid,'racket_output':answer,
             'rival_name':name,'rival_output':rival,'self_check_errors':mod.self_check(grid),
             'documented_generator_domain':True,'actually_generated':False,
             'note':'Constructed witness; emitted-profile witnesses are recorded separately.'})
    dump(out/'summary.json',{**info,'phases':stats,'failures':failures})
    return len(failures)


def audit(task_id, task, mod, apply, out, info):
    rival = preserve_seeds_rival if task_id == AUDITS[0] else reverse_tie_rival
    canonical, witnesses, sampled = [], [], []
    for split,index,pair in canonical_pairs(task):
        answer = apply(pair['input'])
        other = rival(pair['input'])
        entry = {**info,'split':split,'index':index,'input':pair['input'],
                 'racket_output':answer,'rival_output':other,
                 'canonical_output_matches':answer == pair['output'],
                 'self_check_errors':mod.self_check(pair['input']),
                 'rival_disagrees':answer != other,'actually_generated':False}
        canonical.append(entry)
        if answer != other or entry['self_check_errors']:
            witnesses.append(entry)
    for band in ('easy','medium','hard'):
        for seed in range(10):
            for index in range(2):
                grid = mod.generate(seed,index,difficulty=band)
                answer = apply(grid)
                other = rival(grid)
                entry = {'seed':seed,'sample_index':index,'difficulty':band,'input':grid,
                         'racket_output':answer,'rival_output':other,
                         'self_check_errors':mod.self_check(grid),'rival_disagrees':answer != other}
                sampled.append(entry)
    differing = [e for e in sampled if e['rival_disagrees']]
    if differing:
        dump(out/f'{task_id}-generated-counterexample.json', {**info,**differing[0],
             'actually_generated':True,'documented_generator_domain':True,
             'domain_note':'Chamber input satisfies the documented input domain; its seed-preserving output description is contradicted.'})
    dump(out/f'{task_id}-canonical-witnesses.json',{**info,'cases':witnesses})
    dump(out/f'{task_id}-census.json',{**info,'canonical':canonical,'generated':sampled})
    override = {'n_legend':4} if task_id == AUDITS[0] else {'panel_h':2,'panel_w':2,'min_cells':0}
    pinned = mod.generate(0,0,**override)
    default = mod.generate(0,0)
    dump(out/f'{task_id}-override.json',{**info,'seed':0,'sample_index':0,'overrides':override,
         'default_input':default,'overridden_input':pinned,'byte_identical':default==pinned})
    summary = {**info,'canonical_pairs':len(canonical),
               'canonical_output_mismatches':sum(not e['canonical_output_matches'] for e in canonical),
               'canonical_validator_rejections':sum(bool(e['self_check_errors']) for e in canonical),
               'canonical_rival_disagreements':sum(e['rival_disagrees'] for e in canonical),
               'generated_draws':len(sampled),'generated_unique_inputs':len({json.dumps(e['input']) for e in sampled}),
               'generated_rival_disagreements':len(differing),
               'generated_validator_rejections':sum(bool(e['self_check_errors']) for e in sampled),
               'seed_range':[0,9],'sample_index_range':[0,1],'bands':['easy','medium','hard'],
               'override_ignored':pinned==default}
    dump(out/f'{task_id}-summary.json',summary)
    return summary['canonical_output_mismatches']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('selected','audits'),required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    ids = [TASK] if args.mode == 'selected' else AUDITS
    tasks = {}
    for line in (REPO/'shared/data/canonical/puzzles.jsonl').open():
        item = json.loads(line)
        if item.get('task_id') in ids:
            tasks[item['task_id']] = item
    argv = ['python3','run_with_racket.py','python3',str(Path(__file__).relative_to(REPO)),
            '--mode',args.mode,'--out',str(args.out)]
    failures = 0
    with tempfile.TemporaryDirectory(prefix='arc-task-review-') as directory:
        runtime = Path(directory)
        receipt = prepare_runtime(Catalog(REPO),runtime,task_ids=ids)
        dump(out/'runtime-manifest.json',receipt)
        sys.path.insert(0,str(runtime))
        from puzzle_generators import runner
        for task_id in ids:
            task = tasks[task_id]
            path = runtime/'puzzle_generators/per_puzzle'/task_id/'generator.py'
            mod = load_module(path,'review_'+task_id)
            info = identity(task_id,task,path,argv,runtime)
            bridge, fn = runner._open_bridge_with_rule(runner.wrap_rule(task['program_solution']))
            def apply(grid):
                return runner._apply_rule(bridge,fn,grid)
            try:
                if args.mode == 'selected':
                    failures += selected(task,mod,apply,out,info)
                else:
                    failures += audit(task_id,task,mod,apply,out,info)
            finally:
                bridge.shutdown()
    print(json.dumps({'mode':args.mode,'failures':failures,'out':str(out)}))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
