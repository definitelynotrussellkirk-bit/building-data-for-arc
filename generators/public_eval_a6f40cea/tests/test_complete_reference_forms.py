from pathlib import Path
from arc_repl import parser

def test_complete_reference_forms():
    h=Path(__file__).resolve().parents[1]
    for p in h.rglob('*.rkt'):
        if 'evidence'in p.parts:continue
        f=parser.parse_all(p.read_text());assert len(f)==1 and f[0][0]==parser.Symbol('rule!')
