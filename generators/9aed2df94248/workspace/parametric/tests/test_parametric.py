from pathlib import Path
import importlib.util
import pytest

P=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location('panel',P/'adapter.py')
a=importlib.util.module_from_spec(S)
S.loader.exec_module(a)


def test_settings_and_lesson():
    programs=set()
    for mode in ('once','twice','mirror_after'):
        s={'transfer':mode}
        programs.add(a.program(s))
        for count in (2,3,6):
            episode=a.generate(12,s,demos=count,difficulty='hard')
            assert len(episode['train'])==count
            assert len(episode['test'])==4
            all_pairs=episode['train']+episode['test']
            assert len({repr(x['input']) for x in all_pairs})==len(all_pairs)
            assert all(len(x['input'])<=30 and len(x['input'][0])<=30 for x in all_pairs)
            assert len(all_pairs[-1]['input'])==30 and len(all_pairs[-1]['input'][0])==30
    assert len(programs)==3


def test_invalid_counts_settings():
    for val in (1,7,True):
        with pytest.raises(ValueError):a.generate(0,{'transfer':'once'},demos=val)
    with pytest.raises(ValueError):a.program({'transfer':'invalid'})
    with pytest.raises(ValueError):a.generate(0,{'transfer':'once'},queries=3)


def test_transform_code_not_sample_index_schedule():
    # A position-only rival cannot know the transformation: each scene has
    # its own random A->B code, even at a fixed demonstration index.
    codes = {a.prototype._sample(seed,0,6,'medium')[2] for seed in range(20)}
    assert len(codes) >= 3
    for seed in range(10):
        code0=a.prototype._sample(seed,0,6,'medium')[2]
        code1=a.prototype._sample(seed,1,6,'medium')[2]
        assert code0 != code1
