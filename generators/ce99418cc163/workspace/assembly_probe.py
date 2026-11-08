"""Demonstrate why lesson checks belong after the actual assembly policy.

Uses saved Racket-labelled census rows, never solve/private labels. The mutation
is deliberately constructed evidence, not a claim about the production exporter.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def evaluate(demos, query, rivals):
    return {name: {'fits_all_demos': all(fn(x['input']) == x['output'] for x in demos),
                   'disagrees_on_query': fn(query['input']) != query['output']}
            for name,fn in rivals.items()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--census',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).resolve().parents[1]/'generator.py'
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    summary=json.loads((args.census/'summary.json').read_text())
    assert sha==summary['generator_sha256'] and summary['status']=='PASS'
    spec=importlib.util.spec_from_file_location('assembly_subject',source)
    gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
    rows=[json.loads(x) for x in (args.census/'draws.jsonl').read_text().splitlines()]
    rows=[r for r in rows if r['band']=='easy' and r['seed']==1000000]
    rows.sort(key=lambda r:r['sample_index'])
    assert len(rows)==6
    control=evaluate(rows[:3],rows[3],gen.LESSON_COMPETITORS)
    assert not any(r['fits_all_demos'] and r['disagrees_on_query'] for r in control.values())
    # Model an exporter that discards complex teaching inputs before selecting
    # the demonstration set, but keeps a valid hard query.
    demos=[r for r in rows if gen.observe_overrides(r['input'])['layout']!='chain'][:3]
    query=next(r for r in rows if gen.observe_overrides(r['input'])['layout']=='chain')
    mutated=evaluate(demos,query,gen.LESSON_COMPETITORS)
    assert len(demos)==3 and all(r['fits_all_demos'] and r['disagrees_on_query'] for r in mutated.values())
    report={'task_id':gen.TASK_ID,'generator_sha256':sha,'rule_hash':gen.RULE_HASH,
            'intent':'diagnostic_probe','production_failure_observed':False,
            'control':'First three consecutive draws as demos; fourth as query.',
            'mutation':'Select three non-chain demos from six draws; select a chain query.',
            'band':'easy','seed':1000000,'source_indices':[r['sample_index'] for r in rows],
            'control_scores':control,'mutation_scores':mutated,
            'reference_evidence':'checks/lesson-census/racket-0000.json and draws.jsonl',
            'gate':'Flag only competitors agreeing on every demo and differing on the actual query.',
            'status':'PASS: control accepted, intentionally ambiguous mutation detected'}
    lesson={'generator_sha256':sha,'rule_hash':gen.RULE_HASH,
            'intent':'diagnostic_probe','demos':demos,'query':query,
            'rival_outputs':{name:fn(query['input']) for name,fn in gen.LESSON_COMPETITORS.items()}}
    (args.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (args.out/'mutated-lesson.json').write_text(json.dumps(lesson,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
