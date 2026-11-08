"""Regressions for reviewer finding R1: component/color lesson ambiguity."""
import importlib.util
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lesson_probe', HOME/'workspace/lesson_probe.py')
probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
gen = probe.load_generator()


def test_canonical_shortcuts_really_fit_every_canonical_pair():
    pairs = probe.canonical_pairs()
    assert gen.CANONICAL_SHORTCUTS
    failures = {name:[i for i,p in enumerate(pairs) if fn(p['input']) != p['output']]
                for name,fn in gen.CANONICAL_SHORTCUTS.items()}
    assert not {name:bad for name,bad in failures.items() if bad}


def test_color_component_confusion_is_registered_and_witnessed():
    assert 'global_color_components' in gen.CANONICAL_SHORTCUTS
    assert 'global_color_components' in gen.LESSON_COMPETITORS
    assert 'global_color_components' in gen.WITNESS_RIVALS['same_source_color_different_depth']
    assert all(probe.color_group_rival(p['input'])==p['output'] for p in probe.canonical_pairs())


@pytest.mark.parametrize('band', ['easy','medium','hard'])
@pytest.mark.parametrize('start', range(10))
def test_every_cyclic_lesson_teaches_separate_components_of_same_color(band,start):
    grids = [gen.generate(2026,i,difficulty=band) for i in range(start,start+gen.EXAMPLES_NEEDED+1)]
    assert any(probe.color_group_rival(g) != gen.rule_mirror(g) for g in grids[:-1])
    demos = [{'input':g,'output':gen.rule_mirror(g)} for g in grids[:-1]]
    assert gen.lesson_identifiable(demos, {'input':grids[-1]}) == []


def test_explicitly_ambiguous_overridden_lesson_is_rejected():
    # Canonical profiles alone must not conceal missing color-component evidence.
    demos = []
    for i in range(gen.EXAMPLES_NEEDED):
        g=gen.generate(2026,i,color_pattern='distinct')
        demos.append({'input':g,'output':gen.rule_mirror(g)})
    q=gen.generate(2026,5,color_pattern='repeat_depth')
    assert all(probe.color_group_rival(p['input'])==p['output'] for p in demos)
    assert probe.color_group_rival(q)!=gen.rule_mirror(q)
    assert any('global_color_components' in r for r in gen.lesson_identifiable(demos, {'input':q}))


def test_malformed_demo_returns_reasons_instead_of_raising():
    demos=[]
    for i in range(gen.EXAMPLES_NEEDED):
        g=gen.generate(2026,i); demos.append({'input':g,'output':gen.rule_mirror(g)})
    demos[0]={'input':[[0,1],[1]],'output':[[0]]}
    assert gen.lesson_identifiable(demos, {'input':gen.generate(2026,5)})


@pytest.mark.parametrize('band', ['easy','medium','hard'])
def test_canonical_size_anchor_visits_every_scene_color_pair(band):
    # Period seven is coprime to the ten-draw semantic/color cycle. It neither
    # permanently ties the canonical dimensions to one scene nor seed-hunts.
    observed=set()
    for index in range(0,70,7):
        grid=gen.generate(2026,index,difficulty=band)
        axes=gen.observe_overrides(grid)
        assert (len(grid),len(grid[0]))==(11,11)
        observed.add((axes['scene_kind'],axes['color_pattern']))
    assert observed=={(scene,color) for scene in gen.SCENE_KINDS for color in gen.COLOR_PATTERNS}
