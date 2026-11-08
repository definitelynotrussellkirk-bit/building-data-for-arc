"""Proposed component-size/connectivity family; never production authority.

The CLI checks every retained label and finite-setting teaching certificate by
executing Racket. generate() is a deterministic Python proposal for the thin
promotion adapter; it does not claim protected qualification or acceptance.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = '57bafcdde8c3'
DEFAULT = {'min_size': 2, 'connectivity': 4}
PARAMETERS = {'min_size': [2, 3, 4], 'connectivity': [4, 8]}
SETTINGS = [dict(min_size=m, connectivity=c) for m,c in itertools.product((2,3,4),(4,8))]
if str(REPO / 'shared/runtime') not in sys.path:
    sys.path.insert(0, str(REPO / 'shared/runtime'))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CANONICAL = '''(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((bg (mode g -1)))
             (for-each-object g
                              (objects g bg)
                              (lambda (acc obj)
                                (if (> (obj-size obj) 1)
                                    (paint-cells acc (obj-cells obj) 8)
                                    acc)))))))'''


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != set(PARAMETERS):
        raise ValueError('settings must name exactly min_size and connectivity')
    if any(type(settings[k]) is not int or settings[k] not in v for k,v in PARAMETERS.items()):
        raise ValueError('min_size must be 2|3|4 and connectivity must be 4|8; exact integers only')
    return dict(settings)


def _color_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list
            or len(row) != len(grid[0]) or any(type(c) is not int or not 0 <= c <= 9 for c in row)
            for row in grid)):
        raise ValueError('grid must be rectangular 1..30 with exact integer colors 0..9')


def _grid(grid):
    _color_grid(grid)
    counts = Counter(c for row in grid for c in row).most_common()
    if len(counts)>1 and counts[0][1] == counts[1][1]:
        raise ValueError('background must have a unique modal color')
    return counts[0][0]


def _generator():
    spec = importlib.util.spec_from_file_location('_canonical_component_generator', HERE.parents[1]/'generator.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _generator()


def program(settings):
    """Return exact canonical source at default and concrete Racket otherwise."""
    settings = _settings(settings)
    if settings == DEFAULT:
        return _CANONICAL
    objects = 'objects' if settings['connectivity'] == 4 else 'objects-8'
    return f'''(rule! (lambda (g)
  (let ((bg (mode g -1)))
    (for-each-object g ({objects} g bg)
      (lambda (acc obj)
        (if (>= (obj-size obj) {settings['min_size']})
            (paint-cells acc (obj-cells obj) 8)
            acc))))))'''


def transform(grid, settings):
    """Python proposal/mirror; Racket is the retained labeling authority."""
    settings = _settings(settings)
    bg = _grid(grid)
    output = [row[:] for row in grid]
    for obj in GEN._components(grid, background=bg, diagonal=settings['connectivity']==8):
        if obj['size'] >= settings['min_size']:
            for row,col in obj['cells']:
                output[row][col] = 8
    return output


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',',':')).encode()).hexdigest()


def _rng(seed, domain, index=0):
    # Domain separation: setting selection and every input draw have independent state.
    return random.Random(int(_digest([TASK_ID, 'components-v1', seed, domain, index]),16))


def _candidate(seed, index):
    rng = _rng(seed, 'input', index)
    if index % 6 < 2:
        return GEN.generate(rng.randrange(2**63), index % 2)
    h,w = ((16,20),(20,16),(24,24),(30,30))[(index % 6)-2]
    bg,fg = ((1,0),(7,3),(1,3),(7,0))[index%4]
    count = rng.randrange(max(27,h*w*16//100),h*w*31//100+1)
    selected = set(rng.sample(range(h*w),count))
    return [[fg if r*w+c in selected else bg for c in range(w)] for r in range(h)]


def fit_demos(demos, execute=None):
    """Fit only visible demonstrations against the six declared settings."""
    apply = execute or (lambda text, grid: transform(grid, next(s for s in SETTINGS if program(s)==text)))
    return [dict(s) for s in SETTINGS
            if all(apply(program(s),p['input']) == p['output'] for p in demos)]


def certify(episode, execute=None):
    """Check all labels and demo-only finite rivals; runtime errors propagate."""
    chosen = _settings(episode['settings'])
    if episode['program_solution'] != program(chosen):
        raise ValueError('program does not match fixed episode settings')
    train,test = episode['train'],episode['test']
    _integer(len(train),2,8,'demos'); _integer(len(test),1,8,'queries')
    all_pairs = train+test
    if len({_digest(p['input']) for p in all_pairs}) != len(all_pairs):
        raise ValueError('all demonstration and query inputs must be distinct')
    for pair in all_pairs:
        _grid(pair['input'])
        _color_grid(pair['output'])
    apply = execute or (lambda text, grid: transform(grid, next(s for s in SETTINGS if program(s)==text)))
    records=[]
    for setting in SETTINGS:
        predictions = [apply(program(setting),pair['input']) for pair in train]
        records.append({'settings':setting,'disagreeing_demo_indices':[
            i for i,(got,pair) in enumerate(zip(predictions,train)) if got != pair['output']]})
    survivors=[dict(r['settings']) for r in records if not r['disagreeing_demo_indices']]
    if survivors != [chosen]:
        raise ValueError(f'demonstrations do not uniquely identify selected finite setting: {survivors}')
    query_certs=[]
    for pair in test:
        predictions=[apply(program(s),pair['input']) for s in survivors]
        if any(got != pair['output'] for got in predictions):
            raise ValueError('query label disagrees with demonstration-fitting Racket/mirror rule')
        query_certs.append({'input_sha256':_digest(pair['input']),
                            'output_sha256':_digest(pair['output']),
                            'survivors':survivors,'unanimous':True})
    return {'scope':'six declared parameter settings only; demos fit before query checks',
            'racket_checked':execute is not None,'survivors':survivors,
            'demo_refutations':records,'queries':query_certs}


def generate(seed, settings=None, demos=3, queries=4, *, max_attempts=512):
    """Build a bounded proposal, never silently shortening requested counts."""
    _integer(seed,-2**63,2**63-1,'seed')
    _integer(demos,2,8,'demos'); _integer(queries,1,8,'queries')
    _integer(max_attempts,1,8192,'max_attempts')
    chosen = _settings(_rng(seed,'settings').choice(SETTINGS) if settings is None else settings)
    train=[]; test=[]; seen=set(); survivors=list(SETTINGS); attempts=0
    while attempts < max_attempts and len(train)<demos:
        grid = _candidate(seed,attempts); attempts+=1
        key = _digest(grid)
        if key in seen: continue
        output=transform(grid,chosen)
        remaining=[s for s in survivors if transform(grid,s)==output]
        if len(survivors)>1 and len(remaining)==len(survivors): continue
        train.append({'input':grid,'output':output}); seen.add(key); survivors=remaining
    if len(train)!=demos or survivors != [chosen]:
        raise RuntimeError(f'insufficient distinguishing demonstrations within {max_attempts} candidates')
    while attempts < max_attempts and len(test)<queries:
        grid=_candidate(seed,attempts); attempts+=1
        key=_digest(grid)
        if key in seen: continue
        seen.add(key); test.append({'input':grid,'output':transform(grid,chosen)})
    if len(test)!=queries:
        raise RuntimeError(f'could not draw {queries} distinct queries within {max_attempts} candidates')
    episode={'schema':'component-parametric-proposal-v1','task_id':TASK_ID,'seed':seed,
             'settings':chosen,'train':train,'test':test,'program_solution':program(chosen),
             'program_sha256':hashlib.sha256(program(chosen).encode()).hexdigest(),
             'sampling':{'candidate_count':attempts,'max_attempts':max_attempts}}
    episode['certificate']=certify(episode)
    return episode


class RacketRunner:
    """One live protected bridge for a bounded batch; never a Python fallback."""
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge=RacketBridge()
        self.identity=self.bridge.runtime_identity
        if self.identity.get('backend')!='racket' or self.identity.get('protected') is not True:
            self.bridge.close()
            raise RuntimeError('live protected Racket backend required')
        self.cache={}
        return self

    def __call__(self, source, grid):
        from puzzle_generators.rule_wrap import wrap_rule
        _grid(grid)
        if source not in self.cache: self.cache[source]=wrap_rule(source)
        literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
        return self.bridge.eval_text(f'({self.cache[source]} {literal})')

    def __exit__(self,*exc):
        self.bridge.close()


def source_hashes():
    paths=[HERE/'components.py',HERE/'adapter.py',HERE/'promotion.json',
           HERE.parents[1]/'generator.py',REPO/'shared/data/canonical/puzzles.jsonl',
           REPO/'shared/runtime/reviewer_support.py',
           REPO/'shared/runtime/arc_repl/racket_bridge.py',
           REPO/'shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt',
           REPO/'shared/runtime/puzzle_generators/rule_wrap.py']
    return {str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def write_batch(episodes, destination, *, metadata=None):
    """Serialize public projection without executing or trusting private fields.

    CLI certifies before calling. This writer itself makes no label-validity claim.
    Public paths/order/content depend only on visible bytes; private mapping stays
    in private.json. Duplicate visible challenges and existing roots are refused.
    """
    destination=Path(destination)
    rows=sorted(((public_challenge_id(ep),public_challenge_bytes(ep),ep) for ep in episodes), key=lambda row: row[0])
    if not rows or len({r[0] for r in rows}) != len(rows):
        raise ValueError('batch must be nonempty with distinct visible challenges')
    if destination.exists(): raise FileExistsError(destination)
    destination.mkdir(parents=True)
    public=destination/'public'; public.mkdir()
    for identifier,body,_ in rows: (public/f'{identifier}.json').write_bytes(body)
    (destination/'public.jsonl').write_bytes(b''.join(body for _,body,_ in rows))
    private={'schema':'component-parametric-evidence-v1','status':'prototype_proposed',
             'source_sha256':source_hashes(),'metadata':metadata or {},
             'episodes':[dict(ep,public_id=identifier) for identifier,_,ep in rows]}
    (destination/'private.json').write_text(json.dumps(private,sort_keys=True,separators=(',',':'))+'\n')
    files=[destination/'public.jsonl',destination/'private.json']+sorted(public.iterdir())
    manifest={'schema':'component-parametric-export-v1','public_ids':[r[0] for r in rows],
              'writer_executes_racket':False,
              'files':{str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (destination/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,action='append',dest='seeds')
    parser.add_argument('--min-size',type=int,default=2,choices=[2,3,4])
    parser.add_argument('--connectivity',type=int,default=4,choices=[4,8])
    parser.add_argument('--all-settings',action='store_true')
    parser.add_argument('--demos',type=int,default=3)
    parser.add_argument('--queries',type=int,default=4)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    settings=SETTINGS if args.all_settings else [dict(min_size=args.min_size,connectivity=args.connectivity)]
    episodes=[]
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0]:
                ep=generate(seed,setting,args.demos,args.queries)
                ep['certificate']=certify(ep,execute)
                episodes.append(ep)
        metadata={'payload_argv':sys.argv,'runtime_identity':execute.identity,
                  'finite_scope':'six min_size/connectivity rules; no unrestricted-rule claim',
                  'qualification':'not_run','acceptance':'not_requested','training_admitted':False}
        manifest=write_batch(episodes,args.out,metadata=metadata)
    print(json.dumps({'status':'prototype_proposed','episodes':len(episodes),
                      'racket_checked_pairs':sum(len(e['train'])+len(e['test']) for e in episodes),
                      'queries':sum(len(e['test']) for e in episodes),
                      'public_ids':manifest['public_ids'],'out':str(args.out)},sort_keys=True))

if __name__=='__main__': main()
