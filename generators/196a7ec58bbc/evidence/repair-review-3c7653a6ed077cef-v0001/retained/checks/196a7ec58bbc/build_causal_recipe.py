#!/usr/bin/env python3
"""Build minimal selector interventions from qualified, audited quadrant pairs."""
import argparse
import hashlib
import json
from pathlib import Path


def build(qualification, audit):
    q=json.loads(qualification.read_text())
    ep=qualification.with_name('execution.json')
    assert hashlib.sha256(ep.read_bytes()).hexdigest()==q['execution']['sha256']
    execution=json.loads(ep.read_text())
    candidate=json.loads(audit.read_text())['causal_candidates'][0]
    cases=[]
    for i,e in enumerate(execution['episodes']):
        if e['settings']['source_mode']!='largest_component' or e['seed']!=candidate['seed']:
            continue
        pair=e['train'][0]
        assert pair['input']==candidate['input']
        needle='(chosen (argmax obj-size objs))'
        assert e['program'].count(needle)==1
        replacement='(chosen (argmax (lambda (o) (* (obj-h o) (obj-w o))) objs))'
        cases.append({'episode_index':i,'split':'train','pair_index':0,
                      'ablation':'wrong_intermediate',
                      'intermediate_value':candidate['intermediate_value'],
                      'counterfactual_program':e['program'].replace(needle,replacement)})
    assert len(cases)==2
    return {'step_a':'Discover same-color four-connected nonzero components and select the unique largest by occupied cells.',
            'intermediate':'The selected object, its tight square bounding box, and its object-only cropped grid.',
            'step_b':'Rotate and tile that cropped grid into four quadrants under the episode handedness.',
            'why_b_depends_on_a':'The selected object determines the source pixels, color and side length consumed by tiling. Replacing only the selector with largest bounding-box area chooses the sparse distractor and changes the final output geometry and cells; the tiling code is identical.',
            'cases':cases}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--qualification',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    recipe=build(a.qualification,a.audit)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(recipe,indent=2)+'\n')
    print(json.dumps({'cases':len(recipe['cases']),'out':str(a.out),'executed_labels':0}))
