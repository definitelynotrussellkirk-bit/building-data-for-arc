from pathlib import Path
import importlib.util,sys
import pytest

def test_optional_difficulty_and_unknown_controls():
    p=Path(__file__).resolve().parents[1]/'generator.py'
    s=importlib.util.spec_from_file_location('wire_base_defaults',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
    for seed,index in ((17,0),(43,1)):
        assert m.generate(seed,index,difficulty=None)==m.generate(seed,index,difficulty='medium')
    with pytest.raises(ValueError):m.generate(17,0,imaginary=1)
