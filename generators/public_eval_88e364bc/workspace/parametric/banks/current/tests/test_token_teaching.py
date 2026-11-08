"""Retain the three independently discovered token-obstacle teaching failures."""
from pathlib import Path
import importlib.util

import pytest

HOME=Path(__file__).resolve().parents[1]


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sources():
    return load(HOME/"generator.py","token_teaching_base"),load(HOME/"workspace/parametric/adapter.py","token_teaching_adapter")


def static_obstacle_prediction(base,g,mode):
    parsed=base.parse(g);out=[row[:] for row in g]
    all_tokens={tuple(p) for p in parsed["tokens"]}
    for r,c in all_tokens:out[r][c]=0
    for region in parsed["regions"]:
        dr,dc=region["direction"]
        if mode=="toward_tail":dr,dc=-dr,-dc
        for start in region["tokens"]:
            cells={tuple(p) for p in region["cells"]}-(all_tokens-{tuple(start)})
            r,c=start
            while ((r+dr,c+dc) in cells and
                   (not dr or not dc or ((r+dr,c) in cells and (r,c+dc) in cells))):
                r,c=r+dr,c+dc
            out[r][c]=4
    return out


@pytest.mark.parametrize("seed",[7,47,257])
@pytest.mark.parametrize("mode",["toward_head","toward_tail"])
def test_minimum_demos_refute_original_tokens_as_static_obstacles(sources,seed,mode):
    base,adapter=sources
    lesson=adapter.generate(seed,{"motion":mode},2,4)
    assert any(static_obstacle_prediction(base,p["input"],mode)!=p["output"] for p in lesson["train"])
