#!/usr/bin/env python3
"""Admit actual labeled JSONL lessons only after declared wrong rivals are refuted.

Runs after sampling/filtering/shuffling; no model or Racket startup is needed.
This is a semantic-information gate, NOT a replacement for Racket label checks.
The input must be author-side labeled episodes, never public answer-free challenges.
An unrefuted rival flags the lesson even when it agrees on the current query;
query-disagreeing survivors are separately listed as immediate label ambiguity.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def check_episode(episode: dict, rivals: dict) -> dict:
    report={'passed':False,'survivors':[],'query_disagreements':{},'errors':[]}
    if not rivals:
        report['errors'].append('No declared competing-rule contract; cannot certify the lesson.')
        return report
    for split in ('train','test'):
        pairs=episode.get(split)
        if not isinstance(pairs,list) or not pairs:
            report['errors'].append(f'{split} must contain at least one labeled pair')
            continue
        for i,pair in enumerate(pairs):
            if not isinstance(pair,dict) or 'input' not in pair or 'output' not in pair:
                report['errors'].append(f'{split}[{i}] needs input and output; do not supply public challenges')
    if report['errors']:return report
    for name,rival in rivals.items():
        try:
            if all(rival(copy.deepcopy(p['input']))==p['output'] for p in episode['train']):
                report['survivors'].append(name)
                report['query_disagreements'][name]=[
                    i for i,p in enumerate(episode['test']) if rival(copy.deepcopy(p['input']))!=p['output']]
        except Exception as exc:
            report['errors'].append(f'{name}: {type(exc).__name__}: {exc}')
    report['passed']=not report['errors'] and not report['survivors']
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episodes',type=Path);parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    home=Path(__file__).resolve().parents[1];repo=home.parents[1]
    sys.path.insert(0,str(repo/'shared/runtime'))
    source=home/'generator.py'
    spec=importlib.util.spec_from_file_location('admission_subject',source)
    gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    report={'schema':'post-assembly-rival-gate-v1','task_id':gen.TASK_ID,
            'generator_sha256':source_hash,'input_sha256':hashlib.sha256(args.episodes.read_bytes()).hexdigest(),
            'rivals':list(gen.LESSON_COMPETITORS),'lessons':[],
            'scope':'Information content relative to declared rivals; label correctness is a separate Racket gate.'}
    for line_no,line in enumerate(args.episodes.read_text().splitlines(),1):
        if not line.strip():continue
        episode=json.loads(line);result=check_episode(episode,gen.LESSON_COMPETITORS)
        if episode.get('task_id')!=gen.TASK_ID:
            result['errors'].append('task ID does not match loaded contract')
        if episode.get('provenance',{}).get('generator_sha256')!=source_hash:
            result['errors'].append('generator provenance missing or stale')
        result['passed']=result['passed'] and not result['errors']
        result['line']=line_no;report['lessons'].append(result)
    report['lesson_count']=len(report['lessons'])
    report['failed_lessons']=sum(not x['passed'] for x in report['lessons'])
    report['passed']=bool(report['lessons']) and report['failed_lessons']==0
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'out':str(args.out),'lessons':report['lesson_count'],
                      'failed':report['failed_lessons'],'passed':report['passed']}))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
