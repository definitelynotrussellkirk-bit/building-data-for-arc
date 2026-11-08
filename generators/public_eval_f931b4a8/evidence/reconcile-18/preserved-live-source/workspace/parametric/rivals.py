"""Finite pixel-count, scale, opacity, transpose and empty-pattern competitors."""
from pathlib import Path
import importlib.util
BASE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_quadrant_rival_adapter_'+str(BASE),BASE/'adapter.py')
adapter=importlib.util.module_from_spec(s);s.loader.exec_module(adapter)
NAMES=('reverse_sampling','swap_dimensions','occupied_rows','occupied_columns','first_counter_color',
       'constant_palette','transpose_palette','ignore_stencil','stencil_only','transpose_stencil',
       'first_tile_only','empty_large_hole','multiples_only')
BLOCK='(at g (+ side (quotient r side)) (quotient c side))'
PERIODIC='(at g (+ side (modulo r side)) (modulo c side))'
HC='(for*/sum ((r (range side)) (c (range side))) (if (= (at g r c) 0) 0 1))'
WC='(for*/sum ((r (range side)) (c (range side))) (if (= (at g r (+ side c)) 0) 0 1))'


def program(settings,name):
    if name not in NAMES:raise ValueError('Unknown rival')
    mode=adapter.validate(settings);text=adapter.program(settings)
    if name=='reverse_sampling':return adapter.program({'background_sampling':'periodic' if mode=='block' else 'block'})
    if name=='swap_dimensions':return text.replace(HC,'SWAPPED_COUNTER').replace(WC,HC).replace('SWAPPED_COUNTER',WC)
    if name in ('occupied_rows','occupied_columns','first_counter_color'):
        for original,cell in [(HC,'(at g r c)'),(WC,'(at g r (+ side c))')]:
            if name=='first_counter_color':
                expr=f'(let ((color (for*/first ((r (range side)) (c (range side)) #:when (not (= {cell} 0))) {cell}))) (for*/sum ((r (range side)) (c (range side))) (if (= {cell} color) 1 0)))'
            else:
                outer,inner=('r','c') if name=='occupied_rows' else ('c','r')
                expr=f'(for/sum (({outer} (range side))) (if (for/or (({inner} (range side))) (not (= {cell} 0))) 1 0))'
            text=text.replace(original,expr)
        return text
    if name=='constant_palette':return text.replace(BLOCK,'(at g side 0)').replace(PERIODIC,'(at g side 0)')
    if name=='transpose_palette':return text.replace(BLOCK,'(at g (+ side (quotient c side)) (quotient r side))').replace(PERIODIC,'(at g (+ side (modulo c side)) (modulo r side))')
    if name=='ignore_stencil':return text.replace('(if (= ink 0) (at backing r c) ink)','(at backing r c)')
    if name=='stencil_only':return text.replace('(if (= ink 0) (at backing r c) ink)','ink')
    if name=='transpose_stencil':return text.replace('(at g (+ side (modulo r side)) (+ side (modulo c side)))','(at g (+ side (modulo c side)) (+ side (modulo r side)))')
    if name=='first_tile_only':return text.replace(HC,'side').replace(WC,'side')
    if name=='empty_large_hole':return text.replace('(if has-stencil','(if #t')
    if name=='multiples_only':return text.replace(HC,f'(max 1 (* side (quotient {HC} side)))').replace(WC,f'(max 1 (* side (quotient {WC} side)))')
    raise AssertionError(name)


def solve(grid,settings,name):
    if name not in NAMES:raise ValueError('Unknown rival')
    mode=adapter.validate(settings);side,height,width,palette,stencil=adapter.model.analyze(grid)
    if name=='reverse_sampling':mode='periodic' if mode=='block' else 'block'
    if name=='swap_dimensions':height,width=width,height
    if name in ('occupied_rows','occupied_columns','first_counter_color'):
        values=[]
        for offset in (0,side):
            counter=[row[offset:offset+side] for row in grid[:side]]
            if name=='occupied_rows':n=sum(any(row) for row in counter)
            elif name=='occupied_columns':n=sum(any(row[c] for row in counter) for c in range(side))
            else:
                color=next(v for row in counter for v in row if v)
                n=sum(v==color for row in counter for v in row)
            values.append(n)
        height,width=values
    if name=='first_tile_only':height=width=side
    if name=='multiples_only':height=max(1,side*(height//side));width=max(1,side*(width//side))
    exists=any(v for row in stencil for v in row)
    if name=='empty_large_hole':exists=True
    base=[]
    for r in range(height):
        line=[]
        for c in range(width):
            pr,pc=(r//side,c//side) if mode=='block' and exists else (r%side,c%side)
            if name=='transpose_palette':pr,pc=pc,pr
            color=palette[0][0] if name=='constant_palette' else palette[pr][pc]
            ink=stencil[c%side][r%side] if name=='transpose_stencil' else stencil[r%side][c%side]
            if name=='ignore_stencil':line.append(color)
            elif name=='stencil_only':line.append(ink)
            else:line.append(ink or color)
        base.append(line)
    return base
