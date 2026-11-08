"""Reference-labeled counterexamples and finite teaching-schedule regressions.

The schedule test uses a diagnostic Python mirror; the returned public Racket
censuses separately verify production labels and rotations.
"""
from importlib.util import module_from_spec, spec_from_file_location
import json

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "274345a1792c"


@pytest.fixture(scope="module")
def subject():
    root = find_root(__file__)
    home = root / "generators" / TASK
    spec = spec_from_file_location("teaching_generator_274345a1792c", home / "generator.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    evidence = json.loads((home / "counterexamples/repeated-control.json").read_text())
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    return module, evidence, pairs


def test_declared_canonical_shortcuts_fit_every_canonical_label(subject):
    generator, _, pairs = subject
    assert len(pairs) == 5
    assert len(generator.CANONICAL_SHORTCUTS) == 4
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], name


def test_diagnostic_mirror_matches_canonical_and_retained_racket_labels(subject):
    generator, evidence, pairs = subject
    for pair in [*pairs, *evidence["cases"]]:
        assert generator.self_check(pair["input"]) == []
        assert generator._prediction(pair["input"]) == pair["output"]


def test_fixed_l_is_not_misrepresented_as_a_canonical_fitting_shortcut(subject):
    generator, _, pairs = subject
    assert "fixed_l" not in generator.CANONICAL_SHORTCUTS
    rival = generator.LESSON_COMPETITORS["fixed_l"]
    assert sum(rival(pair["input"]) == pair["output"] for pair in pairs) == 1


def test_repeated_control_counterexamples_refute_declared_rivals(subject):
    generator, evidence, _ = subject
    for pair in evidence["cases"]:
        actual = pair["output"]
        assert generator.CANONICAL_SHORTCUTS["once_per_code"](pair["input"]) != actual
    five = evidence["cases"][1]
    for rival in generator.CANONICAL_SHORTCUTS.values():
        assert rival(five["input"]) != five["output"]


def test_lesson_hook_reports_real_unseen_repeated_code_ambiguity(subject):
    generator, evidence, canonical = subject
    warnings = generator.lesson_identifiable(canonical[:4], evidence["cases"][0])
    assert any("once_per_code" in warning for warning in warnings)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 1, 17, 20261008])
def test_each_cyclic_start_has_redundant_rival_refutations(subject, band, seed):
    generator, _, _ = subject
    assert generator.EXAMPLES_NEEDED == 4
    for start in range(generator.LESSON_SCHEDULE_PERIOD):
        grids = [generator.generate(seed, start + offset, difficulty=band)
                 for offset in range(5)]
        assert len({json.dumps(grid) for grid in grids}) == 5
        pairs = [{"input": grid, "output": generator._prediction(grid)} for grid in grids]
        for name, rival in generator.LESSON_COMPETITORS.items():
            refuting = [i for i, pair in enumerate(pairs)
                        if rival(pair["input"]) != pair["output"]]
            assert len(refuting) >= 2, (band, seed, start, name, refuting)
        for query_index in range(5):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert generator.lesson_identifiable(demos, pairs[query_index]) == []
