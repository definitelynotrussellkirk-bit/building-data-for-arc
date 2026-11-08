"""Finite executable rivals, not a proof of universal identifiability."""
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_selector_rivals_adapter_'+str(BASE),BASE/'adapter.py')
adapter=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(adapter)
NAMES=('opposite_assignment','copy_first','copy_second','union','blank','erase_divider','second_priority',
       'eight_neighbor','larger_region','top_left_region','top_half','left_half','height_cap_20')
REGION='''(define region (connected-region selector (first marker) (second marker)
                    (lambda (r c v) (not (member (list r c) barrier))) 4))'''
PASTE='(paste g result top (fourth starts))'

def solve(g,settings,name):
    if name not in NAMES:raise ValueError('Unknown rival')
    mode=adapter.validate(settings);m=adapter.model;info=m.analyze(g)
    if name=='blank' or(name=='height_cap_20' and info['ph']>20):return [row[:] for row in g]
    if name=='height_cap_20':return adapter.solve(g,settings)
    if name in ('copy_first','copy_second','union'):
        out=[row[:] for row in g];a,b=info['sources'];bg=info['bg']
        for r in range(info['ph']):
            for c in range(info['pw']):
                v=a[r][c] if name=='copy_first' else b[r][c] if name=='copy_second' else a[r][c] if a[r][c]!=bg else b[r][c]
                out[info['top']+r][info['runs'][3][0]+c]=v
        return out
    region=info['region']
    if name=='eight_neighbor':region=next(x for x in m.components(info['universe']-info['barrier'],8)if info['marker']in x)
    if name=='larger_region' and len(region)<len(info['other']):region=info['other']
    if name=='top_left_region':
        start=min(info['universe']-info['barrier']);region=next(x for x in m.components(info['universe']-info['barrier'])if start in x)
    if name=='top_half':region={(r,c)for r,c in info['universe']-info['barrier']if 2*r<info['ph']}
    if name=='left_half':region={(r,c)for r,c in info['universe']-info['barrier']if 2*c<info['pw']}
    return m.render(g,info,region,(mode=='marker_first')!=(name=='opposite_assignment'),
                    boundary=name!='erase_divider',first_priority=name!='second_priority')

def replace(text,old,new):
    if text.count(old)!=1:raise ValueError('Rival splice no longer matches source')
    return text.replace(old,new)

def program(settings,name):
    if name not in NAMES:raise ValueError('Unknown rival')
    text=adapter.program(settings)
    if name=='opposite_assignment':return adapter.program({'assignment':'marker_second'if adapter.validate(settings)=='marker_first'else'marker_first'})
    if name=='copy_first':return replace(text,PASTE,'(paste g source-a top (fourth starts))')
    if name=='copy_second':return replace(text,PASTE,'(paste g source-b top (fourth starts))')
    if name=='union':return replace(text,PASTE,'(paste g (overlay source-b source-a bg) top (fourth starts))')
    if name=='blank':return '(rule! (lambda (g) g))\n'
    if name=='erase_divider':return replace(text,'(if (not (= x bg)) x y)','(if on bg (if (not (= x bg)) x y))')
    if name=='second_priority':return replace(text,'(if (not (= x bg)) x y)','(if (not (= y bg)) y x)')
    if name=='eight_neighbor':return replace(text,REGION,REGION.replace(' 4))',' 8))'))
    if name=='larger_region':
        new=REGION.replace('(define region','(define marked-region')+'''
   (define opposite-region (filter (lambda (p) (and (not (member p barrier)) (not (member p marked-region)))) (grid-positions selector)))
   (define region (if (< (length marked-region) (length opposite-region)) opposite-region marked-region))'''
        return replace(text,REGION,new)
    if name=='top_left_region':
        new='''(define start (first (filter (lambda (p) (not (member p barrier))) (grid-positions selector))))
   (define region (connected-region selector (first start) (second start) (lambda (r c v) (not (member (list r c) barrier))) 4))'''
        return replace(text,REGION,new)
    if name in ('top_half','left_half'):
        test='(< (* 2 (first p)) height)'if name=='top_half'else'(< (* 2 (second p)) width)'
        return replace(text,REGION,f'(define region (filter (lambda (p) (and (not (member p barrier)) {test})) (grid-positions selector)))')
    return replace(text,PASTE,'(if (> height 20) g (paste g result top (fourth starts)))')
