"""Declared integer choices contribute to draw envelopes, not occupancy claims."""
import ast
from pathlib import Path
import re
from types import SimpleNamespace


def probe():
    source = Path(__file__).resolve().parents[1] / 'shared/tools/generator_defect_lint.py'
    tree = ast.parse(source.read_text())
    nodes = [node for node in tree.body if
             isinstance(node, ast.FunctionDef) and node.name in ('_parse_valid', 'probe_axis_honesty')
             or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_VALID_RANGE_RE' for t in node.targets)]
    namespace = {'re': re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['probe_axis_honesty']


def test_unselected_invalid_choice_is_still_a_provenance_error():
    context = SimpleNamespace(draw_bounds_store={'width': (3, 3)},
                              draw_options_store={'width': (3, 99)}, recorded_draws=lambda: {'width': 3})
    errors, warnings = probe()(SimpleNamespace(AXES={'width': {'valid': '3..10'}}), [context])
    assert errors and '[3, 99]' in errors[0]


def test_choice_only_provenance_cannot_bypass_declared_range():
    context = SimpleNamespace(draw_bounds_store={}, draw_options_store={'width': (3, 99)},
                              recorded_draws=lambda: {'width': 3})
    errors, warnings = probe()(SimpleNamespace(AXES={'width': {'valid': '3..10'}}), [context])
    assert errors and '[3, 99]' in errors[0]


def test_legal_integer_envelope_is_not_falsely_narrow():
    context = SimpleNamespace(draw_bounds_store={'width': (3, 3)}, draw_options_store={'width': (3, 10)},
                              recorded_draws=lambda: {'width': 3})
    errors, warnings = probe()(SimpleNamespace(AXES={'width': {'valid': '3..10'}}), [context])
    assert errors == [] and warnings == []
