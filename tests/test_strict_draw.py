"""Opt-in typed overrides must reject coercion while preserving keyed draws."""
import importlib.util
from pathlib import Path
import sys

import pytest

spec = importlib.util.spec_from_file_location('strict_draw_base', Path(__file__).resolve().parents[1] / 'shared/runtime/puzzle_generators/base.py')
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)


@pytest.mark.parametrize('value', [True, False, '2', 2.0, 2.5, [], {}])
def test_strict_override_rejects_non_integer_without_recording(value):
    ctx = base.GenCtx(seed=3, sample_index=1, overrides={'n': value})
    assert hasattr(ctx, 'draw_int_strict')
    with pytest.raises(TypeError, match='n.*integer'):
        ctx.draw_int_strict('n', 0, 4)
    assert ctx.recorded_draws() == {} and ctx.overrides_used() == {}


def test_strict_draw_preserves_random_draw_and_provenance():
    strict = base.GenCtx(seed=3, sample_index=1)
    permissive = base.GenCtx(seed=3, sample_index=1)
    assert hasattr(strict, 'draw_int_strict')
    assert strict.draw_int_strict('n', 0, 4) == permissive.draw_int('n', 0, 4)
    strict.overrides['n'] = 4
    assert strict.draw_int_strict('n', 0, 4) == 4
    assert strict.overrides_used() == {'n': 4}
    assert strict.draw_bounds('n') == (0, 4)
    strict.overrides['n'] = 5
    with pytest.raises(ValueError, match='outside'):
        strict.draw_int_strict('n', 0, 4)
    permissive.overrides['n'] = '2'
    assert permissive.draw_int('n', 0, 4) == 2

@pytest.mark.parametrize('value',[True,False,1.0,'2',[],{}])
def test_strict_color_preserves_types(value):
    ctx=base.GenCtx(seed=3,sample_index=1,overrides={'color':value})
    with pytest.raises(TypeError):ctx.draw_color_strict('color',exclude={0})
    assert ctx.recorded_draws()=={}


def test_strict_color_keeps_keyed_randomness_and_legacy_compatibility():
    strict=base.GenCtx(seed=3,sample_index=1)
    legacy=base.GenCtx(seed=3,sample_index=1)
    assert strict.draw_color_strict('color',exclude={0})==legacy.draw_color('color',exclude={0})
    legacy.overrides['color']=True
    assert legacy.draw_color('color',exclude={0})==1
