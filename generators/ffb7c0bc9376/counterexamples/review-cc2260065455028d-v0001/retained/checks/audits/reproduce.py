"""Findings-only, deterministic reproduction for the two immutable audit draws.

From packet root:
  python3 run_with_racket.py python3 ../checks/audits/reproduce.py \
      --repo . --out ../checks/audits/replayed --per-band 1000
Audit sources and canonical authorities are never edited.
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

IDS = ['69fcc82f9e3c', 'ffb7c0bc9376']


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def colors(grid):
    found = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                found.setdefault(color, []).append((r, c))
    return found


def components(grid):
    used, result = set(), []
    for color, cells in colors(grid).items():
        available = set(cells)
        for start in cells:
            if start in used:
                continue
            used.add(start)
            queue = deque([start])
            part = []
            while queue:
                r, c = queue.popleft()
                part.append((r, c))
                for q in [(r-1,c), (r+1,c), (r,c-1), (r,c+1)]:
                    if q in available and q not in used:
                        used.add(q)
                        queue.append(q)
            result.append((color, part))
    return result


def bbox(cells):
    return min(r for r,c in cells), min(c for r,c in cells), max(r for r,c in cells), max(c for r,c in cells)


def overlaps(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def mirror_parts(grid, per_color=False):
    groups = list(colors(grid).items()) if per_color else components(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for color, cells in groups:
        r1,c1,r2,c2 = bbox(cells)
        for r,c in cells:
            output[r][c1+c2-c] = color
    return output


def segments(grid):
    result, decoys = [], []
    for color, pair in colors(grid).items():
        if len(pair) != 2:
            continue
        (r1,c1),(r2,c2) = pair
        if r1 == r2:
            result.append((color, {(r1,c) for c in range(min(c1,c2),max(c1,c2)+1)}))
        elif c1 == c2:
            result.append((color, {(r,c1) for r in range(min(r1,r2),max(r1,r2)+1)}))
        else:
            decoys.extend((color, r,c) for r,c in pair)
    return result, decoys


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--per-band', type=int, default=1000)
    args = parser.parse_args()
    if args.per_band < 1 or args.out.exists():
        parser.error('positive sample count and a fresh output directory required')
    repo = args.repo.resolve()
    args.out.mkdir(parents=True)
    sys.path.insert(0, str(repo/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    report = {'schema': 'arcpuzzles-two-drawn-audits-v1', 'per_band': args.per_band,
              'sample_protocol': 'seed=0..per_band-1; sample_index=0; all three bands',
              'findings_only': True, 'tasks': {}}
    with tempfile.TemporaryDirectory(prefix='portal-review-audits-') as tmp:
        runtime = Path(tmp)
        prepare_runtime(Catalog(repo), runtime, task_ids=IDS)
        sys.path.insert(0,str(runtime))
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        from scripts.coder_synth_verify import _as_pairs, _norm_grid
        rows = {row['task_id']: row for row in (json.loads(line) for line in (runtime/'data/canonical/puzzles.jsonl').read_text().splitlines()) if row['task_id'] in IDS}
        bridge = RacketBridge()
        try:
            for task in IDS:
                path = repo/f'generators/{task}/generator.py'
                module = load(path, 'audit_'+task)
                code = rows[task]['program_solution']
                info = {'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'canonical_program_sha256': hashlib.sha256(code.encode()).hexdigest(),
                        'canonical_rule_hash': hashlib.sha256(' '.join(code.split()).encode()).hexdigest()[:12],
                        'version': module.VERSION,
                        'counts': {}, 'examples': {}, 'canonical': []}
                count = Counter()
                bridge.eval_text(f'(define __audit_rule {wrap_rule(code)})')
                def oracle(grid):
                    bridge.define_grid('__audit_input', grid)
                    return bridge.eval_text('(__audit_rule __audit_input)')
                def witness(name, grid, output, **meta):
                    if name not in info['examples']:
                        value = dict(input=grid, output=output, self_check=module.self_check(grid), **meta)
                        filename = task+'-'+name+'.json'
                        write(args.out/filename,value)
                        info['examples'][name] = filename
                for split in ('train','test'):
                    for index,pair in enumerate(_as_pairs(rows[task].get(split))):
                        grid, expected = _norm_grid(pair['input']),_norm_grid(pair['output'])
                        output=oracle(grid)
                        errors=module.self_check(grid)
                        if output != expected:
                            raise AssertionError(f'{task} canonical {split}[{index}] Racket mismatch')
                        item=dict(split=split,index=index,racket_matches_canonical=True,self_check=errors)
                        if task == IDS[0]:
                            item['whole_color_bbox_rival_matches'] = mirror_parts(grid,per_color=True)==output
                        info['canonical'].append(item)
                        if errors:
                            witness('canonical-rejected',grid,output,split=split,index=index)
                if task == IDS[0]:
                    grid=[[0]*10 for _ in range(7)]
                    for r,c in [(1,1),(2,1),(2,2),(4,6),(4,7),(5,7)]:
                        grid[r][c]=2
                    output=oracle(grid)
                    rival=mirror_parts(grid,per_color=True)
                    assert mirror_parts(grid)==output and rival!=output
                    witness('same-color-components',grid,output,rival_output=rival,
                            rival='mirror all cells of a color in their combined bounding box')
                    blank=module.generate(0,0,texture='no_blobs')
                    output=oracle(blank)
                    assert blank==output and not module.self_check(blank)
                    witness('blank-accepted',blank,output,seed=0,sample_index=0,overrides={'texture':'no_blobs'})
                for band in ('easy','medium','hard'):
                    for seed in range(args.per_band):
                        grid=module.generate(seed,0,difficulty=band)
                        output=oracle(grid)
                        count['generated']+=1
                        count['self_check_rejections']+=bool(module.self_check(grid))
                        count['identity_outputs']+=output==grid
                        meta=dict(seed=seed,sample_index=0,difficulty=band)
                        if task==IDS[0]:
                            parts=components(grid)
                            boxes=[bbox(cells) for color,cells in parts]
                            intersect=[(i,j) for i in range(len(boxes)) for j in range(i+1,len(boxes)) if overlaps(boxes[i],boxes[j])]
                            count['overlapping_bounding_boxes']+=bool(intersect)
                            count['component_mirror_disagrees_with_racket']+=mirror_parts(grid)!=output
                            count['whole_color_rival_disagreements']+=mirror_parts(grid,per_color=True)!=output
                            if intersect:
                                witness('overlapping-bboxes',grid,output,boxes=boxes,overlap_indices=intersect,**meta)
                            if mirror_parts(grid)!=output:
                                witness('bbox-crop-contamination',grid,output,component_only_output=mirror_parts(grid),**meta)
                        else:
                            lines,decoys=segments(grid)
                            crossing=[{'colors':[a,b], 'cells': sorted(aa&bb)} for i,(a,aa) in enumerate(lines) for b,bb in lines[i+1:] if aa&bb]
                            clobbered=[dict(color=v,row=r,col=c,output_color=output[r][c]) for v,r,c in decoys if output[r][c]!=v]
                            count['crossing_segments']+=bool(crossing)
                            count['clobbered_non_aligned_decoys']+=bool(clobbered)
                            if crossing:
                                witness('crossing-segments',grid,output,crossings=crossing,**meta)
                            if clobbered:
                                witness('clobbered-decoys',grid,output,clobbered=clobbered,**meta)
                info['counts']=dict(count)
                report['tasks'][task]=info
                write(args.out/'report.json',report)
        finally:
            bridge.close()
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
