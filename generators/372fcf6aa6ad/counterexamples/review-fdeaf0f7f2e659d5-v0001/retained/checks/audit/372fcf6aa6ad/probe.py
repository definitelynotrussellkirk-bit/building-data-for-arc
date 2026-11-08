#!/usr/bin/env python3
"""Findings-only size-before-holes adversarial probe; prepare or verify evidence."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[2]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO/'shared/runtime'))
SOURCE = REPO / 'generators/372fcf6aa6ad/generator.py'
TASK = '372fcf6aa6ad'

def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()

def write(name, value):
    (HOME/name).write_text(json.dumps(value, indent=2)+'\n')

def generator():
    spec = importlib.util.spec_from_file_location('audit_generator_372fcf6aa6ad', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def rival(g, module):
    # Reuse object extraction and crop helpers; intentionally change ONLY
    # ordering-key precedence, never orientation, spacing, or alignment.
    items = []
    for obj in module._components(g):
        r, c, _, _ = obj['bbox']
        items.append((len(obj['cells']), module._hole_count_cells(obj['cells']), r, c,
                      module._rotate_cw(module._crop_object(g, obj))))
    items.sort(key=lambda item: item[:4])
    pieces = [item[4] for item in items]
    h = max(map(len, pieces)); w = sum(len(p[0]) for p in pieces) + len(pieces)-1
    out = [[0]*w for _ in range(h)]
    left = 0
    for piece in pieces:
        top = (h-len(piece))//2
        for r,row in enumerate(piece):
            for c,v in enumerate(row):
                if v: out[top+r][left+c] = v
        left += len(piece[0])+1
    return out

def command_entry(evidence):
    path = HOME/'commands.json'
    entries = json.loads(path.read_text()) if path.exists() else []
    identity = json.loads((HOME/'manifest.json').read_text())
    entries.append({'argv':[sys.executable,*sys.argv], 'cwd':str(Path.cwd()), 'exit_code':0,
                    'evidence_paths':[str(HOME/p) for p in evidence],
                    'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    'rule_hash':identity['canonical_rule_hash'],
                    'canonical_source_sha256':identity['canonical_rule_sha256']})
    write('commands.json', entries)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('phase', choices=['prepare','verify'])
parser.add_argument('--reference', type=Path, default=HOME/'racket.json')
args = parser.parse_args()
m = generator()
if args.phase == 'prepare':
    canonical = next(json.loads(line) for line in (REPO/'shared/data/canonical/puzzles.jsonl').open()
                     if json.loads(line)['task_id'] == TASK)
    rule = canonical['program_solution']
    pairs = canonical['train'] + canonical['test']
    cases = []
    for i,pair in enumerate(pairs):
        cases.append({'kind':'canonical', 'pair_index':i, 'input':pair['input'], 'given_output':pair['output']})
    for band in ('easy','medium','hard'):
        for index in range(16):
            seed = int(hashlib.sha256(f'audit-size-before-holes:v1:{TASK}:{band}:{index}'.encode()).hexdigest()[:12],16)
            g = m.generate(seed,index,difficulty=band)
            cases.append({'kind':'generated','difficulty':band,'seed':seed,'sample_index':index,
                          'overrides':{},'input':g,'self_check':m.self_check(g),
                          'observed_axes':m.observe_overrides(g)})
    g = [[0]*16 for _ in range(14)]
    # A solid 4x4 zero-hole object, a smaller 3x3 one-hole frame,
    # and a two-hole 5x4 frame. All objects are widely separated.
    for r in range(4):
        for c in range(4):g[1+r][1+c] = 2
    for r in range(3):
        for c in range(3):
            if r in (0,2) or c in (0,2):g[1+r][10+c] = 4
    for r in range(5):
        for c in range(4):
            if r in (0,2,4) or c in (0,3):g[8+r][1+c] = 7
    cases.append({'kind':'adversarial_witness','input':g,'self_check':m.self_check(g),
                  'observed_axes':m.observe_overrides(g),
                  'actual_draw':False,'domain_status':'validator accepted/documented isolated-object scene; outside finite authored motif support'})
    motifs = {str(holes): [{'size':len(cells),'computed_holes':m._hole_count_cells(cells)} for cells in family]
              for holes,family in [(0,m._ZERO_HOLE),(1,m._ONE_HOLE),(2,m._TWO_HOLE)]}
    write('input.json',[case['input'] for case in cases])
    write('rival_outputs.json',[rival(case['input'],m) for case in cases])
    write('manifest.json',{'task_id':TASK,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                          'canonical_rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),
                          'canonical_rule_hash':hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12],
                          'cases':cases,'motif_families':motifs,
                          'rival':'sort by (size,holes,top,left), with identical clockwise rotation and centered packing'})
    command_entry(['input.json','rival_outputs.json','manifest.json'])
    print('Prepared',len(cases),'cases: 5 canonical, 48 generated, 1 adversarial witness')
else:
    raw = json.loads(args.reference.read_text())
    manifest = json.loads((HOME/'manifest.json').read_text())
    rivals = json.loads((HOME/'rival_outputs.json').read_text())
    assert raw['generator_sha256'] == manifest['generator_sha256']
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == manifest['generator_sha256']
    assert raw['executed_rule_hash'] == manifest['canonical_rule_hash']
    results = raw['results']
    assert len(results) == len(manifest['cases']) == len(rivals) == 54
    summary = {'generator_sha256':manifest['generator_sha256'], 'rule_hash':manifest['canonical_rule_hash'],
               'canonical':{'draws':0,'rival_matches':0}, 'generated':{}, 'errors':[]}
    for case, result, wrong in zip(manifest['cases'],results,rivals):
        assert result['input'] == case['input']
        assert result['error'] is None and result['valid_output']
        if case['kind'] == 'canonical':
            assert result['output'] == case['given_output']
            summary['canonical']['draws'] += 1
            summary['canonical']['rival_matches'] += result['output'] == wrong
        elif case['kind'] == 'generated':
            assert not case['self_check']
            assert not m.self_check(case['input'])
            band = summary['generated'].setdefault(case['difficulty'],{'draws':0,'rival_matches':0,'profiles':{},'input_hashes':[]})
            band['draws'] += 1
            band['rival_matches'] += result['output'] == wrong
            profile = case['observed_axes']['lesson_profile']
            band['profiles'][profile] = band['profiles'].get(profile,0)+1
            band['input_hashes'].append(result['input_sha256'])
        else:
            assert not case['self_check']
            assert result['output'] != wrong
            def order(g):
                colors = {v for row in g for v in row if v}
                return sorted(colors,key=lambda v:min(c for row in g for c,x in enumerate(row) if x == v))
            witness = {'task_id':TASK,'generator_sha256':manifest['generator_sha256'],
                       'rule_hash':manifest['canonical_rule_hash'],'rule_text_sha256':manifest['canonical_rule_sha256'],
                       'input':case['input'],'actual_racket_output':result['output'],'rival_output':wrong,
                       'racket_output_color_order':order(result['output']), 'rival_color_order':order(wrong),
                       'validation':case['self_check'], 'domain_status':case['domain_status'],
                       'observed_axes':case['observed_axes'], 'actual_draw':False,
                       'object_profiles':[{'color':obj['color'],'size':len(obj['cells']),
                                           'holes':m._hole_count_cells(obj['cells']),'bbox':obj['bbox']}
                                          for obj in m._components(case['input'])],
                       'racket_command':raw['command'],'racket_cwd':raw['cwd'],'racket_result_index':result['index']}
            write('counterexample.json',witness)
            summary['witness'] = {'rival_disagrees':True,'self_check':[], 'actual_order':order(result['output']),
                                  'rival_order':order(wrong), 'racket_result_index':result['index']}
    for band in summary['generated'].values():
        band['unique_inputs'] = len(set(band.pop('input_hashes')))
        assert band['rival_matches'] == band['draws'] == 16
        assert set(band['profiles'].values()) == {4}
    assert summary['canonical']['rival_matches'] == 5
    write('summary.json',summary)
    command_entry(['summary.json','counterexample.json',str(args.reference.resolve()),'manifest.json'])
    print(json.dumps(summary,indent=2))
