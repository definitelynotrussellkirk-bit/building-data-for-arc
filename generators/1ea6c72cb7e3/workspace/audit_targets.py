#!/usr/bin/env python3
"""Findings-only, source-bound reproducers for this packet's two audit targets.

Uses the actual lesson runner and canonical Racket output authority. This does
not repair either target or inspect private solve labels. Exit 0 means the
probe ran to completion; read findings/profile verdicts, not exit status, as
quality results. --out refuses to overwrite retained evidence.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import gzip
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
TARGETS = ('be743fd05a59', '4f5bd0601f95')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def first_run_only(grid):
    """Incorrect: ignore later same-row runs, even though the rule handles them."""
    out = [[0]*len(row) for row in grid]
    for r, row in enumerate(grid):
        start = next((c for c, value in enumerate(row) if value), None)
        if start is None:
            continue
        end = start
        while end < len(row) and row[end] == row[start]:
            end += 1
        for c in range(start, end, 2):
            out[r][c] = row[start]
    return out


def echo_overwrite(grid):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 9 and r+1 < len(grid) and c > 0:
                out[r+1][c-1] = 5
    return out


def echo_wrap(grid):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 9:
                rr, cc = (r+1) % len(grid), (c-1) % len(row)
                if grid[rr][cc] == 0:
                    out[rr][cc] = 5
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--lessons-per-band', type=int, default=20)
    args = parser.parse_args(argv)
    if args.lessons_per_band < 1:
        parser.error('lessons-per-band must be positive')
    out = args.out.resolve()
    archive = out.with_suffix('.lessons.jsonl.gz')
    if out.exists() or archive.exists():
        parser.error('refusing to overwrite retained evidence')
    out.parent.mkdir(parents=True, exist_ok=True)
    invocation = {'argv': sys.argv, 'cwd': str(Path.cwd())}
    report = {'schema': 'assigned-audit-probe-v1', 'invocation': invocation,
              'probe_sha256': digest(Path(__file__).read_bytes()), 'targets': {},
              'lesson_policy': {'n_demos': 3, 'n_queries': 1,
                  'k_range': [0,args.lessons_per_band-1],
                  'seed': 'canonical_profile_gate._pinned_seed(task_id, lesson:BAND, k)',
                  'sample_index': '11*k', 'bands': ['easy','medium','hard'],
                  'runner': 'generator_semantic_gate.materialize_lessons -> runner.run_one'},
              'scope': 'Findings-only finite audits. Exit 0 is execution success, not target approval.'}
    sys.path.insert(0, str(ROOT/'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    records = []
    old_cwd = Path.cwd()
    try:
        with tempfile.TemporaryDirectory(prefix='assigned-audits-') as directory:
            runtime = Path(directory)
            prepare_runtime(Catalog(ROOT), runtime, task_ids=list(TARGETS))
            report['actual_runtime_directory'] = str(runtime)
            sys.path.insert(0, str(runtime)); os.chdir(runtime)
            from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash, audit_task
            from scripts.generator_semantic_gate import _RuleOracle, materialize_lessons
            for task in TARGETS:
                gen = importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
                rule = canonical_rule_source(task)
                item = {'generator_sha256': digest((ROOT/'generators'/task/'generator.py').read_bytes()),
                        'rule_hash': normalized_rule_hash(rule),
                        'rule_source_sha256': digest(rule.encode()),
                        'declared_rule_hash': getattr(gen, 'RULE_HASH', None),
                        'profile': audit_task(task, per_band=20, strict=True, min_band_support=1),
                        'canonical_racket_matches': 0, 'canonical_rival_matches': Counter(),
                        'generated_rival_matches': Counter(), 'lesson_refutations': Counter(),
                        'errors': [], 'canonical_counterexamples': [], 'generated_counterexamples': []}
                report['targets'][task] = item
                rivals = ({'echo_overwrite':echo_overwrite, 'echo_wrap':echo_wrap}
                          if task == TARGETS[0] else {'first_run_only':first_run_only})
                oracle = _RuleOracle(task)
                try:
                    if not oracle.ready:
                        raise RuntimeError(oracle.error)
                    pairs = canonical_pairs(task)
                    item['canonical_pairs'] = len(pairs)
                    for index, pair in enumerate(pairs):
                        actual, error = oracle.apply(pair['input'])
                        if error:
                            raise RuntimeError(error)
                        item['canonical_racket_matches'] += actual == pair['output']
                        for name, rival in rivals.items():
                            predicted = rival(copy.deepcopy(pair['input']))
                            item['canonical_rival_matches'][name] += predicted == actual
                            if predicted != actual:
                                item['canonical_counterexamples'].append({
                                    'task_id':task, 'generator_sha256':item['generator_sha256'],
                                    'rule_hash':item['rule_hash'], 'rule_source_sha256':item['rule_source_sha256'],
                                    'source':'canonical pair', 'pair_index':index,
                                    'seed':None, 'sample_index':None, 'overrides':None,
                                    'input':pair['input'], 'actual_racket_output':actual,
                                    'rival_name':name, 'rival_output':predicted,
                                    'self_check':gen.self_check(copy.deepcopy(pair['input'])),
                                    'documented_domain': True,
                                    'sampler_support':False if task == TARGETS[1] else 'not established',
                                    'domain_note':'Canonical input; multiple runs in a row are described by the rule but absent from this default sampler.' if task == TARGETS[1] else 'Canonical input.',
                                    'command':invocation})
                    lessons, errors = materialize_lessons(task, 3*args.lessons_per_band,
                        n_demos=3, oracle_factory=lambda:oracle)
                    item['errors'].extend(errors)
                    unique = set(); pair_count = 0; mirror_matches = 0
                    for index, lesson in enumerate(lessons):
                        scores = {}
                        for name, rival in rivals.items():
                            refuted = any(rival(copy.deepcopy(p['input'])) != p['output'] for p in lesson['demos'])
                            item['lesson_refutations'][name] += refuted
                            scores[name] = ('refuted' if refuted else 'query_discriminates'
                                if rival(copy.deepcopy(lesson['query']['input'])) != lesson['query']['output']
                                else 'survived_all')
                            if scores[name] == 'query_discriminates':
                                item['generated_counterexamples'].append({
                                    'task_id':task, 'generator_sha256':item['generator_sha256'],
                                    'rule_hash':item['rule_hash'], 'rule_source_sha256':item['rule_source_sha256'],
                                    'source':'actual runner lesson', 'seed':lesson['seed'],
                                    'sample_index':lesson['sample_index'], 'difficulty':lesson['band'],
                                    'overrides':{}, 'demos':lesson['demos'],
                                    'input':lesson['query']['input'],
                                    'actual_racket_output':lesson['query']['output'],
                                    'rival_name':name, 'rival_output':rival(copy.deepcopy(lesson['query']['input'])),
                                    'self_check':gen.self_check(copy.deepcopy(lesson['query']['input'])),
                                    'documented_domain':True, 'sampler_support':True,
                                    'domain_note':'Generated lawful default input. Rival fits all three demonstrations and differs on query.',
                                    'command':invocation})
                        for pair in [*lesson['demos'],lesson['query']]:
                            pair_count += 1
                            unique.add(digest(json.dumps(pair['input'],separators=(',',':')).encode()))
                            errors = gen.self_check(copy.deepcopy(pair['input']))
                            if errors:
                                item['errors'].append({'lesson':index,'self_check':errors})
                            for name, rival in rivals.items():
                                item['generated_rival_matches'][name] += rival(copy.deepcopy(pair['input'])) == pair['output']
                            if hasattr(gen,'rule_mirror'):
                                mirror_matches += gen.rule_mirror(pair['input']) == pair['output']
                        records.append({'task_id':task,'index':index,**lesson,'scores':scores})
                    item.update({'lessons':len(lessons),'pair_occurrences':pair_count,
                                 'unique_inputs':len(unique),'mirror_racket_matches':mirror_matches if hasattr(gen,'rule_mirror') else None})
                    if task == TARGETS[1]:
                        base = gen.generate(0,0,difficulty='easy')
                        probes = []
                        for overrides in ({'palette_size':1},{'n_distinct_colors':1},{'grid_h':3},{'run_count':1},{'unknown_axis':3}):
                            row = {'seed':0,'sample_index':0,'difficulty':'easy','overrides':overrides}
                            try:
                                grid = gen.generate(0,0,difficulty='easy',**overrides)
                                colors = sorted({v for r in grid for v in r if v})
                                row.update({'input':grid,'h':len(grid),'w':len(grid[0]),
                                    'nonzero_colors':colors, 'nonzero_color_count':len(colors),
                                    'equal_to_default':grid==base,'self_check':gen.self_check(grid)})
                            except Exception as exc:
                                row['exception'] = f'{type(exc).__name__}: {exc}'
                            probes.append(row)
                        item['override_probes'] = probes
                finally:
                    oracle.close()
    finally:
        os.chdir(old_cwd)
    raw = ''.join(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n' for row in records).encode()
    archive.write_bytes(gzip.compress(raw,mtime=0))
    report['archive'] = {'path':archive.name,'sha256':digest(archive.read_bytes()),
        'uncompressed_path':archive.name[:-3], 'uncompressed_bytes':len(raw),'uncompressed_sha256':digest(raw),
        'restore':f'gzip -dc {archive.name} > {archive.name[:-3]}'}
    out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({t:{'profile':v['profile']['status'],'lessons':v['lessons'],
                        'lesson_refutations':v['lesson_refutations'],'errors':v['errors']}
                      for t,v in report['targets'].items()},indent=2))
    return 2 if any(v['errors'] for v in report['targets'].values()) else 0


if __name__ == '__main__':
    raise SystemExit(main())
