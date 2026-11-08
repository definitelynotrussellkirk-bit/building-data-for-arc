"""Bounded wrong rules for motif identity, selection, scale and alignment."""
DEPENDENCY = {
    'step_a': 'Separate multicolor objects, recover each integer scale, normalize the two motifs, and locate their shared color-mask anchor.',
    'intermediate': 'Input-derived object records containing primitive motif identity, scale, anchor offset, absolute anchor position and motif instance frequencies.',
    'step_b': 'Select the other motif or the rarer motif, then reconstruct it at each recipient scale while preserving the absolute internal anchor.',
    'why_b_depends_on_a': 'The destination footprint depends on the recovered internal anchor, not its outer bounding box. Substituting zero anchor offsets misaligns transferred appendages and changes the executed output on the same input.'
}


def change(source, old, new):
    if source.count(old) != 1:
        raise ValueError('expected one mutation point: ' + old)
    return source.replace(old, new)


def counterfactual(source):
    return change(source, '(define align-bbox #f)', '(define align-bbox #t)')


def programs(adapter, settings):
    selected = adapter.program(settings)
    declaration = "(define replacement '" + settings['replacement'] + ')'

    def policy(name):
        return change(selected, declaration, "(define replacement '" + name + ')')

    return {
        'other_replacement': adapter.program({'replacement': 'minority' if settings['replacement'] == 'swap' else 'swap'}),
        'identity': '(rule! (lambda (g) g))',
        'first_donor': policy('first'),
        'last_donor': policy('last'),
        'majority_donor': policy('majority'),
        'unit_scale': change(selected, '(define preserve-scale #t)', '(define preserve-scale #f)'),
        'bbox_origin': counterfactual(selected),
        'recolor_existing_pixels_only': change(selected, '(if hit (third hit) bg)',
            '(if (= (at g r c) bg) bg (if hit (third hit) (at g r c)))'),
    }
