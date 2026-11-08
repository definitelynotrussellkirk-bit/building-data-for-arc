#!/usr/bin/env python3
"""Public-only, query-sensitive ambiguity gate for reviewed candidate programs.

CANDIDATES in a trusted local Python adapter maps names to solve(grid) functions.
The gate reads visible train labels, but rejects any query carrying an output.
Exit 2: surviving programs disagree on a query. Exit 1: incomplete/error.
Exit 0: no disagreement within this finite candidate set, NOT a uniqueness proof.
This is a diagnostic tool, not a sandbox for untrusted or unbounded Python code.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def valid_grid(grid):
    return (isinstance(grid,list) and bool(grid) and
            all(isinstance(row,list) and bool(row) for row in grid) and
            len({len(row) for row in grid})==1 and
            all(type(v) is int and 0 <= v <= 9 for row in grid for v in row))


def audit(challenge, candidates):
    report={'schema':'public-lesson-ambiguity-v1','status':'ERROR',
        'uses_query_labels':False,'survivors':[],'ambiguous_queries':[],
        'candidates':{},'errors':[],
        'scope':'Reviewed finite candidates only. Agreement is not proof of identifiability or query correctness.'}
    if (not isinstance(challenge,dict) or not challenge.get('train') or not challenge.get('test') or
            any(not isinstance(pair,dict) or set(pair)!={'input','output'} for pair in challenge['train']) or
            any(not isinstance(pair,dict) or set(pair)!={'input'} for pair in challenge['test'])):
        report['errors'].append('Require labelled train pairs and input-only test pairs; query labels are prohibited.')
        return report
    if not candidates or not all(isinstance(name,str) and callable(fn) for name,fn in candidates.items()):
        report['errors'].append('Require at least one named callable candidate.')
        return report
    if any(not valid_grid(pair[key]) for split in ('train','test') for pair in challenge[split] for key in pair):
        report['errors'].append('Malformed ARC grid in public challenge.')
        return report
    for name,fn in candidates.items():
        stats={'visible_matches':0,'visible_total':len(challenge['train']),
               'query_predictions':[],'errors':[]}
        for i,pair in enumerate(challenge['train']):
            try:
                out=fn(deepcopy(pair['input']))
                if not valid_grid(out):
                    raise ValueError('candidate returned invalid grid')
                stats['visible_matches']+=out==pair['output']
            except Exception as exc:
                stats['errors'].append({'split':'train','index':i,'error':repr(exc)})
        if not stats['errors'] and stats['visible_matches']==stats['visible_total']:
            report['survivors'].append(name)
            for i,pair in enumerate(challenge['test']):
                try:
                    out=fn(deepcopy(pair['input']))
                    if not valid_grid(out):
                        raise ValueError('candidate returned invalid grid')
                    stats['query_predictions'].append(out)
                except Exception as exc:
                    stats['errors'].append({'split':'test','index':i,'error':repr(exc)})
        report['candidates'][name]=stats
        if stats['errors']:
            report['errors'].append({'candidate':name,'errors':stats['errors']})
    if report['errors']:
        return report
    if not report['survivors']:
        report['errors'].append('No candidate fits the visible examples; expand or repair the reviewed candidate set.')
        return report
    for i in range(len(challenge['test'])):
        predictions={json.dumps(report['candidates'][name]['query_predictions'][i],separators=(',',':'))
                     for name in report['survivors']}
        if len(predictions)>1:
            report['ambiguous_queries'].append(i)
    report['status']='AMBIGUOUS' if report['ambiguous_queries'] else 'NO_KNOWN_QUERY_DISAGREEMENT'
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--challenge',required=True,type=Path)
    ap.add_argument('--candidates',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args()
    raw=a.challenge.read_bytes(); source=a.candidates.read_bytes()
    # Local adapters may import a sibling solution module. Callables are trusted,
    # reviewed diagnostics, not arbitrary remotely supplied executable programs.
    sys.path.insert(0,str(a.candidates.resolve().parent))
    spec=importlib.util.spec_from_file_location('lesson_candidates',a.candidates)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    report=audit(json.loads(raw),getattr(mod,'CANDIDATES',{}))
    report.update({'challenge_sha256':hashlib.sha256(raw).hexdigest(),
        'candidate_module_sha256':hashlib.sha256(source).hexdigest(),
        'candidate_module':str(a.candidates),'gate_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='candidates'},indent=2))
    return {'ERROR':1,'AMBIGUOUS':2,'NO_KNOWN_QUERY_DISAGREEMENT':0}[report['status']]

if __name__=='__main__':
    raise SystemExit(main())
