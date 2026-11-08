"""Native unapproved-authoring adapter for relational template enlargement."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
from puzzle_generators.base import stable_rng

BASE=Path(__file__).resolve().parent
_name='_familyc4_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec=importlib.util.spec_from_file_location(_name,BASE/'family.py')
family=importlib.util.module_from_spec(_spec);sys.modules[_name]=family;_spec.loader.exec_module(family)


def _settings(settings):
    if (type(settings) is not dict or set(settings)!={'completion'} or type(settings['completion']) is not str
            or settings['completion'] not in ('all','anchored_components')):
        raise ValueError('settings must be exactly completion=all|anchored_components')
    return settings['completion']


def program(settings):
    value=_settings(settings)
    return (BASE/('canonical.rkt' if value=='all' else 'anchored_components.rkt')).read_text()


def generate(seed,settings,demos,queries):
    completion=_settings(settings)
    family.integer(seed,0,2**63-1,'seed');family.integer(demos,2,6,'demos');family.integer(queries,1,4,'queries')
    shapes=[(16,20),(22,26),(20,24),(23,25),(26,28),(28,30)]
    qshapes=[(16,20),(20,24),(26,28),(30,30)]
    def pair(index,shape):
        g=family.sample(seed,index,*shape)
        return {'input':g,'output':family.solve(g,completion)}
    train=[pair(i,shapes[i]) for i in range(demos)]
    bank=[pair(100+i,shape) for i,shape in enumerate(qshapes)]
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'private_query_bank':bank,'program_solution':program(settings)}


def presentation_order(presentation_seed):
    family.integer(presentation_seed,0,2**63-1,'presentation_seed')
    order=list(range(4));stable_rng(presentation_seed,'four-query-presentation','1').shuffle(order)
    return order


def public_view(episode,source_query_index):
    from reviewer_support import public_challenge_bytes
    import json
    family.integer(source_query_index,0,3,'source_query_index')
    bank=episode['private_query_bank']
    if type(bank) is not list or len(bank)!=4:raise ValueError('private four-query bank required')
    return json.loads(public_challenge_bytes({'train':episode['train'],
                     'test':[{'input':bank[source_query_index]['input']}]}))

CAUSAL_DESCRIPTIONS={
 'step_a':'Extract the miniature and seed squares; solve their unique color/relative-position registration, then map seeds into miniature coordinates and select their four-connected foreground components.',
 'intermediate':'The inferred origin, pitch, block side, registered seed-cell indices and selected miniature-component mask.',
 'step_b':'Render enlarged squares at the inferred lattice addresses for exactly the selected miniature cells, preserving original miniature and seed evidence.',
 'why_b_depends_on_a':'Several miniature cells share the seed color, and repeated colors occur in disconnected components. Only relational registration determines the correct target addresses and component membership; fixed origin or palette-only selection is insufficient.'}


def causal_settings():return {'completion':'anchored_components'}


def causal_intermediate(grid):return family.intermediate(grid)


def counterfactual_program():
    text=program(causal_settings())
    needle='(let* ((reg (first candidates)) (ar (first reg)) (ac (second reg)) (pitch (third reg)))'
    if text.count(needle)!=1:raise ValueError('registration consumer source changed')
    return text.replace(needle,'(let* ((reg (first candidates)) (ar (+ (first reg) 1)) (ac (second reg)) (pitch (third reg)))')
