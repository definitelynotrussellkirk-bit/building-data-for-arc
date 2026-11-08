"""Finite executable compositing mistakes; not evidence of universal uniqueness."""
from pathlib import Path
import importlib.util
import sys
p=Path(__file__).with_name('adapter.py');s=importlib.util.spec_from_file_location('_9385_rival_adapter',p)
a=importlib.util.module_from_spec(s);sys.modules[s.name]=a;s.loader.exec_module(a)
RIVALS=('identity','opposite','fill_key','erase_corners','restore_markers','ascending_keys',
        'descending_keys','first_two','ignore_solids','skip_background_fills','skip_nonblack','literal_zero','ignore_thin')

def rival(g,priority,name):
    if name not in RIVALS:raise ValueError(name)
    if name=='identity':return [row[:] for row in g]
    st=a.measure(g);bg=st['background']
    if name=='opposite':priority='bottom_priority' if priority=='top_priority' else 'top_priority'
    elif name=='fill_key':
        for layer in st['layers']:layer['fill']=layer['key']
    elif name=='erase_corners':
        for layer in st['layers']:layer['markers']=[]
    elif name in ('ascending_keys','descending_keys'):
        st['layers'].sort(key=lambda x:x['key'],reverse=name=='descending_keys')
    elif name=='first_two':
        keep={entry[0] for entry in st['entries'][:2]};st['layers']=[x for x in st['layers'] if x['key'] in keep]
    elif name=='ignore_solids':st['layers']=[x for x in st['layers'] if x['markers']]
    elif name=='ignore_thin':st['layers']=[x for x in st['layers'] if not x['markers'] or min(x['box'][2]-x['box'][0]+1,x['box'][3]-x['box'][1]+1)>2]
    elif name=='skip_background_fills':st['layers']=[x for x in st['layers'] if x['fill']!=bg]
    elif name=='skip_nonblack' and bg!=0:return [row[:] for row in g]
    elif name=='literal_zero':
        raw=dict(st['entries'])
        for layer in st['layers']:layer['fill']=raw[layer['key']]
    out=a.render(g,st,priority)
    if name=='restore_markers':
        for r,row in enumerate(g):
            for c,v in enumerate(row):
                if v!=bg:out[r][c]=v
    return out

def program(priority,name):
    if name not in RIVALS:raise ValueError(name)
    if name=='identity':return '(rule! (lambda (g) g))'
    if name=='opposite':return a.program({'priority':'bottom_priority' if priority=='top_priority' else 'top_priority'})
    code=a.program({'priority':priority})
    old='(define draw-order (if earlier-wins (reverse entries) entries))'
    order='(if earlier-wins (reverse entries) entries)'
    if name=='fill_key':return code.replace('(define fill-color (if (= (second entry) 0) bg (second entry)))','(define fill-color key)')
    if name=='erase_corners':return code.replace('(define markers (second record))',"(define markers '())")
    if name=='restore_markers':return code.replace('     result)))))','     (grid-from-fn h w (lambda (r c) (if (= (at g r c) bg) (at result r c) (at g r c)))))))))')
    if name in ('ascending_keys','descending_keys'):
        cmp='<' if name=='ascending_keys' else '>'
        return code.replace(old,f'(define draw-order (let ((es (sort entries (lambda (a b) ({cmp} (first a) (first b)))))) (if earlier-wins (reverse es) es)))')
    if name=='first_two':return code.replace(old,'(define draw-order (let ((es (take entries (min 2 (length entries))))) (if earlier-wins (reverse es) es)))')
    if name=='ignore_solids':return code.replace("(define solid-records (for/list ((obj solids)) (list (obj-bbox obj) '())))","(define solid-records '())")
    if name=='skip_background_fills':return code.replace(old,'(define draw-order (filter (lambda (entry) (and (not (= (second entry) 0)) (not (= (second entry) bg)))) '+order+'))')
    if name=='skip_nonblack':return code.replace(old,'(define draw-order (if (= bg 0) '+order+" '()))")
    if name=='ignore_thin':return code.replace("(list (list (bbox-of-cells ps) ps))","(let ((b0 (bbox-of-cells ps))) (if (<= (min (+ 1 (- (third b0) (first b0))) (+ 1 (- (fourth b0) (second b0)))) 2) '() (list (list b0 ps))))")
    if name=='literal_zero':return code.replace('(define fill-color (if (= (second entry) 0) bg (second entry)))','(define fill-color (second entry))')
    raise ValueError(name)
