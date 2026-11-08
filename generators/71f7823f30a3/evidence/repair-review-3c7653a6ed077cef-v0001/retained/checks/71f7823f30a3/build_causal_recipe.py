#!/usr/bin/env python3
"""Bind audited row-color cues to exact native-qualified pairs and interventions."""
import argparse
import hashlib
import json
from pathlib import Path


def build(qualification,audit):
    q=json.loads(qualification.read_text())
    p=qualification.with_name('execution.json')
    assert hashlib.sha256(p.read_bytes()).hexdigest()==q['execution']['sha256']
    execution=json.loads(p.read_text())
    candidates=json.loads(audit.read_text())['causal_candidates']
    cases=[]
    for candidate in candidates:
        matches=[(i,e) for i,e in enumerate(execution['episodes'])
                 if e['settings']==candidate['settings'] and e['seed']==candidate['seed']
                 and e['program']==candidate['program'] and e['train'][0]['input']==candidate['input']
                 and e['train'][0]['output']==candidate['output']]
        assert len(matches)==1
        index,e=matches[0]
        policy=e['settings']['copy_policy']
        choice='argmin' if policy=='nearest_color' else 'argmax'
        wrong='argmax' if choice=='argmin' else 'argmin'
        needle=f'(cue ({choice} (lambda (c) (abs (- c a))) sources))'
        replacement=f'(cue ({wrong} (lambda (c) (abs (- c a))) sources))'
        assert e['program'].count(needle)==1
        cases.append({'episode_index':index,'split':'train','pair_index':0,
                      'ablation':'wrong_intermediate',
                      'intermediate_value':candidate['intermediate_value'],
                      'counterfactual_program':e['program'].replace(needle,replacement)})
    assert len(cases)==2
    return {'step_a':'For each anchored row, locate the nearest or farthest individual source relative to its maroon anchor.',
            'intermediate':'The input-derived cue column and color for each row, with the same-color source columns and their reflection targets.',
            'step_b':'Reflect every source of that selected color across the same row-local anchor, including remote sources, while preserving originals and orphan rows.',
            'why_b_depends_on_a':'The cue color determines which other source cells are copied. Changing only the nearest/farthest cue selector changes the selected colors and the remote writes; the subsequent color test and reflection code are identical. The reference reads the original input, not an iteratively updated grid.',
            'cases':cases}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualification',type=Path,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    result=build(a.qualification,a.audit)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cases':len(result['cases']),'out':str(a.out),'executed_labels':0}))
