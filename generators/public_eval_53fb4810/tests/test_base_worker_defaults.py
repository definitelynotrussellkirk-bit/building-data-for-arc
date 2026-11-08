from pathlib import Path
import importlib.util

def test_optional_difficulty_uses_medium_input_stream():
    p=Path(__file__).resolve().parents[1]/'generator.py'
    s=importlib.util.spec_from_file_location('base_default',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    for seed,index in ((17,0),(43,1)):
        assert m.generate(seed,index,difficulty=None)==m.generate(seed,index,difficulty='medium')
        assert m.self_check(m.generate(seed,index,difficulty=None))==[]
