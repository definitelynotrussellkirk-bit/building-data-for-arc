"""Proposed episode-fixed shear variants; never selects or approves production code.

Run through WORK/run_with_racket.py. Only the standard library and the packet's
reviewer_support / protected RacketBridge are required.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = '4326f5c2ded0'
CANONICAL_RULE_HASH = '884d94dde3d6'
DIRECTIONS = ('left', 'right')
STRIDES = (1, 2)
SHORTCUTS = ('identity', 'rigid_shift', 'canvas_bottom', 'top_anchor',
             'component_bottom', 'color_bottom', 'occupied_row_rank',
             'wrap', 'clamp', 'single_color', 'retain_source')


@dataclass(frozen=True)
class Settings:
    direction: str = 'left'
    stride: int = 1

    def __post_init__(self):
        if type(self.direction) is not str or self.direction not in DIRECTIONS:
            raise ValueError('direction must be left or right')
        if type(self.stride) is not int or self.stride not in STRIDES:
            raise ValueError('stride must be the exact integer 1 or 2')

    @property
    def step(self):
        return self.stride * (-1 if self.direction == 'left' else 1)


def _cells(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError('grid must have 1..30 rows')
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid must have 1..30 columns')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('grid must be rectangular with exact integer colors 0..9')
    cells = [(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    if not cells:
        raise ValueError('the bottommost occupied row is undefined for an empty foreground')
    return cells


def apply_python(grid, settings=Settings()):
    """Independent local comparison only; published labels come from Racket."""
    if not isinstance(settings, Settings):
        raise ValueError('settings must be Settings')
    cells = _cells(grid)
    bottom = max(r for r,_,_ in cells)
    width = len(grid[0])
    output = [[0] * width for _ in grid]
    for r,c,v in cells:
        target = c + settings.step * (bottom-r)
        if 0 <= target < width:
            output[r][target] = v
    return output


@lru_cache(maxsize=1)
def _canonical_program():
    ledger = find_root(__file__) / 'shared/data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    programs = {row['program_solution'] for row in rows if row.get('task_id') == TASK_ID}
    if len(programs) != 1:
        raise ValueError('expected one unambiguous canonical shear program')
    program = programs.pop()
    if hashlib.sha256(' '.join(program.split()).encode()).hexdigest()[:12] != CANONICAL_RULE_HASH:
        raise ValueError('canonical authority changed; review the prototype before reusing it')
    return program


def rule_program(settings=Settings()):
    """Default is the exact canonical text; variants change only displacement."""
    if not isinstance(settings, Settings):
        raise ValueError('settings must be Settings')
    original = _canonical_program()
    if settings == Settings():
        return original
    old = '(new-c (- cc (- max-r cr)))'
    if original.count(old) != 1:
        raise ValueError('canonical displacement location changed')
    return original.replace(old, f'(new-c (+ cc (* {settings.step} (- max-r cr))))')


def racket_labels(inputs, settings, bridge):
    """Execute every requested label through the protected, persistent bridge."""
    program = rule_program(settings)
    if not program.startswith('(rule! ') or not program.endswith(')'):
        raise ValueError('expected a rule! wrapper around a lambda')
    bridge.eval_text('(define __parametric_shear ' + program[7:-1] + ')')
    outputs = []
    for grid in inputs:
        expected = apply_python(grid, settings)
        bridge.define_grid('__shear_input', grid)
        actual = bridge.eval_text('(__parametric_shear __shear_input)')
        if actual != expected:
            raise RuntimeError('Racket/Python shear mismatch; no label fallback is permitted')
        outputs.append(actual)
    return outputs


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')


def _diagnostic(rng, height, width):
    grid = [[0]*width for _ in range(height)]
    colors = rng.sample(range(1,10), 7)
    mid = width//2
    # Unique interior markers identify all four settings. Edge points expose
    # clipping/clamping; blank bottom rows and a row gap expose wrong anchors.
    locations = [(1,0), (1,width-1), (3,mid), (4,mid),
                 (4,0), (4,width-1), (5,mid)]
    for (r,c),color in zip(locations,colors):
        grid[r][c] = color
    return grid


def _scene(rng, height, width, profile):
    grid = [[0]*width for _ in range(height)]
    colors = rng.sample(range(1,10),4)
    bottom = height-2
    mid = width//2
    if profile == 'long_span':
        # Occupied height grows with the canvas; this is not empty padding.
        for r in range(1,bottom+1):
            grid[r][mid] = colors[(r//3)%3]
        for r in (1,bottom//2,bottom):
            grid[r][min(width-1,mid+2)] = colors[3]
    elif profile == 'outline':
        top = rng.randint(1,min(3,bottom-3))
        left = rng.randint(1,max(1,width-6))
        right = min(width-2,left+rng.randint(3,5))
        for r in range(top,bottom+1):
            for c in range(left,right+1):
                if r in (top,bottom) or c in (left,right):
                    grid[r][c] = colors[0]
        grid[bottom][width-1] = colors[1]
    elif profile == 'objects':
        for top,left,color in ((1,1,colors[0]), (max(4,bottom-2),width-4,colors[1])):
            for r in (top,top+1):
                for c in (left,left+1):
                    grid[r][c] = color
        grid[bottom][mid] = colors[2]
    elif profile == 'edges':
        for r in sorted({1,3,bottom-1,bottom}):
            for c in (0,1,mid,width-2,width-1):
                grid[r][c] = rng.choice(colors)
    else:  # disconnected, multicolor, widely separated rows
        for r in sorted({1,3,bottom-2,bottom}):
            for c in rng.sample(range(width),3):
                grid[r][c] = rng.choice(colors)
    return grid


def sample_inputs(seed, *, n_train=3, n_test=4, height=None, width=None):
    """Deterministic unique grids; dimensions/counts never select the rule."""
    if type(seed) is not int:
        raise ValueError('seed must be an exact integer')
    _integer('n_train',n_train,1,16)
    _integer('n_test',n_test,1,16)
    if height is not None:
        _integer('height',height,8,30)
    if width is not None:
        _integer('width',width,9,30)
    rng = random.Random(seed)
    samples = {'train':[], 'test':[]}
    seen = set()
    query_sizes = ((30,30),(24,27),(27,21),(12,19))
    profiles = ('long_span','objects','edges','gaps','outline')
    for role,count in (('train',n_train),('test',n_test)):
        for index in range(count):
            if role == 'train':
                h,w = rng.randint(8,18),rng.randint(9,20)
            else:
                h,w = query_sizes[index % len(query_sizes)]
            h,w = height if height is not None else h, width if width is not None else w
            for _attempt in range(256):
                grid = (_diagnostic(rng,h,w) if role == 'train' and index == 0 else
                        _scene(rng,h,w,profiles[index % len(profiles)]))
                key = tuple(map(tuple,grid))
                if key not in seen:
                    seen.add(key)
                    samples[role].append(grid)
                    break
            else:
                raise RuntimeError('distinct input sampling exhausted its 256-attempt budget')
    return samples


def _component_bottoms(cells):
    remaining = {(r,c) for r,c,_ in cells}
    bottoms = {}
    while remaining:
        start = min(remaining)
        group, stack = {start},[start]
        remaining.remove(start)
        while stack:
            r,c = stack.pop()
            for neighbor in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    group.add(neighbor)
                    stack.append(neighbor)
        bottom = max(r for r,_ in group)
        bottoms.update({cell:bottom for cell in group})
    return bottoms


def _shortcut(grid, settings, name):
    cells = _cells(grid)
    if name == 'identity':
        return [row[:] for row in grid]
    height,width = len(grid),len(grid[0])
    bottom,top = max(r for r,_,_ in cells),min(r for r,_,_ in cells)
    components = _component_bottoms(cells) if name == 'component_bottom' else {}
    by_color = {v:max(r for r,_,color in cells if color == v) for _,_,v in cells} if name == 'color_bottom' else {}
    occupied = sorted({r for r,_,_ in cells})
    first_color = min(v for _,_,v in cells)
    output = [row[:] for row in grid] if name == 'retain_source' else [[0]*width for _ in grid]
    for r,c,v in cells:
        distance = bottom-r
        if name == 'rigid_shift': distance = 1
        elif name == 'canvas_bottom': distance = height-1-r
        elif name == 'top_anchor': distance = r-top
        elif name == 'component_bottom': distance = components[(r,c)]-r
        elif name == 'color_bottom': distance = by_color[v]-r
        elif name == 'occupied_row_rank': distance = len(occupied)-1-occupied.index(r)
        elif name == 'single_color' and v != first_color: distance = 0
        target = c+settings.step*distance
        if name == 'wrap': target %= width
        elif name == 'clamp': target = min(width-1,max(0,target))
        if 0 <= target < width:
            output[r][target] = v
    return output


def lesson_audit(episode, settings):
    """Finite declared-rival audit. Only demonstration labels select survivors."""
    train,test = episode.get('train'),episode.get('test')
    if not isinstance(train,list) or not train or not isinstance(test,list) or not test:
        raise ValueError('lesson audit needs nonempty train and test lists')
    alternatives = [Settings(d,s) for d in DIRECTIONS for s in STRIDES]
    survivors,shortcuts,functions = [],[],[]
    for candidate in alternatives:
        if all(apply_python(pair['input'],candidate) == pair['output'] for pair in train):
            survivors.append(asdict(candidate))
            functions.append((f'parameter:{candidate.direction}:{candidate.stride}',
                              lambda grid,p=candidate:apply_python(grid,p)))
    for name in SHORTCUTS:
        if all(_shortcut(pair['input'],settings,name) == pair['output'] for pair in train):
            shortcuts.append(name)
            functions.append((name,lambda grid,n=name:_shortcut(grid,settings,n)))
    ambiguities = []
    for index,pair in enumerate(test):
        disagree = [name for name,fn in functions if fn(pair['input']) != pair['output']]
        if disagree:
            ambiguities.append({'query_index':index,'surviving_rivals':disagree})
    return {'scope':'four parameter settings and eleven explicitly declared shortcuts; not completeness',
            'selection_uses':'demonstration inputs and outputs only',
            'declared_shortcuts':list(SHORTCUTS), 'surviving_parameters':survivors,
            'surviving_shortcuts':shortcuts,'query_ambiguities':ambiguities,
            'identifiable':asdict(settings) in survivors and not ambiguities}


def build_episode(seed, *, settings=None, n_train=3, n_test=4, height=None, width=None, bridge=None):
    samples = sample_inputs(seed,n_train=n_train,n_test=n_test,height=height,width=width)
    if settings is None:
        setting_rng = random.Random(f'shear-setting:{seed}')
        settings = Settings(setting_rng.choice(DIRECTIONS),setting_rng.choice(STRIDES))
    if not isinstance(settings,Settings):
        raise ValueError('settings must be Settings or None')
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge(timeout=10,startup_timeout=60) as owned:
            return build_episode(seed,settings=settings,n_train=n_train,n_test=n_test,
                                 height=height,width=width,bridge=owned)
    inputs = samples['train']+samples['test']
    outputs = racket_labels(inputs,settings,bridge)
    pairs = [{'input':grid,'output':output} for grid,output in zip(inputs,outputs)]
    episode = {'train':pairs[:n_train],'test':pairs[n_train:]}
    audit = lesson_audit(episode,settings)
    if not audit['identifiable']:
        raise RuntimeError('demonstrations leave a declared rival that changes a query answer')
    program = rule_program(settings)
    episode['metadata'] = {'status':'proposed_prototype','task_id':TASK_ID,'seed':seed,
        'parameters':asdict(settings),'training_admitted':False,
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'reference':{'program':program,'sha256':hashlib.sha256(program.encode()).hexdigest(),
                     'canonical_rule_hash':CANONICAL_RULE_HASH},
        'labels':{'backend':'racket','pairs_executed':len(inputs),'python_agreement':True},
        'lesson_audit':audit}
    return episode


def write_batch(episodes, out):
    """Write visible-only opaque names plus separate private records.

    This is a projection writer, not a label validator. The CLI supplies only
    build_episode results, whose labels have already executed in Racket.
    """
    if not episodes:
        raise ValueError('batch must contain at least one episode')
    rows = []
    seen = set()
    for episode in episodes:
        visible = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        if identifier in seen:
            raise ValueError('duplicate visible public payload')
        seen.add(identifier)
        private = (json.dumps(episode,sort_keys=True,separators=(',',':'))+'\n').encode()
        rows.append((identifier,visible,private))
    rows.sort(key=lambda row:row[0])
    out = Path(out)
    out.mkdir(parents=True,exist_ok=False)
    (out/'public').mkdir()
    (out/'private').mkdir()
    for identifier,visible,private in rows:
        (out/'public'/f'{identifier}.json').write_bytes(visible)
        (out/'private'/f'{identifier}.json').write_bytes(private)
    receipt = {'schema':'arcpuzzles-shear-prototype-batch-v1','status':'proposed',
               'episodes':len(rows),'public_ids':[row[0] for row in rows],
               'public_name_basis':'SHA-256 of the exact visible bytes written',
               'training_admitted':False}
    (out/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=17)
    parser.add_argument('--count',type=int,default=1,help='episodes per setting')
    parser.add_argument('--train',type=int,default=3)
    parser.add_argument('--test',type=int,default=4)
    parser.add_argument('--height',type=int)
    parser.add_argument('--width',type=int)
    parser.add_argument('--direction',choices=DIRECTIONS,default='left')
    parser.add_argument('--stride',type=int,choices=STRIDES,default=1)
    parser.add_argument('--all-settings',action='store_true')
    args = parser.parse_args()
    _integer('count',args.count,1,16)
    settings = ([Settings(d,s) for d in DIRECTIONS for s in STRIDES] if args.all_settings else
                [Settings(args.direction,args.stride)])
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=10,startup_timeout=60) as bridge:
        episodes = [build_episode(args.seed+i,settings=setting,n_train=args.train,n_test=args.test,
                                 height=args.height,width=args.width,bridge=bridge)
                    for setting in settings for i in range(args.count)]
    print(json.dumps(write_batch(episodes,args.out),sort_keys=True))


if __name__ == '__main__':
    main()
