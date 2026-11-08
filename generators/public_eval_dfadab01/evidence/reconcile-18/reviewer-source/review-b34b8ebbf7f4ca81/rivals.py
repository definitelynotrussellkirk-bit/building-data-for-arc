"""Finite explicit competitors; a rival error is never evidence of refutation."""
from pathlib import Path
BASE=Path(__file__).resolve().parent

def patch(text,old,new):
    if text.count(old)!=1:raise ValueError('Rival patch no longer matches exactly once')
    return text.replace(old,new)

def _original_programs(mode):
    canonical=(BASE/'canonical.rkt').read_text()
    high=(BASE/'highlight_largest.rkt').read_text()
    if mode=='decode':
        return {
          'keep_legend_code':patch(canonical,'(not (legend? p))','#t'),
          'keep_exemplar_pixels':patch(canonical,'(empty-grid (rows g) (cols g))','g'),
          'repeat_symbol_corner':patch(canonical,'(pixel (at g (first p) (second p)) i j)','(pixel (at g (first p) (second p)) 0 0)'),
          'all_square_symbols':patch(canonical,'(pixel (at g (first p) (second p)) i j)','(pixel 2 i j)'),
          'highlight_unconditionally':high,
        }
    if mode!='highlight_largest':raise ValueError('Unknown setting')
    bbox='(lambda (o) (* (obj-h o) (obj-w o)))'
    markers='''(lambda (o) (count-if (lambda (p)
        (and (<= (obj-r1 o) (first p) (obj-r2 o))
             (<= (obj-c1 o) (second p) (obj-c2 o)))) targets))'''
    return {
       'skip_highlight':canonical,
       'largest_bounding_box':patch(high,'(pick-max groups obj-size)',f'(pick-max groups {bbox})'),
       'most_raw_markers':patch(high,'(pick-max groups obj-size)',f'(pick-max groups {markers})'),
       'smallest_component':patch(high,'(pick-max groups obj-size)','(pick-min groups obj-size)'),
       'first_component':patch(high,'(pick-max groups obj-size)','(first groups)'),
       'last_component':patch(high,'(pick-max groups obj-size)','(last groups)'),
       'raw_geometry':patch(high,'(objects-multicolor decoded 0)','(objects-multicolor g 0)'),
       'same_color_four_connected':patch(high,'(objects-multicolor decoded 0)','(objects decoded 0)'),
    }


def programs(mode):
    rivals=_original_programs(mode)
    source=(BASE/('canonical.rkt' if mode=='decode' else 'highlight_largest.rkt')).read_text()
    rivals['reverse_painter']=patch(source,'(p targets)','(p (reverse targets))')
    rivals['first_writer_wins']=patch(source,
        '(and (> v 0) (in-bounds? r c (rows g) (cols g)))',
        '(and (> v 0) (in-bounds? r c (rows g) (cols g)) (= (at out r c) 0))')
    return rivals
