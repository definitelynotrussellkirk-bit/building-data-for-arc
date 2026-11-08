"""Pure regressions for exported-lesson count, uniqueness, and rival decisions."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from reviewer_support import find_root


def checker():
    root = find_root(__file__)
    choices = [root / 'generators/d377a54f20c6/workspace/check_four_queries.py',
               root / 'puzzle_generators/per_puzzle/d377a54f20c6/workspace/check_four_queries.py']
    source = next((p for p in choices if p.is_file()), choices[0])
    assert source.is_file(), 'four-query checker implementation is missing'
    spec = importlib.util.spec_from_file_location('four_query_probe_under_test', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lesson():
    return {'train': [{'input': [[0]], 'output': [[9]]},
                      {'input': [[1]], 'output': [[9]]},
                      {'input': [[2]], 'output': [[9]]}],
            'test': [{'input': [[3]], 'output': [[9]]},
                     {'input': [[4]], 'output': [[9]]},
                     {'input': [[5]], 'output': [[9]]},
                     {'input': [[6]], 'output': [[9]]}]}


def test_actual_counts_cannot_be_replaced_by_requested_counts():
    tool = checker()
    episode = lesson()
    episode['test'].pop()
    result = tool.inspect_layout(episode, demos=3, queries=4)
    assert result['query_count'] == 3
    assert not result['passed']
    assert 'query_count' in result['errors']


@pytest.mark.parametrize('replacement,expected_error', [([[3]], 'duplicate_query_input'),
                                                       ([[1]], 'demo_query_input_reuse')])
def test_duplicate_and_reused_queries_are_rejected(replacement, expected_error):
    tool = checker()
    episode = lesson()
    episode['test'][1]['input'] = replacement
    result = tool.inspect_layout(episode, demos=3, queries=4)
    assert not result['passed']
    assert expected_error in result['errors']


def test_distinct_three_demo_four_query_lesson_passes_structure():
    result = checker().inspect_layout(lesson(), demos=3, queries=4)
    assert result['passed']
    assert result['demo_count'] == 3
    assert result['query_count'] == 4
    assert result['distinct_query_inputs'] == 4


def test_query_disagreement_never_disqualifies_a_demo_fitting_rival():
    result = checker().assess_predictions([[[1]], [[2]]], [[[3]], [[4]]],
                                           [[[1]], [[2]], [[8]], [[4]]])
    assert result['fits_demonstrations'] is True
    assert result['ambiguous_query_indices'] == [0]


def test_rival_refuted_by_demo_cannot_create_query_ambiguity():
    result = checker().assess_predictions([[[1]], [[2]]], [[[3]], [[4]]],
                                           [[[1]], [[8]], [[8]], [[8]]])
    assert result['fits_demonstrations'] is False
    assert result['ambiguous_query_indices'] == []
    assert result['refuting_demo_indices'] == [1]


def test_exported_query_label_mismatch_is_not_ignored():
    pairs = [{'input': [[0]], 'output': [[1]]}, {'input': [[2]], 'output': [[8]]}]
    assert checker().label_mismatches(pairs, [[[1]], [[3]]]) == [1]


def test_rivals_come_from_both_live_declarations_without_name_loss():
    def first(grid):
        return grid
    def second(grid):
        return grid
    module = SimpleNamespace(CANONICAL_SHORTCUTS={'shared': first},
                             LESSON_COMPETITORS={'shared': first, 'new_rival': second})
    rivals, declarations = checker().declared_rivals(module)
    assert set(rivals) == {'shared', 'new_rival'}
    assert declarations['shared'] == ['CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS']


def test_json_lines_are_all_checked():
    raw = json.dumps(lesson()) + '\n' + json.dumps(lesson()) + '\n'
    assert len(checker().parse_episodes(raw)) == 2
