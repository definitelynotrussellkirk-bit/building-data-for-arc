"""Change 1: dead/unparsable AXES domains are caught BEFORE any matrix.

The defect these tests pin: a declared axis whose ``valid`` string the
override checker's parser cannot decode is dropped from the Cartesian
matrix without a word, so the axis is never exercised while the report
still reads PASS (``density`` / ``position_bias`` in the reviewer census).
"""

from __future__ import annotations

import types
from pathlib import Path

from scripts.check_generator_override_contract import (
    _axis_values,
    axis_domain_report,
    classify_axis_domain,
)
from scripts.lint_generator import (
    _check_axis_domains,
    _check_realized_axis_honesty,
    _locked_axis_pairs,
    LintReport,
    lint_generator,
)


# --------------------------------------------------------------------------
# domain classification (shared parser, one source of truth)
# --------------------------------------------------------------------------

def test_probeable_singleton_never_probed_and_unparsable_are_distinguished():
    axes = {
        "grid_h": {"type": "int", "valid": "5..14"},
        "pinned": {"type": "int", "valid": "3..3"},
        "density": {"type": "str", "valid": "sparse"},
        "typo": {"type": "int", "valid": "12-22"},
        "expr": {"type": "int", "valid": "1..h*w/2"},
    }
    statuses = {d.name: d.status for d in axis_domain_report(axes)}
    assert statuses == {
        "grid_h": "probeable",
        "pinned": "singleton",
        "density": "never_probed",
        "typo": "unparsable",
        "expr": "unparsable",
    }


def test_diagnostic_marker_exempts_an_unexpressible_domain():
    for marker in ({"probe": "diagnostic"}, {"exact": False}, {"diagnostic": True}):
        spec = {"type": "int", "valid": "1..h*w/2", **marker}
        domain = classify_axis_domain("n_dots", spec, {"n_dots": spec})
        assert domain.status == "diagnostic", marker
        assert domain.probed is False


def test_malformed_axis_spec_is_reported_not_skipped():
    axes = {"broken": ["not", "a", "spec"]}
    assert axis_domain_report(axes)[0].status == "malformed"


def test_huge_integer_domain_collapses_to_endpoints_without_materializing():
    axes = {
        "scene_code": {
            "type": "int",
            "valid": "0..7233945599",
        }
    }

    assert _axis_values(axes["scene_code"], axes) == [0, 7233945599]
    domain = axis_domain_report(axes)[0]
    assert domain.status == "probeable"
    assert domain.values == [0, 7233945599]


def test_huge_integer_domain_honors_excluded_endpoints():
    axes = {
        "scene_code": {
            "type": "int",
            "valid": "0..7233945599 (≠0, ≠7233945599)",
        }
    }

    assert _axis_values(axes["scene_code"], axes) == [1, 7233945598]


# --------------------------------------------------------------------------
# lint severities (blast radius drove these: 5.9% ERROR / 67.2% WARNING)
# --------------------------------------------------------------------------

def test_unparsable_axis_is_an_error_and_singleton_classes_are_warnings():
    report = LintReport()
    _check_axis_domains(
        {
            "typo": {"type": "int", "valid": "12-22"},
            "density": {"type": "str", "valid": "sparse"},
            "pinned": {"type": "int", "valid": "3..3"},
            "grid_h": {"type": "int", "valid": "5..14"},
            "n_dots": {"type": "int", "valid": "1..h*w/2", "probe": "diagnostic"},
        },
        report,
    )

    assert [m for m in report.errors if "'typo'" in m], report.errors
    assert len(report.errors) == 1, report.errors
    assert any("'density'" in m and "never probed" in m for m in report.warnings)
    assert any("'pinned'" in m and "singleton" in m for m in report.warnings)
    assert not any("'grid_h'" in m for m in report.warnings + report.errors)
    assert any("n_dots" in n for n in report.notes)


def _fixture(axes_literal: str) -> str:
    return (
        'GENERATOR_ID = "fixture"\n'
        'VERSION = "1.0.0"\n'
        'TASK_ID = "fixture"\n'
        'SUMMARY = "fixture"\n'
        'RULE_HASH = "123456789abc"\n'
        'INVARIANTS = ["fixture"]\n'
        f"AXES = {axes_literal}\n"
        "def generate(seed, sample_index, *, difficulty=None, **overrides):\n"
        "    return [[0]]\n"
        "def self_check(grid):\n"
        "    return []\n"
    )


def test_lint_end_to_end_errors_on_a_dead_axis(tmp_path: Path) -> None:
    path = tmp_path / "generator.py"
    path.write_text(_fixture('{"grid_w": {"type": "int", "valid": "12-22"}}'))

    report = lint_generator(path)

    assert any("AXES['grid_w'] is never probed" in e for e in report.errors)
    assert report.exit_code == 2


def test_lint_end_to_end_stays_clean_for_a_probeable_axis(tmp_path: Path) -> None:
    path = tmp_path / "generator.py"
    path.write_text(_fixture('{"grid_w": {"type": "int", "valid": "12..22"}}'))

    report = lint_generator(path)

    assert report.errors == []
    assert not any("never probed" in w for w in report.warnings)


def test_lint_end_to_end_handles_a_huge_probeable_axis(tmp_path: Path) -> None:
    path = tmp_path / "generator.py"
    path.write_text(
        _fixture('{"scene_code": {"type": "int", "valid": "0..7233945599"}}')
    )

    report = lint_generator(path)

    assert report.errors == []


# --------------------------------------------------------------------------
# --validate cohort: alias axes and unrecoverable axes
# --------------------------------------------------------------------------

def test_locked_axis_pairs_needs_a_bijection_and_enough_distinct_values():
    aliased = [{"a": n, "b": n} for n in (1, 2, 3, 4)]
    assert _locked_axis_pairs(aliased, ["a", "b"]) == [("a", "b", 4)]

    offset = [{"a": n, "b": n + 1} for n in (1, 2, 3)]
    assert _locked_axis_pairs(offset, ["a", "b"]) == [("a", "b", 3)]

    # too few distinct pairs to distinguish aliasing from coincidence
    assert _locked_axis_pairs([{"a": 1, "b": 1}, {"a": 2, "b": 2}], ["a", "b"]) == []

    independent = [
        {"a": 1, "b": 1}, {"a": 1, "b": 2}, {"a": 2, "b": 1}, {"a": 2, "b": 2}
    ]
    assert _locked_axis_pairs(independent, ["a", "b"]) == []


def _stub_module(observer):
    return types.SimpleNamespace(
        AXES={
            "palette_size": {"type": "int", "valid": "1..9"},
            "n_distinct_colors": {"type": "int", "valid": "1..9"},
            "hidden": {"type": "int", "valid": "1..9"},
        },
        generate=lambda seed, sample_index, *, difficulty=None, **overrides: [
            [(seed % 9) + 1]
        ],
        observe_overrides=observer,
    )


def test_alias_axes_are_warned_over_a_cohort():
    module = _stub_module(
        lambda grid: {
            "palette_size": grid[0][0],
            "n_distinct_colors": grid[0][0],
            "hidden": grid[0][0],
        }
    )
    report = LintReport()

    _check_realized_axis_honesty(module, module.AXES, report)

    aliases = [w for w in report.warnings if "look like aliases" in w]
    assert len(aliases) == 3, report.warnings
    assert any("'palette_size'" in w and "'n_distinct_colors'" in w for w in aliases)


def test_cohort_lock_does_not_warn_when_axis_interventions_are_independent():
    def generate(seed, sample_index, *, difficulty=None, **overrides):
        value = seed + 1
        return [[overrides.get("left", value), overrides.get("right", value)]]

    module = types.SimpleNamespace(
        AXES={
            "left": {"type": "int", "valid": "1..4"},
            "right": {"type": "int", "valid": "1..4"},
        },
        generate=generate,
        observe_overrides=lambda grid: {"left": grid[0][0], "right": grid[0][1]},
    )
    report = LintReport()

    _check_realized_axis_honesty(module, module.AXES, report)

    assert not any("look like aliases" in warning for warning in report.warnings)


def test_cohort_lock_is_rechecked_across_independent_seed_and_index_values():
    def generate(seed, sample_index, *, difficulty=None, **overrides):
        left = (seed % 4) + 1
        right = left if sample_index == seed * 17 + 3 else (sample_index % 4) + 1
        return [[left, right]]

    module = types.SimpleNamespace(
        AXES={
            "left": {"type": "int", "valid": "1..4"},
            "right": {"type": "int", "valid": "1..4"},
        },
        generate=generate,
        observe_overrides=lambda grid: {"left": grid[0][0], "right": grid[0][1]},
    )
    report = LintReport()

    _check_realized_axis_honesty(module, module.AXES, report)

    assert not any("look like aliases" in warning for warning in report.warnings)


def test_axes_the_observer_cannot_recover_are_warned():
    module = _stub_module(lambda grid: {"palette_size": grid[0][0]})
    report = LintReport()

    _check_realized_axis_honesty(module, module.AXES, report)

    assert any(
        "never reports exact axis/axes" in w
        and "n_distinct_colors" in w
        and "hidden" in w
        for w in report.warnings
    ), report.warnings


def test_missing_observer_is_warned_once_with_the_axis_names():
    module = _stub_module(None)
    del module.observe_overrides
    report = LintReport()

    _check_realized_axis_honesty(module, module.AXES, report)

    assert len(report.warnings) == 1
    assert "no observe_overrides(grid)" in report.warnings[0]
    assert "palette_size" in report.warnings[0]
