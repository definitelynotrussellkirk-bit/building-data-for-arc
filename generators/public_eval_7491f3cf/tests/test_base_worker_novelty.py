from pathlib import Path
import importlib.util,json,sys

def test_ordinary_stream_extends_four_query_bank():
    p=Path(__file__).resolve().parents[1]/'generator.py'
    s=importlib.util.spec_from_file_location('panel_novelty',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
    for seed in (17,29):
        draws=[m.generate(seed,i,difficulty=None)['input']for i in range(8)]
        assert len({json.dumps(g)for g in draws})==8
