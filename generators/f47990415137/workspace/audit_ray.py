"""Find a ray-legend audit witness; validate retained candidates with public Racket commands.

No audit target is edited. This independent Python mirror selects hypotheses only.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def ray_mirror(grid, numeric=False):
    legend = [x for x in grid[0] if x]
    field = grid[1:]; h, w = len(field), len(field[0])
    emitters = []
    for c in range(w):
        for r,dr in ((0,1),(h-1,-1)):
            if field[r][c] not in (0,5): emitters.append((r,c,field[r][c],dr,0))
    for r in range(1,h-1):
        for c,dc in ((0,1),(w-1,-1)):
            if field[r][c] not in (0,5): emitters.append((r,c,field[r][c],0,dc))
    out = [[5 if v == 5 else 0 for v in row] for row in field]
    proposals = {}
    for r,c,color,dr,dc in emitters:
        out[r][c] = color
        r += dr; c += dc
        while 0 <= r < h and 0 <= c < w and field[r][c] != 5:
            proposals.setdefault((r,c),[]).append(color)
            r += dr; c += dc
    for (r,c),colors in proposals.items():
        if out[r][c] == 0:
            out[r][c] = max(colors, key=(lambda color:color) if numeric else legend.index)
    return out


def main():
    from reviewer_support import find_root
    root = find_root(__file__)
    path = root/'generators/311ebe067559/generator.py'
    spec=importlib.util.spec_from_file_location('audit_ray_target', path)
    gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
    destination=Path(sys.argv[1]); destination.mkdir(parents=True,exist_ok=True)
    overrides={'grid_h':14,'grid_w':16,'palette_size':2,'n_distinct_colors':2}
    ordinary=gen.generate(17,9,difficulty='medium')
    controlled=gen.generate(17,9,difficulty='medium',**overrides)
    witness=None
    for seed in range(100):
        grids=[gen.generate(seed,i,difficulty='medium') for i in range(4)]
        matches=[ray_mirror(g) == ray_mirror(g,numeric=True) for g in grids]
        if matches == [True,True,True,False]:
            witness={'seed':seed,'sample_indices':[0,1,2,3], 'difficulty':'medium',
                     'numeric_rival_matches':matches,'inputs':grids,
                     'python_mirror_outputs':[ray_mirror(g) for g in grids],
                     'rival_outputs':[ray_mirror(g,numeric=True) for g in grids]}
            break
    if witness is None: raise RuntimeError('No witness in bounded seed range 0..99')
    report={'task_id':gen.TASK_ID, 'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'declared_rule_hash':gen.RULE_HASH,
            'override_counterexample':{'seed':17,'sample_index':9,'difficulty':'medium',
                 'overrides':overrides,'observed_h':len(controlled),'observed_w':len(controlled[0]),
                 'observed_palette_size_including_background':len(set(sum(controlled,[]))),
                 'unchanged_by_all_overrides':ordinary==controlled,
                 'self_check':gen.self_check(controlled),'input':controlled},
            'conditional_legend_rival_candidate':witness,
            'verification':'Python candidate only; see supported apply/generate evidence before asserting Racket parity.'}
    (destination/'candidate.json').write_text(json.dumps(report,indent=2)+'\n')
    (destination/'input.json').write_text(json.dumps(witness['inputs']+[controlled])+'\n')
    print(json.dumps({'seed':witness['seed'], 'override_observed_shape':[len(controlled),len(controlled[0])],
                     'overrides_ignored':ordinary==controlled}))


if __name__=='__main__':main()
