"""Native matched-input adapter for the divider/marked-side family."""
from __future__ import annotations
import copy, importlib.util, json, random, sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_model_7491f3cf',BASE/'model.py')
model=importlib.util.module_from_spec(spec);sys.modules[spec.name]=model;spec.loader.exec_module(model)

def _mode(settings):
    if (type(settings) is not dict or set(settings)!={'marker_source'}
            or type(settings['marker_source']) is not str
            or settings['marker_source'] not in ('second','third')):
        raise ValueError('settings must be exactly marker_source=second|third')
    return settings['marker_source']

def program(settings):
    mode=_mode(settings);text=(BASE/'canonical.rkt').read_text()
    if mode=='second': return text
    needle="(define marker-source 'second)"
    if text.count(needle)!=1: raise ValueError('Canonical setting marker drifted')
    return text.replace(needle,"(define marker-source 'third)")

def generate(seed,settings,demos,queries):
    mode=_mode(settings);model.integer(seed,0,2**63-1,'seed');model.integer(demos,2,6,'demos');model.integer(queries,1,4,'queries')
    def pair(grid): return {'input':grid,'output':model.solve(grid,mode)}
    train=[pair(model.sample_input(seed,i,'demo')) for i in range(demos)]
    bank=[pair(model.sample_input(seed,i,'query')) for i in range(4)]
    random.Random(f'7491f3cf:{seed}:presentation').shuffle(bank)
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'private_query_bank':bank,
            'program_solution':program(settings),'settings':dict(settings),'seed':seed}

def public_view(episode,index=0):
    model.integer(index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':model.grid_copy(p['input']),'output':model.grid_copy(p['output'])} for p in episode['train']],
            'test':[{'input':model.grid_copy(episode['test'][index]['input'])}]}

CAUSAL_DESCRIPTIONS={
 'step_a':'Parse the guide panel, identify the full edge-separating divider component, remove it to recover the four-connected regions, and determine which region contains the detached marker.',
 'intermediate':'The input-dependent divider cells, marker cells, marked-region cells, and per-cell region-side classification.',
 'step_b':'Route the two source panels to opposite region classes and resolve divider overlaps with the source assigned to the marked region.',
 'why_b_depends_on_a':'The source patterns occupy multiple regions and the divider. Without the inferred divider, region partition, and marked-region identity, the renderer cannot know which source supplies a target coordinate or which color wins a divider conflict.'}

def causal_settings(): return {'marker_source':'second'}
def causal_intermediate(grid):
    a=model.analyze(grid)
    return {'divider_cells':[list(p) for p in sorted(a['divider'])],
            'marker_cells':[list(p) for p in sorted(a['marker_cells'])],
            'marked_region_cells':[list(p) for p in sorted(a['marker_region'])],
            'side_matrix':[[a['side'](r,c) for c in range(a['pw'])] for r in range(a['ph'])]}
def counterfactual_program(): return program({'marker_source':'third'})
