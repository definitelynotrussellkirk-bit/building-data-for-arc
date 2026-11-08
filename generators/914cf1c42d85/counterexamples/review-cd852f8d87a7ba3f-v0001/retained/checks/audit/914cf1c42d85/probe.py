"""Reproduce the selected source's ordinary missing-shape outputs; no mutations."""
from pathlib import Path
from collections import Counter
import json
from reviewer_support import canonical_pairs, find_root, load_selected_generator

OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
EXPECTED_SHA = 'b3a4fbc6838bc051b5f6524f67d86820af3b079e87751acd2c854bc26a9e550d'
mod, source, sha = load_selected_generator('914cf1c42d85', root=ROOT)
assert sha == EXPECTED_SHA, (sha, EXPECTED_SHA)

def components(grid):
    seen, result = set(), []
    for r in range(1, len(grid)):
        for c, color in enumerate(grid[r]):
            if not color or (r,c) in seen:
                continue
            queue, cells = [(r,c)], []
            seen.add((r,c))
            while queue:
                a,b = queue.pop()
                cells.append((a,b))
                for x,y in [(a+1,b),(a-1,b),(a,b+1),(a,b-1)]:
                    if (1 <= x < len(grid) and 0 <= y < len(grid[0])
                            and grid[x][y] == color and (x,y) not in seen):
                        seen.add((x,y))
                        queue.append((x,y))
            result.append({'color':color, 'size':len(cells), 'cells':sorted(cells)})
    return sorted(result, key=lambda item:item['size'])

def recolor(grid, endpoint_rival=False):
    """Rank-loop mirror, or the canonical-consistent smallest/medium/largest rival."""
    palette = [v for v in grid[0] if v]
    items = components(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for rank,item in enumerate(items):
        index = len(palette)-1 if endpoint_rival and rank == len(items)-1 and rank else rank
        for r,c in item['cells']:
            output[r][c] = palette[index]
    return output

pairs = canonical_pairs('914cf1c42d85', root=ROOT)
canonical_checks = []
for pair in pairs:
    canonical_checks.append({
        'variant':pair['variant'], 'split':pair['split'], 'pair_index':pair['pair_index'],
        'sizes':[item['size'] for item in components(pair['input'])],
        'rank_mirror_matches':recolor(pair['input']) == pair['output'],
        'endpoint_rival_matches':recolor(pair['input'], True) == pair['output'],
    })
assert len(pairs) == 3 and all(p['rank_mirror_matches'] and p['endpoint_rival_matches'] for p in canonical_checks)

counts = {}
for difficulty in [None, 'easy', 'medium', 'hard']:
    sizes, validators = Counter(), Counter()
    for seed in range(1000):
        grid = mod.generate(seed, 0, difficulty=difficulty)
        sizes[str(tuple(item['size'] for item in components(grid)))] += 1
        validators[str(mod.self_check(grid, difficulty=difficulty))] += 1
    counts[str(difficulty)] = {'draws':1000, 'size_counts':dict(sizes), 'validator_counts':dict(validators)}
census = {'generator_sha256':sha, 'seed_range_inclusive':[0,999], 'sample_index':0,
          'overrides':{}, 'difficulty_counts':counts, 'total_draws':4000,
          'generation_exceptions':0, 'canonical_checks':canonical_checks}
(OUT/'census.json').write_text(json.dumps(census, indent=2)+'\n')

grid = mod.generate(0, 0, difficulty=None)
witness = {'generator_sha256':sha, 'seed':0, 'sample_index':0, 'difficulty':None,
           'overrides':{}, 'input':grid, 'body_components':components(grid),
           'validator_result':mod.self_check(grid), 'missing_size':4,
           'reference_rank_python_mirror':recolor(grid),
           'endpoint_rival_output':recolor(grid, True),
           'rival_description':'Smallest component gets first palette color; largest gets third; intermediate gets second.',
           'rival_canonical_matches':3, 'rival_canonical_total':3,
           'reference_output_status':'Python mirror; exact supported Racket receipt retained separately when available.'}
assert [item['size'] for item in witness['body_components']] == [1,2]
assert witness['validator_result'] == []
assert witness['reference_rank_python_mirror'] != witness['endpoint_rival_output']
(OUT/'finding.json').write_text(json.dumps(witness, indent=2)+'\n')
(OUT/'input.json').write_text(json.dumps(grid)+'\n')
(OUT/'rival_output.json').write_text(json.dumps(witness['endpoint_rival_output'])+'\n')
print(json.dumps({'generator_sha256':sha, 'census':counts, 'canonical_checks':canonical_checks,
                  'witness_sizes':[item['size'] for item in witness['body_components']],
                  'validator_result':witness['validator_result']}, indent=2))
