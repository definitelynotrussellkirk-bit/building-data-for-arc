#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from reviewer_support import canonical_pairs, load_selected_generator

TASK = '73ab3e5ab7dc'

def component_sizes(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); sizes = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r,c) in seen:
                continue
            stack=[(r,c)]; seen.add((r,c)); n=0
            while stack:
                rr,cc=stack.pop(); n+=1
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr,nc=rr+dr,cc+dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr,nc) not in seen:
                        seen.add((nr,nc)); stack.append((nr,nc))
            sizes.append(n)
    return sorted(sizes, reverse=True)

def recolor_nonzero(grid, winner):
    return [[winner if v else 0 for v in row] for row in grid]

def summary(grid):
    counts=Counter(v for row in grid for v in row if v)
    return {
        str(c): {'global_count': counts[c], 'component_sizes': component_sizes(grid,c)}
        for c in sorted(counts)
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--apply', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    repo=Path(__file__).resolve().parents[3] / 'repo'
    gen, source, digest=load_selected_generator(TASK, root=repo)
    receipt=json.loads(Path(args.apply).read_text())
    result=receipt['results'][0]
    grid=result['input']; actual=result['output']
    stats=summary(grid)
    rival_winner=max((int(c) for c in stats), key=lambda c: (stats[str(c)]['component_sizes'][0], -c))
    rival=recolor_nonzero(grid, rival_winner)
    global_winner=max((int(c) for c in stats), key=lambda c: (stats[str(c)]['global_count'], -c))
    canonical=[]
    for pair in canonical_pairs(TASK, root=repo):
        s=summary(pair['input'])
        if any(len(v['component_sizes']) > 1 for v in s.values()):
            canonical.append({
                'split': pair['split'], 'pair_index': pair['pair_index'],
                'input_statistics': s,
                'input': pair['input'], 'output': pair['output'],
            })
    report={
        'task_id': TASK,
        'origin': 'constructed adversarial input; no generator seed/sample/overrides',
        'generator_path': str(source.relative_to(repo)),
        'generator_sha256': digest,
        'executed_rule_hash': receipt['executed_rule_hash'],
        'rule_text_sha256': receipt['rule_text_sha256'],
        'finding': 'The selected generator requires one component per color, but the authoritative rule is global frequency and canonical examples include split colors.',
        'rival_name': 'largest_single_component_wins',
        'rival_definition': 'Choose the color whose largest 4-connected component is largest; recolor every nonzero cell to it.',
        'input': grid,
        'input_statistics': stats,
        'global_frequency_winner': global_winner,
        'largest_component_winner': rival_winner,
        'authoritative_output': actual,
        'rival_output': rival,
        'outputs_disagree': actual != rival,
        'generator_self_check': gen.self_check(grid),
        'apply_generator_domain': result['generator_domain'],
        'canonical_split_color_examples': canonical,
        'source_receipt': str(Path(args.apply)),
        'racket_command': receipt['command'],
        'racket_cwd': receipt['cwd'],
        'builder_command': ['python3', '../checks/audit/73ab3e5ab7dc/build_counterexample.py', '--apply', args.apply, '--out', args.out],
        'builder_cwd': str(Path.cwd()),
    }
    assert global_winner == 2 and rival_winner == 3
    assert actual == recolor_nonzero(grid, global_winner)
    assert actual != rival
    assert report['generator_self_check']
    assert canonical
    out=Path(args.out)
    if out.exists(): raise SystemExit(f'refusing to overwrite {out}')
    out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({
        'task_id': TASK,
        'generator_sha256': digest,
        'executed_rule_hash': receipt['executed_rule_hash'],
        'global_frequency_winner': global_winner,
        'largest_component_winner': rival_winner,
        'outputs_disagree': actual != rival,
        'generator_self_check': report['generator_self_check'],
        'canonical_split_examples': len(canonical),
    }, indent=2))

if __name__=='__main__': main()
