"""Focused tests for generator-lint finite-codomain calibration."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.lint_generator import (
    _covers_declared_output_codomain,
    lint_generator,
)


class FiniteCodomainTests(unittest.TestCase):
    def test_exact_or_overcomplete_sample_covers_declared_space(self):
        self.assertTrue(_covers_declared_output_codomain(13, 13))
        self.assertTrue(_covers_declared_output_codomain(13, 14))

    def test_partial_or_invalid_declaration_does_not_suppress_warning(self):
        self.assertFalse(_covers_declared_output_codomain(13, 12))
        self.assertFalse(_covers_declared_output_codomain(0, 13))
        self.assertFalse(_covers_declared_output_codomain(True, 13))
        self.assertFalse(_covers_declared_output_codomain(None, 13))


def _fixture(
    *,
    rule_hash: bool,
    self_checks: int,
    rule_hash_value: str = "123456789abc",
) -> str:
    hash_line = f"RULE_HASH = {rule_hash_value!r}\n" if rule_hash else ""
    check_defs = "\n".join(
        f"def self_check_{index}(grid):\n    return []\n".replace(
            f"self_check_{index}", "self_check"
        )
        for index in range(self_checks)
    )
    return (
        'GENERATOR_ID = "fixture"\n'
        'VERSION = "1.0.0"\n'
        'TASK_ID = "fixture"\n'
        'SUMMARY = "fixture"\n'
        'INVARIANTS = ["fixture"]\n'
        'AXES = {"size": {"type": "int", "valid": "1..2"}}\n'
        f"{hash_line}"
        "def generate(seed, sample_index, *, difficulty=None, **overrides):\n"
        "    return [[0]]\n"
        f"{check_defs}\n"
    )


def test_lint_rejects_missing_rule_hash_and_shadowed_self_check(
    tmp_path: Path,
) -> None:
    path = tmp_path / "generator.py"
    path.write_text(
        _fixture(rule_hash=False, self_checks=2),
        encoding="utf-8",
    )

    report = lint_generator(path)

    assert "missing required module constant: RULE_HASH" in report.errors
    assert (
        "expected exactly one top-level self_check() definition, found 2"
        in report.errors
    )


def test_lint_accepts_rule_hash_and_single_self_check(tmp_path: Path) -> None:
    path = tmp_path / "generator.py"
    path.write_text(
        _fixture(rule_hash=True, self_checks=1),
        encoding="utf-8",
    )

    report = lint_generator(path)

    assert not report.errors


def test_lint_rejects_malformed_rule_hashes(tmp_path: Path) -> None:
    path = tmp_path / "generator.py"
    malformed = (
        "",
        "   ",
        "xyz",
        "123456789ab",
        "123456789abc0",
        "ABCDEF123456",
    )

    for value in malformed:
        path.write_text(
            _fixture(
                rule_hash=True,
                self_checks=1,
                rule_hash_value=value,
            ),
            encoding="utf-8",
        )
        report = lint_generator(path)
        assert (
            "RULE_HASH must be exactly 12 lowercase hexadecimal characters"
            in report.errors
        ), value


def test_lint_flags_discarded_place_no_overlap_result(tmp_path: Path) -> None:
    path = tmp_path / "generator.py"
    path.write_text(
        _fixture(rule_hash=True, self_checks=1).replace(
            "    return [[0]]\n",
            "    placer.place_no_overlap([[0]], [[1]], object())\n"
            "    return [[0]]\n",
        ),
        encoding="utf-8",
    )

    report = lint_generator(path)

    assert any(
        "discarded Optional result from place_no_overlap" in warning
        for warning in report.warnings
    )


def test_lint_accepts_checked_or_postcondition_suppressed_placement(
    tmp_path: Path,
) -> None:
    path = tmp_path / "generator.py"
    source = _fixture(rule_hash=True, self_checks=1).replace(
        "    return [[0]]\n",
        "    offset = placer.place_no_overlap([[0]], [[1]], object())\n"
        "    if offset is None:\n"
        "        raise ValueError('placement failed')\n"
        "    placer.place_no_overlap([[0]], [[1]], object())"
        "  # lint: place-no-overlap-postcondition\n"
        "    return [[0]]\n",
    )
    path.write_text(source, encoding="utf-8")

    report = lint_generator(path)

    assert not any(
        "discarded Optional result from place_no_overlap" in warning
        for warning in report.warnings
    )


if __name__ == "__main__":
    unittest.main()
