from pathlib import Path
from arc_repl import parser

def test_complete_reference_forms():
    home=Path(__file__).resolve().parents[1]
    for rel in ['reference.rkt','workspace/parametric/canonical.rkt']:
        forms=parser.parse_all((home/rel).read_text())
        assert len(forms)==1 and forms[0][0]==parser.Symbol('rule!')
