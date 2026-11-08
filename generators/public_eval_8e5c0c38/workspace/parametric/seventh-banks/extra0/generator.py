"""Public ARC 8e5c0c38: restore per-color vertical symmetry by trimming noise.

Inputs only; private Python claims are independently re-executed through Racket.
No original task data or answer is imported by this sampler or its solver.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from puzzle_generators.base import gen_ctx

GENERATOR_ID = 'public_eval_8e5c0c38'
TASK_ID = GENERATOR_ID
VERSION = '1.0.0'
SUMMARY = 'Infer each color silhouette\'s best vertical mirror axis and remove unmatched pixels.'
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
INVARIANTS = ['unique modal background', 'one silhouette per foreground color',
              'asymmetric additions to nontrivial vertically symmetric cores',
              'input-derived axes rather than canvas or noisy-bbox centers']
AXES = {'scene_profile': {'type':'str', 'default':'mixed', 'valid':'compact|ordinary|stress'}}


def validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError('grid must have 1..30 rows')
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid must have 1..30 columns')
    w = len(grid[0])
    if any(type(row) is not list or len(row) != w or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('rectangular exact-integer ARC grid required')


def analyze(grid):
    """Infer background, then each color's maximum-overlap doubled axis.

    The smallest color resolves a modal-color tie; the smallest doubled column
    resolves an overlap tie. Ordinary generation requires a unique background.
    Grouping by color, not connectivity, preserves diagonally/disconnected parts.
    """
    validate_grid(grid)
    counts = Counter(v for row in grid for v in row)
    bg = min(counts, key=lambda v: (-counts[v], v))
    groups = []
    for color in sorted(set(counts) - {bg}):
        cells = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color}
        r0,r1 = min(r for r,c in cells), max(r for r,c in cells)
        c0,c1 = min(c for r,c in cells), max(c for r,c in cells)
        scores = {k: sum((r,k-c) in cells for r,c in cells) for k in range(2*c0, 2*c1+1)}
        axis = min(scores, key=lambda k: (-scores[k], k))
        groups.append({'color':color, 'cells':cells, 'axis2':axis,
                       'bbox':(r0,c0,r1,c1), 'score':scores[axis],
                       'maximizers':[k for k in scores if scores[k] == scores[axis]]})
    return bg, groups


def solve(grid, action='trim', *, axis_rule='best', only_largest=False):
    if action not in ('trim','complete'):
        raise ValueError('unknown symmetry action')
    bg, groups = analyze(grid)
    out = deepcopy(grid)
    if only_largest and groups:
        groups = [max(groups, key=lambda x:len(x['cells']))]
    for group in groups:
        cells, col = group['cells'], group['color']
        axis = group['axis2']
        if axis_rule == 'bbox': axis = group['bbox'][1] + group['bbox'][3]
        elif axis_rule == 'canvas': axis = len(grid[0])-1
        elif axis_rule == 'rightmost': axis = max(group['maximizers'])
        elif axis_rule != 'best': raise ValueError('unknown axis rule')
        if action == 'trim':
            for r,c in cells:
                if (r,axis-c) not in cells: out[r][c] = bg
        else:
            for r,c in cells:
                target = axis-c
                if 0 <= target < len(grid[0]) and grid[r][target] == bg:
                    out[r][target] = col
    return out


def _patch(rng, height, width):
    """Bounded random mirrored cores plus one-sided noise, all inside a slot."""
    sh, sw = height-2, width-2
    target = sw+1
    for _ in range(160):
        core = set()
        for r in range(1, sh+1):
            for c in range(1, (sw+1)//2+1):
                if rng.random() < 0.43:
                    core.update(((r,c),(r,target-c)))
        # A varying connected backbone and two extremes create real silhouettes.
        backbone = rng.randrange(1, sh+1)
        core.update((backbone,c) for c in range(1, sw+1))
        core.update(((1,1),(1,sw),(sh,1),(sh,sw)))
        candidates = [(r,c) for r in range(height) for c in range(width)
                      if (r,c) not in core and (r,target-c) not in core]
        rng.shuffle(candidates)
        # One deliberately asymmetric outer-column noise cell makes bbox
        # centering a wrong rule, not an accidentally sufficient surrogate.
        noise = {(rng.randrange(1, sh+1),0)}
        target_noise = rng.randint(2, max(3, (sh*sw)//12))
        for p in candidates:
            if len(noise) >= target_noise: break
            if p[1] == width-1 or (p[0],target-p[1]) in noise: continue
            noise.add(p)
        cells = core | noise
        scores = [sum((r,k-c) in cells for r,c in cells) for k in range(2*width-1)]
        if scores[target] == len(core) and scores.count(max(scores)) == 1 and max(scores) == len(core):
            return cells
    raise RuntimeError('bounded symmetry-core construction exhausted')


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise TypeError('seed and nonnegative sample_index must be exact integers')
    if difficulty not in (None,'easy','medium','hard'):
        raise ValueError('unknown difficulty')
    if set(overrides)-set(AXES): raise ValueError('unknown override')
    profile = overrides.get('scene_profile')
    if profile is not None and profile not in ('compact','ordinary','stress'):
        raise ValueError('unknown scene_profile')
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    choices = ['stress'] if sample_index == 103 else ['compact','ordinary']
    profile = ctx.draw_choice('scene_profile', choices) if profile is None else ctx.draw_choice('scene_profile',[profile])
    rng = ctx.draw_rng('geometry')
    bg = ctx.draw_choice('background', list(range(10)))
    palette = [c for c in range(10) if c != bg]
    rng.shuffle(palette)
    if profile == 'stress':
        h = w = 30
        slots = [(0,0,14,14),(0,16,14,14),(16,0,14,14),(16,16,14,14)]
    else:
        h = rng.randint(17,22) if profile == 'compact' else rng.randint(23,29)
        w = rng.randint(18,23) if profile == 'compact' else rng.randint(24,29)
        hh,ww = (h-2)//2,(w-2)//2
        slots = [(0,0,hh,ww),(0,w-ww,hh,ww),(h-hh,0,hh,ww),(h-hh,w-ww,hh,ww)]
        rng.shuffle(slots)
        slots = slots[:rng.choice([2,3,4])]
    grid = [[bg]*w for _ in range(h)]
    for (r0,c0,ph,pw), color in zip(slots,palette):
        # Keep geometry independent of the episode's hidden action.
        for r,c in _patch(rng, ph, pw): grid[r0+r][c0+c] = color
    errors = self_check(grid)
    if errors: raise RuntimeError('; '.join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    try:
        bg, groups = analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    counts = Counter(v for row in grid for v in row)
    errors=[]
    if sum(n == counts[bg] for n in counts.values()) != 1: errors.append('background is not unique')
    if not 2 <= len(groups) <= 4: errors.append('expected 2..4 color groups')
    for group in groups:
        if len(group['maximizers']) != 1: errors.append('ambiguous generated symmetry axis')
        if not 4 <= group['score'] < len(group['cells']): errors.append('no nontrivial noisy core')
        if group['axis2'] == group['bbox'][1]+group['bbox'][3]: errors.append('bbox shortcut not separated')
        for r,c in group['cells']:
            cc = group['axis2']-c
            if not 0 <= cc < len(grid[0]): errors.append('completion would leave canvas')
            elif grid[r][cc] not in (bg, group['color']): errors.append('completion color collision')
    return errors


rule_mirror = solve
strict_canonical_like = self_check

RULE_TASK_ID='ee_8e5c0c38'
