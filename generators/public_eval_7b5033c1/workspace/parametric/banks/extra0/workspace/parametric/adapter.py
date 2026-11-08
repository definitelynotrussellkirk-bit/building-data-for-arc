"""Native adapter. Every non-runtime source/resource lives beside this file."""
from pathlib import Path
import importlib.util
import json

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('_7b5033c1_native_family', HERE/'family.py')
family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(family)
SETTINGS = family.FINISHES


def checked(settings):
    if (type(settings) is not dict or set(settings) != {'finish'}
        or type(settings['finish']) is not str or settings['finish'] not in SETTINGS):
        raise ValueError('Expected exactly one declared finish setting')
    return settings['finish']


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'Cannot safely specialize unique program anchor {old!r}')
    return source.replace(old, new)


def program(settings):
    finish = checked(settings)
    canonical = (HERE/'canonical.rkt').read_text()
    if finish == 'unroll':
        return canonical
    return replace_once(canonical, "(define finish 'unroll)", "(define finish 'length_addressed_run)")


def generate(seed, settings, demos, queries):
    finish = checked(settings)
    for value, lo, hi, name in ((seed, 0, 2**63-1, 'seed'), (demos, 2, 6, 'demos'), (queries, 1, 4, 'queries')):
        family._integer(value, lo, hi, name)
    # Build the maximum bank first: visible counts cannot change sampling.
    all_pairs = []
    for index in list(range(6)) + list(range(1000, 1004)):
        g = family.generate(seed, index, stress=index == 1000)
        all_pairs.append({'input': g, 'output': family.solve(g, finish)})
    if len({json.dumps(p['input'], separators=(',', ':')) for p in all_pairs}) != len(all_pairs):
        raise ValueError('Sampling produced duplicate visible inputs')
    return {'train': all_pairs[:demos], 'test': all_pairs[6:6+queries],
            'program_solution': program(settings)}


def rival_programs(settings):
    selected = program(settings)
    rivals = {'other_setting': program({'finish': SETTINGS[1-SETTINGS.index(checked(settings))]})}
    for mode in ('row_major', 'column_major', 'reverse', 'histogram'):
        rivals[mode] = replace_once(selected, "(define trace-mode 'path)", f"(define trace-mode '{mode})")
    if checked(settings) == 'length_addressed_run':
        for selector in (1, 2, 3, 4, 'largest', 'last'):
            value = str(selector) if type(selector) is int else "'"+selector
            rivals[f'select_{selector}'] = replace_once(selected, "(define selector 'header)", f'(define selector {value})')
        rivals['paint_all_matching'] = replace_once(selected, "(define paint-mode 'run)", "(define paint-mode 'all_matching)")
        rivals['all_header_color'] = replace_once(
            selected, '(else (length (first runs)))',
            '(else (length (filter (lambda (c) (= c (first sequence))) sequence)))')
    return rivals
