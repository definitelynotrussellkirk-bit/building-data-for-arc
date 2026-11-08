#!/usr/bin/env python3
"""Bounded, findings-only pinned-source transform-gallery audit."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
from reviewer_support import canonical_pairs

TASK='ce3c0854174d'
SOURCE=REPO/'generators'/TASK/'generator.py'
PIN='42da7ef9b8d1112303ad4a1645bf5c4b6f87148f724fee63bc78ee5f93a9d5d8'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==PIN
spec=importlib.util.spec_from_file_location('audited_timeline',SOURCE)
gen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def build():
    rows=[]
    for difficulty in ('easy','medium','hard'):
        for index in range(4):
            grid=gen.generate(101,index,difficulty=difficulty)
            assert gen.generate(101,index,difficulty=difficulty)==grid
            assert not gen.self_check(grid)
            if index%2==0:
                assert set(grid[0])-{0}=={1,2,3,4}
                assert gen._asymmetric(gen._template(grid))
            rows.append({'kind':'default','seed':101,'sample_index':index,'difficulty':difficulty,
                         'overrides':{},'input':grid})
    endpoints=[(7,10,2),(7,16,5),(12,10,5),(12,16,2)]
    for index,(height,width,length) in enumerate(endpoints):
        overrides={'height':height,'width':width,'script_len':length}
        difficulty='easy' if index%2==0 else 'hard'
        grid=gen.generate(202,index,difficulty=difficulty,**overrides)
        assert gen.observe_overrides(grid)==overrides
        assert not gen.self_check(grid)
        rows.append({'kind':'endpoint','seed':202,'sample_index':index,'difficulty':difficulty,
                     'overrides':overrides,'input':grid})
    for index,pair in enumerate(canonical_pairs(TASK,root=REPO)):
        assert not gen.self_check(pair['input'])
        rows.append({'kind':'canonical','canonical_pair_index':index,**pair})
    original=[[7,0,0],[7,7,7]]
    firsts={1:[[7,7],[7,0],[7,0]],2:[[7,7,7],[0,0,7]],
            3:[[0,0,7],[7,7,7]],4:[[7,7],[0,7],[0,7]]}
    for code in range(1,5):
        grid=[[0]*10 for _ in range(7)]
        grid[0][:2]=[code,code]
        grid[2][2]=7
        grid[3][2:5]=[7,7,7]
        assert not gen.self_check(grid)
        second=firsts[2] if code==1 else original
        first=firsts[code]
        width=len(first[0])+1+len(second[0])
        expected=[[0]*width for _ in range(max(len(first),len(second)))]
        for frame,left in ((first,0),(second,len(first[0])+1)):
            for r,row in enumerate(frame):
                expected[r][left:left+len(row)]=row
        rows.append({'kind':'literal_rectangular_legend','script':[code,code],
                     'input':grid,'independent_expected_output':expected})
    (HERE/'cases.json').write_text(json.dumps({'task_id':TASK,'generator_sha256':PIN,'cases':rows},indent=2)+'\n')
    (HERE/'input.json').write_text(json.dumps({'inputs':[row['input'] for row in rows]})+'\n')
    print(json.dumps({'status':'inputs-built','cases':len(rows),'source_sha256':PIN}))


def verify():
    rows=json.loads((HERE/'cases.json').read_text())['cases']
    applied=json.loads((HERE/'racket.json').read_text())
    assert applied['generator_sha256']==PIN
    assert applied['executed_rule_hash']=='442270b293a4'
    assert applied['rule_hash_matches_catalog']
    assert len(applied['results'])==len(rows)==24
    for row,result in zip(rows,applied['results'],strict=True):
        assert result['input']==row['input']
        assert result['output']==gen.predict_gallery(row['input'])
        if 'output' in row:
            assert result['output']==row['output']
        if 'independent_expected_output' in row:
            assert result['output']==row['independent_expected_output']
        output=result['output']
        assert 1<=len(output)<=30 and 1<=len(output[0])<=30
        assert all(len(part)==len(output[0]) for part in output)
    heldouts=[]
    for difficulty in ('easy','medium','hard'):
        selected=[(row,result) for row,result in zip(rows,applied['results'])
                  if row['kind']=='default' and row['difficulty']==difficulty]
        pairs=[{'input':row['input'],'output':result['output']} for row,result in selected]
        for query_index,query in enumerate(pairs):
            demos=[pair for index,pair in enumerate(pairs) if index!=query_index]
            issues=gen.lesson_identifiable(demos,query)
            assert not issues,(difficulty,query_index,issues)
            heldouts.append({'difficulty':difficulty,'query_index':query_index,'issues':issues})
    malformed=[]
    base=rows[0]['input']
    hole=copy.deepcopy(base); hole[0][1]=0
    multicolor=copy.deepcopy(base)
    position=next((r,c) for r in range(2,len(base)) for c,value in enumerate(base[r]) if value)
    multicolor[position[0]][position[1]]=1
    for name,grid in [('script_hole',hole),('body_wrong_color',multicolor)]:
        errors=gen.self_check(grid)
        assert errors
        malformed.append({'kind':name,'errors':errors})
    unique=len({json.dumps(row['input']) for row in rows})
    summary={'task_id':TASK,'generator_sha256':PIN,'rule_hash':applied['executed_rule_hash'],
             'rule_text_sha256':applied['rule_text_sha256'],
             'executed_pairs':24,'unique_inputs':unique,
             'counts':{'default':12,'joint_endpoint':4,'canonical':4,'literal_rectangular_legend':4},
             'label_mismatches':0,'self_check_failures_on_lawful_inputs':0,
             'heldout_lessons_checked':12,'declared_rivals_per_lesson':len(gen.LESSON_COMPETITORS),
             'heldout_issues':heldouts,'malformed_rejections':malformed,
             'conclusion':'No new issue found within this bounded audit; existing finite-shape and short-script limits remain.'}
    (HERE/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':
    {'build':build,'verify':verify}[sys.argv[1]]()
