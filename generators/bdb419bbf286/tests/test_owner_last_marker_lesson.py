import importlib.util
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'generator.py'
spec=importlib.util.spec_from_file_location('owner_bdb',P)
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
def last_marker(grid):
    a=gen._analysis(grid);p=a['marker_3'][-1];q=a['marker_4'][-1]
    return gen._paint_output(len(grid),len(grid[0]),gen._translated(a['shape'],q[0]-p[0],q[1]-p[1]))
def test_seed414_supported_three_demo_four_query_lesson_refutes_last_marker():
    grids=[gen.generate(414,i,difficulty='medium') for i in range(7)]
    assert len({repr(g) for g in grids})==7
    assert any(last_marker(g)!=gen.rule_mirror(g) for g in grids[:3])
    assert all(gen.self_check(g)==[] for g in grids)
def test_automatic_draws_refute_rival_in_each_demo_and_explicit_publics_stay_exact():
    for seed,start in ((0,2),(414,0)):
        for i in range(start,start+7):
            g=gen.generate(seed,i,difficulty='medium')
            assert last_marker(g)!=gen.rule_mirror(g)
    for profile in gen.PUBLIC_PROFILES:
        assert gen.generate(414,0,scene_profile=profile)==gen._PUBLIC_INPUTS[profile]
def test_automatic_profile_provenance_matches_emitted_scene(monkeypatch):
    original=gen.gen_ctx
    contexts=[]
    def capture(**kwargs):
        ctx=original(**kwargs);contexts.append(ctx);return ctx
    monkeypatch.setattr(gen,'gen_ctx',capture)
    grid=gen.generate(414,0,difficulty='medium')
    assert contexts[-1].axis_value('scene_profile')==gen._analysis(grid)['scene_profile']
