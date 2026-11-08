#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID = '1bfb2ef9ca71'

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args=ap.parse_args()
    gen, source, sha = load_selected_generator(TASK_ID, root=find_root(__file__))
    seed, sample_index, band = 731, 1, 'medium'
    grid=gen.generate(seed, sample_index, difficulty=band)
    analysis=gen._analyze(grid)
    assert gen.self_check(grid)==[]
    assert gen.SEMANTIC_WITNESSES['non_three_height'](grid)
    payload={
      'task_id': TASK_ID,
      'generator_sha256': sha,
      'seed': seed,
      'sample_index': sample_index,
      'difficulty': band,
      'input': grid,
      'analysis': {
        'shape': [len(grid), len(grid[0])],
        'boxes': analysis['boxes'],
        'orientations': analysis['orientations'],
      },
      'python_intended_output': gen.rule_mirror(grid),
      'fixed_height_three_output': gen.CANONICAL_SHORTCUTS['fixed_height_three'](grid),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'source': str(source), 'sha': sha, 'out': str(args.out)}))
    return 0
if __name__=='__main__':
    raise SystemExit(main())
