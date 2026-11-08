from pathlib import Path
import importlib.util,json

def test_ordinary_draws_do_not_repeat_after_four():
    p=Path(__file__).resolve().parents[1]/'generator.py'
    s=importlib.util.spec_from_file_location('base_novelty',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    for seed in (17,29):
        grids=[m.generate(seed,i,difficulty=None)for i in range(8)]
        assert len({json.dumps(g)for g in grids})==8
        assert all(m.self_check(g)==[]for g in grids)
        assert grids==[m.generate(seed,i,difficulty=None)for i in range(8)]
