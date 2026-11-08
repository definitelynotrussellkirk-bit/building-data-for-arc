"""Finite executable shortcut audit. Python claims; Racket parity is separate."""
import argparse
from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_a251_audit_adapter', BASE/'adapter.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
C = A.CORE
RIVALS = ('all_templates', 'largest_template', 'smallest_template', 'largest_bbox',
          'first_template', 'last_template', 'minimum_marker', 'maximum_marker',
          'most_source_copies', 'least_source_copies', 'most_target_markers',
          'least_target_markers', 'weighted_source_area', 'bbox_top_left',
          'bbox_center', 'horizontal_reflection', 'vertical_reflection',
          'half_turn', 'one_template_for_all', 'opaque_bbox',
          'monochrome_payload', 'cardinal_template', 'crop_only')


def predictions(grid):
    source, target, templates, anchors = C.extract(grid)
    largest = max(t['size'] for t in templates.values())
    out = {'all_templates': C.paint(target, templates, anchors),
           'largest_template': C.paint(target, templates, anchors,
                                      {c for c,t in templates.items() if t['size'] == largest}),
           'crop_only': [row[:] for row in target['board']]}
    def selected(name, scores, maximum=True):
        best = (max if maximum else min)(scores.values())
        out[name] = C.paint(target, templates, anchors, {c for c,s in scores.items() if s == best})
    def bbox(t):
        rs = [r for r,c,v in t['mask']]; cs = [c for r,c,v in t['mask']]
        return min(rs), min(cs), max(rs), max(cs)
    selected('smallest_template', {c:t['size'] for c,t in templates.items()}, False)
    selected('largest_bbox', {c:(bbox(t)[2]-bbox(t)[0]+1)*(bbox(t)[3]-bbox(t)[1]+1) for c,t in templates.items()})
    selected('minimum_marker', {c:c for c in templates}, False)
    selected('maximum_marker', {c:c for c in templates})
    selected('most_source_copies', {c:t['copies'] for c,t in templates.items()})
    selected('least_source_copies', {c:t['copies'] for c,t in templates.items()}, False)
    target_counts = Counter(c for r,cc,c in anchors)
    selected('most_target_markers', dict(target_counts))
    selected('least_target_markers', dict(target_counts), False)
    selected('weighted_source_area', {c:t['copies']*t['size'] for c,t in templates.items()})
    out['first_template'] = C.paint(target, templates, anchors, {next(iter(templates))})
    out['last_template'] = C.paint(target, templates, anchors, {list(templates)[-1]})
    transforms = {
        'bbox_top_left': lambda r,c,b:(r-b[0],c-b[1]),
        'bbox_center': lambda r,c,b:(r-(b[0]+b[2])//2,c-(b[1]+b[3])//2),
        'horizontal_reflection': lambda r,c,b:(r,-c),
        'vertical_reflection': lambda r,c,b:(-r,c),
        'half_turn': lambda r,c,b:(-r,-c)}
    for name, fn in transforms.items():
        changed = deepcopy(templates)
        for color, t in changed.items():
            b = bbox(t)
            t['mask'] = [(*fn(r,c,b),v) for r,c,v in t['mask']]
        out[name] = C.paint(target, changed, anchors)
    first = next(iter(templates.values()))
    out['one_template_for_all'] = C.paint(target, {c:first for c in templates}, anchors)
    changed = deepcopy(templates)
    for t in changed.values():
        r0,c0,r1,c1 = bbox(t)
        values = {(r,c):v for r,c,v in t['mask']}
        t['mask'] = [(r,c,values.get((r,c),source['background'])) for r in range(r0,r1+1) for c in range(c0,c1+1)]
    out['opaque_bbox'] = C.paint(target, changed, anchors)
    changed = deepcopy(templates)
    for color,t in changed.items():
        dominant = C.mode(v for r,c,v in t['mask'] if (r,c)!=(0,0))
        t['mask'] = [(r,c, color if (r,c)==(0,0) else dominant) for r,c,v in t['mask']]
    out['monochrome_payload'] = C.paint(target, changed, anchors)
    changed = deepcopy(templates)
    for t in changed.values():
        points = {(r,c) for r,c,v in t['mask']}; seen={(0,0)}; queue=[(0,0)]
        for r,c in queue:
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in points and p not in seen:seen.add(p);queue.append(p)
        t['mask'] = [(r,c,v) for r,c,v in t['mask'] if (r,c) in seen]
    out['cardinal_template'] = C.paint(target, changed, anchors)
    assert set(out)==set(RIVALS)
    return out


def audit(seeds=range(16), demo_counts=(2,3,6)):
    seeds=list(seeds);harmful=[];equivalent=[];episodes=0;pairs=0;boundary=0
    for seed in seeds:
        bank=A.generate(seed, {'transfer_scope':'all_templates'}, 6, 4)
        trains=[predictions(p['input']) for p in bank['train']]
        tests=[predictions(p['input']) for p in bank['test']]
        for demos in demo_counts:
            for chosen in C.SCOPES:
                episodes+=1;pairs+=demos+4
                for rival in RIVALS:
                    if rival==chosen or not all(p[rival]==p[chosen] for p in trains[:demos]):continue
                    rec={'seed':seed,'demos':demos,'setting':chosen,'rival':rival}
                    if any(p[rival]!=p[chosen] for p in tests):harmful.append(rec)
                    else:equivalent.append(rec)
                boundary+=int(any(len(p['input'])==len(p['input'][0])==30 for p in bank['test']))
    return {'schema':'arcpuzzles-finite-teaching-audit-v1','status':'failed' if harmful else 'passed',
            'episodes':episodes,'labeled_pairs':pairs,'seeds':seeds,'demo_counts':list(demo_counts),
            'rivals':list(RIVALS),'harmful_survivors':harmful,'finite_equivalent_survivors':equivalent,
            'substantive_30x30_episodes':boundary,
            'label_backend':'Python claims; protected Racket in separate preflight and boundary receipts',
            'limits':'Finite declared competitors and seeds only, not universal uniqueness or owner acceptance.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,default=16);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();report=audit(range(args.seeds))
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pairs','harmful_survivors')}))
    raise SystemExit(0 if report['status']=='passed' else 1)
