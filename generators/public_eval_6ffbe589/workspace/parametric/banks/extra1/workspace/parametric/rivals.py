"""Executable finite alternatives used only for authoring audits."""
import copy
import importlib.util
from pathlib import Path
import sys
p=Path(__file__).with_name('adapter.py');spec=importlib.util.spec_from_file_location('_6ff_rival_adapter',p)
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
RIVALS=('identity','opposite','once','twice','thrice','cap_three','presence','color_rank','global_count','ignore_long','size_gate','four_colors_only')

def rival(grid,direction,name):
    if name not in RIVALS:raise ValueError(name)
    st=a.measure(grid); counts=st['counts']; total=sum(counts.values())
    for i,v in enumerate(sorted(counts)):
        count=counts[v]
        counts[v]={'identity':0,'opposite':count,'once':1,'twice':2,'thrice':3,
                   'cap_three':min(count,3),'presence':int(count>0),'color_rank':i,
                   'global_count':total,'ignore_long':count if count<=4 else 0,
                   'size_gate':count if st['box'][2]-st['box'][0]+1<=20 else 0,
                   'four_colors_only':0 if len(counts)>4 and v==max(counts) else count}[name]
    if name=='opposite':direction='counterclockwise' if direction=='clockwise' else 'clockwise'
    return a.render(grid,st,direction)

def program(direction,name):
    if name not in RIVALS:raise ValueError(name)
    if name=='opposite':return a.program({'direction':'counterclockwise' if direction=='clockwise' else 'clockwise'})
    code=a.program({'direction':direction})
    expr={'identity':'0','once':'1','twice':'2','thrice':'3',
          'cap_three':'(min (second entry) 3)','presence':'(if (> (second entry) 0) 1 0)',
          'color_rank':'(count-if (lambda (v) (< v (first entry))) colors)',
          'global_count':'(length outs)','ignore_long':'(if (> (second entry) 4) 0 (second entry))',
          'size_gate':'(if (> n 20) 0 (second entry))',
          'four_colors_only':'(if (and (> (length colors) 4) (= (first entry) (last colors))) 0 (second entry))'}[name]
    return code.replace('(define turns (modulo (* turn-sign (second entry)) 4))',
                        f'(define turns (modulo (* turn-sign {expr}) 4))')
