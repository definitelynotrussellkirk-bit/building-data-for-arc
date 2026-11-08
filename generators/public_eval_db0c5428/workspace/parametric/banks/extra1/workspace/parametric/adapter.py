"""Native authoring adapter for missing-center tile reconstruction."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
from puzzle_generators.base import stable_rng
BASE=Path(__file__).resolve().parent
_name='_familydb0_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec=importlib.util.spec_from_file_location(_name,BASE/'family.py')
family=importlib.util.module_from_spec(_spec);sys.modules[_name]=family;_spec.loader.exec_module(family)


def _settings(settings):
    if type(settings) is not dict or set(settings)!={'outer_scope'} or type(settings['outer_scope']) is not str or settings['outer_scope'] not in ('all','modal_inward'):
        raise ValueError('settings must be exactly outer_scope=all|modal_inward')
    return settings['outer_scope']


def program(settings):
    value=_settings(settings);text=(BASE/'canonical.rkt').read_text()
    return text if value=='all' else text.replace('(define scope-mode 0)','(define scope-mode 1)')


def _scene(seed,index,shape,size):
    h,w=shape;return family.make_scene(seed,index,h,w,size=size)


def generate(seed,settings,demos,queries):
    value=_settings(settings);family.integer(seed,0,2**63-1,'seed');family.integer(demos,2,6,'demos');family.integer(queries,1,4,'queries')
    demo_profiles=[((15,17),3),((25,26),5),((18,20),3),((27,28),5),((21,24),3),((30,30),5)]
    query_profiles=[((16,18),3),((25,27),5),((28,29),5),((30,30),5)]
    def pair(index,item):
        shape,size=item;scene=_scene(seed,index,shape,size)
        return {'input':scene['input'],'output':family.solve(scene['input'],value)}
    train=[pair(i,demo_profiles[i]) for i in range(demos)]
    bank=[pair(100+i,item) for i,item in enumerate(query_profiles)]
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'private_query_bank':bank,'program_solution':program(settings)}


def presentation_order(presentation_seed):
    family.integer(presentation_seed,0,2**63-1,'presentation_seed');order=list(range(4));stable_rng(presentation_seed,'db0-four-query-presentation','1').shuffle(order);return order


def public_view(episode,source_query_index):
    from reviewer_support import public_challenge_bytes
    family.integer(source_query_index,0,3,'source_query_index');bank=episode['private_query_bank']
    if type(bank) is not list or len(bank)!=4:raise ValueError('private four-query bank required')
    return json.loads(public_challenge_bytes({'train':episode['train'],'test':[{'input':bank[source_query_index]['input']}]}))


CAUSAL_DESCRIPTIONS={
 'step_a':'Locate the 3x3 macro-tile source, reconstruct the missing center tile from all eight inward-facing boundaries, and count the eight inward anchor colors.',
 'intermediate':'The input-dependent reconstructed center tile, ordered inward samples, sample multiplicities, and uniquely modal inward color.',
 'step_b':'Retain the source 3x3 arrangement and copy outward either every surrounding tile or exactly those whose inward sample has the modal color.',
 'why_b_depends_on_a':'Under modal_inward, the outward renderer cannot select source tiles until the missing-center analysis has measured and compared the eight input-dependent inward samples.'}


def causal_settings():return {'outer_scope':'modal_inward'}
def causal_intermediate(grid):return family.intermediate(grid)
def counterfactual_program():
    text=program(causal_settings())
    old='''   (define modal-record
    (pick-max records
     (lambda (record)
      (count-if (lambda (other) (= (third other) (third record))) records))))'''
    if text.count(old)!=1:raise ValueError('modal consumer source changed')
    return text.replace(old,'   (define modal-record (third records))')
