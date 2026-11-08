"""One bounded source-bound validation probe; run before and after the local repair."""
import hashlib
import json
from pathlib import Path
import sys

repo = Path.cwd()
sys.path.insert(0, str(repo / 'shared/runtime'))
from reviewer_support import load_selected_generator

gen, path, sha = load_selected_generator('7eaf2d73ca39', root=repo)
rows = [{'texture': texture, 'errors': gen.self_check(gen.generate(0, 0, texture=texture))}
        for texture in gen.DEGENERATE_TEXTURES]
defaults = [gen.generate(seed, 0, difficulty=difficulty)
            for difficulty in ('easy', 'medium', 'hard') for seed in range(8)]
rule_path = repo / 'shared/data/base/solutions/banks/765a70430bc9/M1__7eaf2d73ca39.json'
canonical_path = repo / 'shared/data/canonical/puzzles.jsonl'
canonical = next(json.loads(line) for line in canonical_path.read_text().splitlines()
                 if json.loads(line).get('task_id') == '7eaf2d73ca39')
print(json.dumps({'task_id': gen.TASK_ID, 'source_path': str(path.relative_to(repo)),
                  'generator_sha256': sha,
                  'base_authority_sha256': hashlib.sha256(rule_path.read_bytes()).hexdigest(),
                  'canonical_row_sha256': hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                  'degenerate_results': rows,
                  'default_draw_count': len(defaults),
                  'default_grids_sha256': hashlib.sha256(json.dumps(defaults, separators=(',', ':')).encode()).hexdigest(),
                  'default_validation_errors': [gen.self_check(grid) for grid in defaults]}, indent=2))
