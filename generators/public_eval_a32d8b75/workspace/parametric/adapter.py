"""Native unapproved-authoring adapter for the sidebar-stamp family."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from puzzle_generators.base import stable_rng

BASE = Path(__file__).resolve().parent
_NAME = '_sidebar_family_' + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, BASE / 'family.py')
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
assert _SPEC.loader is not None
_SPEC.loader.exec_module(family)


def _scope(settings):
    if type(settings) is not dict or set(settings) != {'scope'} or settings['scope'] not in family.SETTINGS:
        raise ValueError('settings must be exactly scope=all|texture_indexed_component')
    return settings['scope']


def program(settings):
    scope = _scope(settings)
    return (BASE / ('canonical.rkt' if scope == 'all' else 'texture-indexed-component.rkt')).read_text()


def generate(seed, settings, demos, queries):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('invalid seed')
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError('invalid demos')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('invalid queries')
    scope = _scope(settings)
    bank = family.inputs(seed)
    grids = deepcopy(list(bank[:demos]) + list(bank[6:6 + queries]))
    pairs = [{'input': grid, 'output': family.solve(grid, scope)} for grid in grids]
    return {'train': pairs[:demos], 'test': pairs[demos:], 'program_solution': program(settings)}


def presentation_order(presentation_seed):
    if type(presentation_seed) is not int or not 0 <= presentation_seed < 2**63:
        raise ValueError('invalid presentation_seed')
    order = list(range(4))
    stable_rng(presentation_seed, 'sidebar-stamp-query-order', '1').shuffle(order)
    return order


def public_view(episode, source_query_index):
    from reviewer_support import public_challenge_bytes
    if type(source_query_index) is not int or not 0 <= source_query_index < len(episode['test']):
        raise ValueError('invalid source_query_index')
    challenge = {'train': episode['train'], 'test': [{'input': episode['test'][source_query_index]['input']}]}
    return json.loads(public_challenge_bytes(challenge))


CAUSAL_DESCRIPTIONS = {
    'step_a': 'Parse each sidebar, swap its texture colors, count the new top-left color, and use that input-derived count to select one row-major four-connected glyph component.',
    'intermediate': 'For every sidebar: the swapped texture, selected component index and selected glyph-cell mask before rotation.',
    'step_b': 'Rotate that selected mask from the bar cue, replace each retained cell by the swapped texture, and dock the sparse stamp at the dot-selected field corner.',
    'why_b_depends_on_a': 'The renderer cannot know which disconnected glyph cells to stamp until the texture-derived count selects a component; a fixed component or the complete glyph changes the final output.',
}


def causal_settings():
    return {'scope': 'texture_indexed_component'}


def causal_intermediate(grid):
    info = family.analyze(grid)
    rows = []
    for recipe in info['recipes']:
        tile = recipe['swapped']
        count = sum(value == tile[0][0] for row in tile for value in row)
        index = (count - 1) % len(recipe['components'])
        rows.append({'texture_count': count, 'selected_index': index, 'selected_cells': sorted(recipe['components'][index])})
    return rows


def counterfactual_program():
    text = program(causal_settings())
    needle = '(define chosen-index (modulo (- texture-count 1) (length glyph-components)))'
    if text.count(needle) != 1:
        raise ValueError('component selector source changed')
    return text.replace(needle, '(define chosen-index (modulo texture-count (length glyph-components)))')
