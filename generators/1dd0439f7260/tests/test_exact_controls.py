"""Focused regressions for source-bound override and shortcut findings."""
import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'generator.py'
S=importlib.util.spec_from_file_location('base_markers',P)
a=importlib.util.module_from_spec(S)
S.loader.exec_module(a)


def test_exact_shapes_counts_colors_across_difficulty():
    for difficulty in (None,'easy','medium','hard'):
        for size in (5,14):
            for ncolors in (2,3):
                grid=a.generate(0,1,difficulty=difficulty,grid_h=size,grid_w=size,
                                n_row_marks=min(6,size-1),n_col_marks=min(6,size-1),
                                palette_size=ncolors,n_distinct_colors=ncolors)
                assert (len(grid),len(grid[0]))==(size,size)
                assert sum(x==1 for x in grid[0])==min(6,size-1)
                assert sum(row[0]==2 for row in grid)==min(6,size-1)
                assert len({v for row in grid for v in row if v!=0})==ncolors
                assert a.self_check(grid)==[]


def test_degenerate_dims_and_contradictions():
    for texture in a.DEGENERATE_TEXTURES:
        g=a.generate(17,0,texture=texture,grid_h=13,grid_w=11)
        assert (len(g),len(g[0]))==(13,11)
        for count in (2,3):
            exact=a.generate(17,0,texture=texture,grid_h=13,grid_w=11,
                             palette_size=count,n_distinct_colors=count)
            assert len({x for row in exact for x in row if x})==count
    with pytest.raises(ValueError): a.generate(0,0,texture='no_row_marks',n_row_marks=3)
    with pytest.raises(ValueError): a.generate(0,0,texture='no_col_marks',n_col_marks=3)


def test_strict_controls_and_content_diversity():
    for kwargs in ({'grid_h':True},{'grid_w':20},{'grid_h':5,'n_col_marks':6},
                   {'palette_size':2,'n_distinct_colors':3},{'unknown':1},
                   {'position_bias':'ignored'}):
        with pytest.raises(ValueError):a.generate(0,0,**kwargs)
    grids=[a.generate(s,0) for s in range(32)]
    assert sum(len({x for row in g for x in row if x})==3 for g in grids)>=12
    assert len({repr(g) for g in grids})==32
