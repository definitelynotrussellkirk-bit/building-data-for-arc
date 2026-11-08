"""Focused checks for the disjoint five-rule candidate."""
import importlib.util
from pathlib import Path


def family():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/union_family.py"
    spec = importlib.util.spec_from_file_location("quadrant_union_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_old_programs_and_default_are_exact():
    m = family()
    assert m.program() == m._base.program()
    for setting in m._base.SETTINGS:
        assert m.program(setting) == m._base.program(setting)


def test_matched_inputs_two_demo_teaching_and_count_prefixes():
    m = family()
    for seed in (0, 17, 49):
        episodes = [m.generate(seed, s, 6, 4) for s in m.SETTINGS]
        assert len({repr([p["input"] for p in e["train"] + e["test"]]) for e in episodes}) == 1
        assert len({repr([p["output"] for p in e["train"][:2]]) for e in episodes}) == 5
        for setting, full in zip(m.SETTINGS, episodes):
            short = m.generate(seed, setting, 2, 1)
            assert short["train"] == full["train"][:2]
            assert short["test"] == full["test"][:1]
            assert len(full["test"][-1]["output"]) == 30
