"""Total, independently executable finite rivals for shape-conditioned voting."""
from collections import Counter
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_vote_rivals_adapter_'+str(BASE),BASE/'adapter.py')
adapter=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(adapter)
NAMES=('reverse_vote','translation_only','rotation_only','area_only','global_vote',
       'lowest_color','highest_color','first_color','last_color','blank_panel','first_five_classes')
MATCH='(member (sort (normalize-cells x) cell<) (all-transforms y))'
CHOOSE='(if most-frequent (pick-max counts second) (pick-min counts second))'
PAINT='''(for/fold ((out canvas)) ((entry winner-table))
     (recolor-cells out (first entry) (second entry)))'''

def solve(g,settings,name):
    if name not in NAMES:raise ValueError('Unknown rival')
    mode=adapter.validate(settings);m=adapter.model;info=m.analyze(g)
    if name=='reverse_vote':return m.solve(g,'least_frequent'if mode=='most_frequent'else'most_frequent')
    if name=='blank_panel':return [row[:]for row in info['canvas']]
    selected=list(dict.fromkeys(m.shape_key(h)for h in info['holes']))[:5]
    def key(cells):
        if name=='translation_only':return m.normalize(cells)
        if name=='rotation_only':return min(m.transform(cells,i)for i in range(4))
        if name=='area_only':return len(cells)
        if name=='global_vote':return 0
        return m.shape_key(cells)
    colors=[]
    for hole in info['holes']:
        matching=[o for o in info['clues']if key(o['cells'])==key(hole)];counts=Counter(o['color']for o in matching)
        if not matching or(name=='first_five_classes'and m.shape_key(hole)not in selected):color=info['bg']
        elif name=='lowest_color':color=min(counts)
        elif name=='highest_color':color=max(counts)
        elif name=='first_color':color=matching[0]['color']
        elif name=='last_color':color=matching[-1]['color']
        else:color=m.choose_color(counts,mode)
        colors.append(color)
    return m.render(info,colors)

def replace(text,old,new):
    if text.count(old)!=1:raise ValueError('Rival splice no longer matches source')
    return text.replace(old,new)

def program(settings,name):
    if name not in NAMES:raise ValueError('Unknown rival')
    if name=='reverse_vote':return adapter.program({'vote':'least_frequent'if adapter.validate(settings)=='most_frequent'else'most_frequent'})
    text=adapter.program(settings)
    if name=='blank_panel':return replace(text,PAINT,'canvas')
    if name=='translation_only':text=replace(text,MATCH,'(equal? (sort (normalize-cells x) cell<) (sort (normalize-cells y) cell<))')
    if name=='rotation_only':text=replace(text,MATCH,'''(member (sort (normalize-cells x) cell<)
       (map (lambda (cells) (sort (normalize-cells cells) cell<))
        (list y (rotate-cells-cw y) (rotate-cells-cw (rotate-cells-cw y)) (rotate-cells-cw (rotate-cells-cw (rotate-cells-cw y))))))''')
    if name=='area_only':text=replace(text,MATCH,'(= (length x) (length y))')
    if name=='global_vote':text=replace(text,MATCH,'#t')
    choice=CHOOSE
    if name=='lowest_color':choice='(pick-min counts first)'
    if name=='highest_color':choice='(pick-max counts first)'
    if name=='first_color':choice='(list (obj-color (first matching)) 0)'
    if name=='last_color':choice='(list (obj-color (last matching)) 0)'
    text=replace(text,CHOOSE,f'(if (null? counts) (list bg 0) {choice})')
    if name=='first_five_classes':
        definitions='''(define distinct-shapes
     (for/fold ((known '())) ((hole holes))
      (if (ormap (lambda (cells) (matches? (obj-cells hole) cells)) known)
          known (append known (list (obj-cells hole))))))
   (define selected-shapes (take distinct-shapes (min 5 (length distinct-shapes))))
   (define winner-table'''
        text=replace(text,'(define winner-table',definitions)
        text=replace(text,'(list (obj-cells hole) (first chosen))',
           '(list (obj-cells hole) (if (ormap (lambda (cells) (matches? (obj-cells hole) cells)) selected-shapes) (first chosen) bg))')
    return text
