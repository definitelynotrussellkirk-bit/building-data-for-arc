from pathlib import Path

import pytest
from arc_repl import parser

HOME = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('relative', ['reference.rkt', 'workspace/parametric/canonical.rkt', 'workspace/parametric/destination.rkt'])
def test_reference_is_one_complete_racket_form(relative):
    forms = parser.parse_all((HOME / relative).read_text())
    assert len(forms) == 1
    assert forms[0][0] == parser.Symbol('rule!')
