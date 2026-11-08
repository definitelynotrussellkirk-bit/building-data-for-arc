import importlib.util
from pathlib import Path
import pytest

P=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location('spokes',P/'adapter.py')
a=importlib.util.module_from_spec(S)
S.loader.exec_module(a)


def test_scenes_and_lesson():
    programs=set()
    for m in ('all','closest_spokes','farthest_spokes'):
        s={'paint_policy':m}
        programs.add(a.program(s))
        for demos in (2,3,6):
            ep=a.generate(13,s,demos=demos,difficulty='hard')
            pairs=ep['train']+ep['test']
            assert len(ep['train'])==demos and len(ep['test'])==4
            assert len({repr(p['input']) for p in pairs})==len(pairs)
            assert (len(pairs[-1]['input']),len(pairs[-1]['input'][0]))==(30,30)
    assert len(programs)==3


def test_invalid():
    for demos in (1,7,True):
        with pytest.raises(ValueError):a.generate(0,{'paint_policy':'all'},demos=demos)
    with pytest.raises(ValueError):a.program({'paint_policy':'x'})
    with pytest.raises(ValueError):a.generate(0,{'paint_policy':'all'},queries=5)
