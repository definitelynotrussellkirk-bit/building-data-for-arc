"""Native authoring adapter for template-blueprint expansion."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
from puzzle_generators.base import stable_rng
BASE=Path(__file__).resolve().parent
_name='_family65_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec=importlib.util.spec_from_file_location(_name,BASE/'family.py')
family=importlib.util.module_from_spec(_spec);sys.modules[_name]=family;_spec.loader.exec_module(family)

def _settings(settings):
    if type(settings) is not dict or set(settings)!={'placement_scope'} or type(settings['placement_scope']) is not str or settings['placement_scope'] not in ('all','modal_template'):
        raise ValueError('settings must be exactly placement_scope=all|modal_template')
    return settings['placement_scope']

def program(settings):
    value=_settings(settings);text=(BASE/'canonical.rkt').read_text()
    return text if value=='all' else text.replace('(define scope-mode 0)','(define scope-mode 1)')

def _scene(seed,index,shape,profile):
    h,w=shape;s,n=profile
    return family.make_scene(seed,index,h,w,size=s,templates=n)

def generate(seed,settings,demos,queries):
    value=_settings(settings);family.integer(seed,0,2**63-1,'seed');family.integer(demos,2,6,'demos');family.integer(queries,1,4,'queries')
    demo_shapes=[((12,14),(3,3)),((14,20),(4,4)),((18,23),(5,3)),((20,24),(4,4)),((24,27),(5,4)),((26,29),(5,4))]
    query_shapes=[((14,16),(3,3)),((18,20),(4,4)),((24,27),(5,3)),((30,30),(5,4))]
    def pair(index,item):
        scene=_scene(seed,index,*item);return {'input':scene['input'],'output':family.solve(scene['input'],value)}
    train=[pair(i,demo_shapes[i]) for i in range(demos)]
    bank=[pair(100+i,item) for i,item in enumerate(query_shapes)]
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'private_query_bank':bank,'program_solution':program(settings)}

def presentation_order(presentation_seed):
    family.integer(presentation_seed,0,2**63-1,'presentation_seed');order=list(range(4));stable_rng(presentation_seed,'four-query-presentation','1').shuffle(order);return order

def public_view(episode,source_query_index):
    from reviewer_support import public_challenge_bytes
    family.integer(source_query_index,0,3,'source_query_index');bank=episode['private_query_bank']
    if type(bank) is not list or len(bank)!=4:raise ValueError('private four-query bank required')
    return json.loads(public_challenge_bytes({'train':episode['train'],'test':[{'input':bank[source_query_index]['input']}]}))

CAUSAL_DESCRIPTIONS={
 'step_a':'Overlay the separated blueprint panels by coordinate, identify each placement color, and count how often every template is requested.',
 'intermediate':'The input-dependent blueprint, per-template placement counts, recolor legend, and uniquely modal template color.',
 'step_b':'Expand only placements selected by the episode scope into the corresponding template masks and recolor them from the legend.',
 'why_b_depends_on_a':'Under modal_template, the renderer cannot know which spatial blocks survive until the separated placement panels are overlaid and their template-color counts are compared.'}

def causal_settings():return {'placement_scope':'modal_template'}
def causal_intermediate(grid):return family.intermediate(grid)
def counterfactual_program():
    text=program(causal_settings())
    old='''   (define modal-record\n    (pick-max records\n     (lambda (record)\n      (count-if (lambda (placement) (= (third placement) (second record)))\n                placements))))'''
    if text.count(old)!=1:raise ValueError('modal consumer source changed')
    return text.replace(old,'   (define modal-record (first records))')
