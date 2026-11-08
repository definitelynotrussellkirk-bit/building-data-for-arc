"""Executable, total-on-grammar hypotheses and an audited intervention."""
from pathlib import Path

DEPENDENCY={
 'step_a':'Recover consistent fragment translations from shared colored components and merge the observed cells into one cropped drawing.',
 'intermediate':'The reconstructed drawing, including the two endpoint coordinates of each color after deduplication and translation.',
 'step_b':'For colors with exactly two aligned occurrences and an empty intervening span, fill that span in the reconstructed drawing.',
 'why_b_depends_on_a':'The endpoints live in separate scattered fragments; only the recovered translations put them on the common route. Using raw coordinates leaves the reconstructed route unfilled.'
}

def programs(adapter,settings):
    default=adapter.program({'finish_rule':'assemble'});chosen=adapter.program(settings)
    return {
      'other_setting':adapter.program({'finish_rule':'assemble' if settings['finish_rule']!='assemble' else 'assemble_then_bridge'}),
      'identity':'(rule! (lambda (g) g))',
      'crop_input':'(rule! (crop-to-content g (mode g -1)))',
      'largest_fragment':'(rule! (let* ([bg (mode g -1)] [os (objects-multicolor g bg)] [o (first (sort os > #:key obj-size))]) (crop-object g o)))',
      'no_whole_component_anchor':chosen.replace('(and (> score 0) anchor)','(and (> score 0) consistent)'),
      'transparent_observed_background':chosen.replace('(or (= av -1) (= bv -1) (= av bv))','(or (= av -1) (= bv -1) (= av bg) (= bv bg) (= av bv))'),
      'horizontal_relay_only':chosen.replace('[same-c (= (second p) (second q))]','[same-c #f]'),
      'vertical_relay_only':chosen.replace('[same-r (= (first p) (first q))]','[same-r #f]'),
      'raw_endpoint_coordinates':counterfactual(chosen),
    }

def counterfactual(source):
    old='(define points (find-color assembled color))'
    new='(define points (filter (lambda (p) (and (< (first p) (rows assembled)) (< (second p) (cols assembled)))) (find-color g color)))'
    if source.count(old)!=1:raise ValueError('endpoint intermediate source changed')
    return source.replace(old,new)


def intermediate(adapter,pair):
    model=adapter._model; assembled=model.assemble(pair['input']); bg=model.background(pair['input'])
    from collections import Counter
    counts=Counter(v for row in assembled for v in row if v!=bg)
    endpoints={str(color):[[r,c] for r,row in enumerate(assembled) for c,v in enumerate(row) if v==color] for color,n in counts.items() if n==2}
    raw={color:[[r,c] for r,row in enumerate(pair['input']) for c,v in enumerate(row) if str(v)==color] for color in endpoints}
    return {'assembled_endpoints':endpoints,'raw_endpoints':raw,'assembled_shape':[len(assembled),len(assembled[0])]}
