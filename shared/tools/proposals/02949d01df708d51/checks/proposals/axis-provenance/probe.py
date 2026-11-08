#!/usr/bin/env python3
"""Reproduce F1 on the actual function; evaluate an unapplied optional patch.

Run from any directory with Python 3. No project imports, labels, or mutations
to production files are needed. The source hash pins the reviewed revision.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
SOURCE_REL = "repo/shared/tools/generator_defect_lint.py"
SOURCE = HERE.parents[2] / SOURCE_REL
SOURCE_SHA256 = "cad291fddbdfa8a48557733a565ff2d0616cf4a5b336dd58988a26e65c9f21fa"


def optional_patch(source):
    old = "    bounds, drawn, options = {}, {}, {}\n"
    new = "    bounds, drawn, options, int_options = {}, {}, {}, {}\n"
    assert source.count(old) == 1
    patched = source.replace(old, new, 1)
    old = "            options.setdefault(label, set()).update(str(o) for o in opts)\n"
    new = old + (
        "            int_options.setdefault(label, set()).update(\n"
        "                o for o in opts if isinstance(o, int) and not isinstance(o, bool))\n"
    )
    assert patched.count(old) == 1
    patched = patched.replace(old, new, 1)
    old = "            if key in bounds:\n                lo, hi = bounds[key]\n"
    new = (
        "            envelope = bounds.get(key)\n"
        "            choice_ints = int_options.get(key, set())\n"
        "            if choice_ints:\n"
        "                choice_bounds = (min(choice_ints), max(choice_ints))\n"
        "                envelope = ((min(envelope[0], choice_bounds[0]),\n"
        "                             max(envelope[1], choice_bounds[1]))\n"
        "                            if envelope is not None else choice_bounds)\n"
        "            if envelope is not None:\n"
        "                lo, hi = envelope\n"
    )
    assert patched.count(old) == 1
    return patched.replace(old, new, 1)


def extract_actual_function(source, filename):
    """Compile the actual function and its parser/regex dependencies only."""
    tree = ast.parse(source, filename=filename)
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in (
            "_parse_valid", "probe_axis_honesty"
        ):
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_VALID_RANGE_RE"
            for target in node.targets
        ):
            nodes.append(node)
    assert len(nodes) == 3, "Parser dependency extraction changed"
    namespace = {"re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, "exec"), namespace)
    return namespace["probe_axis_honesty"]


class PublicContext:
    """Only the public provenance surface consumed by the real function."""
    def __init__(self, *, bounds=None, options=(), value=3):
        self.draw_bounds_store = {} if bounds is None else {"grid_w": bounds}
        self.draw_options_store = {"grid_w": tuple(options)}
        self._values = {"grid_w": value}

    def recorded_draws(self):
        return dict(self._values)


def outcome(function, declared, contexts):
    module = SimpleNamespace(AXES={"grid_w": {"type": "int", "valid": declared}})
    errors, warnings = function(module, contexts)
    return {"errors": errors, "warnings": warnings,
            "counts": {"errors": len(errors), "warnings": len(warnings)}}


def main():
    raw = SOURCE.read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest()
    assert actual_hash == SOURCE_SHA256, "Source changed; review and repin before running"
    source = raw.decode("utf-8")
    patched = optional_patch(source)
    patch = "".join(difflib.unified_diff(
        source.splitlines(keepends=True), patched.splitlines(keepends=True),
        fromfile="a/shared/tools/generator_defect_lint.py",
        tofile="b/shared/tools/generator_defect_lint.py",
    ))
    (HERE / "optional.patch").write_text(patch, encoding="utf-8")
    before = extract_actual_function(source, str(SOURCE))
    after = extract_actual_function(patched, str(SOURCE) + " [optional patch, memory only]")
    cases = [
        ("mixed_full_support", "3..12", [PublicContext(bounds=(3, 3)),
            PublicContext(options=range(3, 13))], (0, 1), (0, 0)),
        ("genuine_narrow_support", "3..12", [PublicContext(bounds=(3, 3)),
            PublicContext(options=(3, 4))], (0, 1), (0, 1)),
        ("hidden_invalid_option", "3..12", [PublicContext(bounds=(3, 3)),
            PublicContext(options=(3, 99), value=3)], (0, 1), (1, 0)),
        ("choice_only_invalid_option", "3..12", [PublicContext(options=(3, 99))],
            (0, 0), (1, 0)),
        ("choice_only_narrow_support", "3..12", [PublicContext(options=(3, 4))],
            (0, 0), (0, 1)),
        ("bool_options_not_coerced", "0..6", [PublicContext(bounds=(3, 3),
            options=(False, True))], (0, 1), (0, 1)),
        ("string_options_not_coerced", "0..6", [PublicContext(bounds=(3, 3),
            options=("0", "6"))], (0, 1), (0, 1)),
        ("existing_invalid_bounds", "3..12", [PublicContext(bounds=(2, 12),
            options=range(3, 13))], (1, 0), (1, 0)),
        ("existing_recorded_outlier", "3..12", [PublicContext(bounds=(3, 12),
            options=(3,), value=99)], (1, 0), (1, 0)),
        ("existing_enum_behavior", "red|blue", [PublicContext(options=("red", "green"),
            value="green")], (1, 0), (1, 0)),
    ]
    results = []
    for name, declared, contexts, expected_before, expected_after in cases:
        actual_before = outcome(before, declared, contexts)
        actual_after = outcome(after, declared, contexts)
        expected = {
            "before": {"errors": expected_before[0], "warnings": expected_before[1]},
            "after": {"errors": expected_after[0], "warnings": expected_after[1]},
        }
        assert actual_before["counts"] == expected["before"], (name, actual_before)
        assert actual_after["counts"] == expected["after"], (name, actual_after)
        if name == "genuine_narrow_support":
            assert "[3, 4]" in actual_after["warnings"][0]
        if name in ("bool_options_not_coerced", "string_options_not_coerced"):
            assert "[3, 3]" in actual_after["warnings"][0]
        if name in ("hidden_invalid_option", "choice_only_invalid_option"):
            assert "[3, 99]" in actual_after["errors"][0]
        results.append({"case": name, "declared": declared,
            "contexts": [{"bounds": ctx.draw_bounds_store,
                          "options": ctx.draw_options_store,
                          "recorded": ctx.recorded_draws()} for ctx in contexts],
            "expected": expected, "actual_before": actual_before,
            "actual_after": actual_after, "passed": True})
    assert SOURCE.read_bytes() == raw, "Production source unexpectedly changed"
    report = {"proposal": "F1 optional integer-choice provenance union",
        "status": "all_expected_before_and_after_outcomes_verified",
        "source_path_relative_to_WORK": SOURCE_REL,
        "source_sha256": actual_hash,
        "patched_source_sha256": hashlib.sha256(patched.encode()).hexdigest(),
        "patch_sha256": hashlib.sha256(patch.encode()).hexdigest(),
        "production_source_changed": False,
        "method": "Extract actual parser, regex, and probe function with AST; execute original and in-memory patched source against fake public GenCtx contexts.",
        "limits": "Range-envelope coverage remains an envelope estimate; it does not establish occupancy of interior values or audit non-integer choices as integer options.",
        "cases": results}
    (HERE / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": len(results),
                      "source_sha256": actual_hash, "production_source_changed": False}, indent=2))


if __name__ == "__main__":
    main()
