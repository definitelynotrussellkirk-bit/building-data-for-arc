#!/usr/bin/env python3
"""Findings-only, bounded source-bound audit; never edits a generator or rule."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import apply_rule, validate_grid

TASK = '3374854ed70d'
REPO = Path.cwd()
OUT = REPO.parent / 'checks/audit' / TASK
GENERATOR = REPO / 'generators' / TASK / 'generator.py'


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def grid_sha(grid: object) -> str:
    return sha_bytes(json.dumps(grid, separators=(',', ':')).encode())


def main() -> None:
    sys.dont_write_bytecode = True
    started = time.monotonic()
    original = GENERATOR.read_bytes()
    spec = importlib.util.spec_from_file_location('audited_generator_3374854ed70d', GENERATOR)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    baseline_cases = []
    for seed in range(8):
        for index in (0, 3):
            grid = generator.generate(seed, index)
            baseline_cases.append((seed,index,grid))
    inert_axes = []
    for axis, values in [('palette_size',(1,8)), ('n_distinct_colors',(1,8)),
                         ('palette_kind',('warm','cool')), ('texture',('warm','cool'))]:
        comparisons = []
        for seed,index,baseline in baseline_cases:
            generated = [generator.generate(seed,index,**{axis:value}) for value in values]
            comparisons.append({'seed':seed,'sample_index':index,'default_grid_sha256':grid_sha(baseline),
                'values':list(values),'override_grid_sha256':[grid_sha(g) for g in generated],
                'all_equal_to_default':all(g==baseline for g in generated),
                'nonzero_distinct_colors':len({v for row in baseline for v in row if v})})
        inert_axes.append({'axis':axis,'declared':generator.AXES[axis],
                          'comparisons':comparisons,
                          'identical_to_default_count':sum(c['all_equal_to_default'] for c in comparisons)})
    declared_range_rejections = []
    for axis,value in [('grid_h',5),('grid_h',14),('grid_w',5),('grid_w',14),('seed_count',1),('seed_count',8)]:
        try:
            grid=generator.generate(0,0,**{axis:value})
            result={'accepted':True,'grid_sha256':grid_sha(grid)}
        except Exception as error:
            result={'accepted':False,'exception_type':type(error).__name__,'message':str(error)}
        declared_range_rejections.append({'axis':axis,'declared':generator.AXES[axis],
                                         'requested_value':value,**result})
    bool_grid=[[0]*7 for _ in range(7)]
    bool_grid[1][2]=True
    bool_grid[4][1]=2
    validation={'input':bool_grid,'self_check_errors':generator.self_check(bool_grid)}
    try:
        validate_grid(bool_grid)
        validation['public_validator_accepts']=True
    except Exception as error:
        validation.update(public_validator_accepts=False,public_validator_exception_type=type(error).__name__,
                          public_validator_message=str(error))
    malformed=copy.deepcopy(baseline_cases[0][2])
    malformed[1]=None
    try:
        malformed_check={'raised':False,'errors':generator.self_check(malformed)}
    except Exception as error:
        malformed_check={'raised':True,'exception_type':type(error).__name__,'message':str(error)}
    witness=generator.generate(0,0,n_distinct_colors=1)
    catalog=Catalog(REPO)
    metadata=catalog.describe(TASK)
    labelled=apply_rule(catalog,TASK,[witness],reference='canonical',check_generator_domain=True,timeout=120)
    (OUT/'public_racket_label.json').write_text(json.dumps(labelled,indent=2,sort_keys=True)+'\n')
    source_files={p.relative_to(REPO).as_posix():sha_bytes(p.read_bytes())
                  for p in (GENERATOR.parent).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    report={'schema':'arcpuzzles-bounded-findings-audit-v1','task_id':TASK,'audit_mode':'findings_only',
        'argv':sys.argv,'effective_cwd':str(REPO),'audited_generator_sha256':sha_bytes(original),
        'source_files_sha256':source_files,'review_index_present':(GENERATOR.parent/'evidence/review_index.json').exists(),
        'catalog_rule_hash':metadata['rule_hash'],'inert_axes':inert_axes,
        'declared_range_rejections':declared_range_rejections,'boolean_schema_probe':validation,
        'malformed_row_probe':malformed_check,
        'label_witness':{'call':{'seed':0,'sample_index':0,'overrides':{'n_distinct_colors':1}},
            'input':witness,'actual_nonzero_distinct_colors':len({v for row in witness for v in row if v}),
            'public_racket_receipt':'public_racket_label.json'},
        'source_unchanged':GENERATOR.read_bytes()==original,'elapsed_seconds':round(time.monotonic()-started,3)}
    (OUT/'probe.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    assert report['source_unchanged']
    assert all(item['identical_to_default_count']==16 for item in inert_axes)
    assert all(not item['accepted'] for item in declared_range_rejections)
    assert validation['self_check_errors']==[] and not validation['public_validator_accepts']
    assert report['label_witness']['actual_nonzero_distinct_colors']>1
    assert labelled['rule_hash_matches_catalog']
    assert len(labelled['results'])==1 and labelled['results'][0]['output'] is not None
    print(json.dumps({'task_id':TASK,'source_sha256':report['audited_generator_sha256'],
        'inert_axes':len(inert_axes),'paired_cases_per_axis':16,'advertised_values_rejected':len(declared_range_rejections),
        'boolean_accepted_by_self_check':True,'public_racket_rule_hash':labelled['executed_rule_hash'],
        'source_unchanged':report['source_unchanged'],'elapsed_seconds':report['elapsed_seconds']}),flush=True)


if __name__=='__main__':
    main()
