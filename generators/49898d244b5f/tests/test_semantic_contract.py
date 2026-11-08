"""Semantic regressions: count occupied cells, erase distractors, fill columns."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import types

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "49898d244b5f"
ROOT = find_root(__file__)
GENERATOR = next(path for path in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators/per_puzzle" / TASK / "generator.py",
) if path.is_file())
SOURCE_BYTES = GENERATOR.read_bytes()
MODULE = types.ModuleType("column_semantics_subject")
MODULE.__file__ = str(GENERATOR)
exec(compile(SOURCE_BYTES, str(GENERATOR), "exec"), MODULE.__dict__)
DATA = json.loads((GENERATOR.parent / "counterexamples/column_semantics.json").read_text())
CASES = {case["name"]: case for case in DATA["cases"]}
MINIMAL_CASES = json.loads((GENERATOR.parent / "counterexamples/lawful_minimal_inputs.json").read_text())["cases"]


def _monochromatic_columns(grid):
    """Independent wrong rule: count distinct colors rather than cells."""
    output = [[0] * len(grid[0]) for _ in grid]
    for column in range(len(grid[0])):
        colors = {row[column] for row in grid if row[column] != 0}
        if len(colors) == 1:
            color = next(iter(colors))
            for row in output:
                row[column] = color
    return output


@pytest.fixture(scope="module")
def racket_label():
    with canonical_path(ROOT).open() as handle:
        source = next(row["program_solution"] for line in handle
                      if (row := json.loads(line)).get("task_id") == TASK)
    assert hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12] == DATA["rule_hash"]
    body = strip_rule_wrapper(strip_line_comments(source))
    bridge = RacketBridge()

    def apply(grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"(let ([g {literal}]) {body})")

    try:
        yield apply
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("name", list(CASES))
def test_hand_inputs_have_independently_verified_racket_labels(name, racket_label):
    pair = CASES[name]
    assert racket_label(pair["input"]) == pair["output"]


@pytest.mark.parametrize("name", list(CASES))
def test_output_mirror_counts_cells_and_rebuilds_blank(name, racket_label):
    # Changing singleton detection to distinct-color detection or preserving
    # original multi-cell columns makes these Racket-labeled cases fail.
    mirror = getattr(MODULE, "expected_output", None)
    assert callable(mirror), "missing task output mirror"
    grid = deepcopy(CASES[name]["input"])
    assert mirror(grid) == racket_label(grid)
    assert grid == CASES[name]["input"]


def test_monochromatic_shortcut_fits_canonical_but_not_same_color_distractor(racket_label):
    for pair in canonical_pairs(TASK, root=ROOT):
        assert _monochromatic_columns(pair["input"]) == racket_label(pair["input"]) == pair["output"]
    query = CASES["same_color_multiple"]
    assert _monochromatic_columns(query["input"]) != racket_label(query["input"])


@pytest.mark.parametrize("name", [name for name, pair in CASES.items() if pair["positive_generator_domain"]])
def test_positive_semantic_inputs_pass_without_canonical_metadata(name):
    assert MODULE.self_check(CASES[name]["input"]) == []
    strict = getattr(MODULE, "strict_canonical_like", None)
    assert callable(strict), "missing strict task-domain hook"
    result = strict(CASES[name]["input"])
    assert result is True or result == []


def test_claimed_canonical_shortcuts_fit_all_authoritative_pairs(racket_label):
    shortcuts = getattr(MODULE, "CANONICAL_SHORTCUTS", None)
    assert isinstance(shortcuts, dict) and shortcuts, "missing claimed canonical shortcuts"
    for name, rival in shortcuts.items():
        for pair in canonical_pairs(TASK, root=ROOT):
            assert rival(pair["input"]) == racket_label(pair["input"]), name


def test_lesson_guard_rejects_unshown_cell_count_and_accepts_demonstrated_distinction(racket_label):
    guard = getattr(MODULE, "lesson_identifiable", None)
    assert callable(guard), "missing lesson guard"
    rivals = getattr(MODULE, "LESSON_COMPETITORS", {})
    assert "monochromatic_columns" in rivals, "missing strongest canonical-fitting rival"
    demos = [{"input": pair["input"], "output": racket_label(pair["input"])}
             for pair in canonical_pairs(TASK, root=ROOT) if pair["split"] == "train"]
    query = {"input": CASES["same_color_multiple"]["input"],
             "output": racket_label(CASES["same_color_multiple"]["input"])}
    before = deepcopy((demos, query))
    reasons = guard(demos, query)
    assert any("monochromatic_columns" in reason for reason in reasons)
    assert (demos, query) == before
    # A rival that disagrees with this query cannot fit it as a demonstration.
    assert guard([demos[0], query], query) == []


@pytest.mark.parametrize("texture, axis, value", [
    (texture, "columns", 1) for texture in MODULE.DEGENERATE_TEXTURES
] + [
    ("no_seeds", "palette_size", 1),
    ("no_seeds", "n_distinct_colors", 1),
    ("no_seeds", "palette_kind", "warm"),
])
def test_unsupported_negative_fixture_controls_report_exact_conflict(texture, axis, value):
    # Rejection fixtures cannot silently ignore otherwise meaningful controls.
    with pytest.raises(ValueError) as caught:
        MODULE.generate(1, 0, texture=texture, **{axis: value})
    assert set(caught.value.incompatible_axes) == {"texture", axis}


@pytest.mark.parametrize("case", MINIMAL_CASES, ids=lambda case: case["name"])
def test_minimal_geometry_is_classified_by_column_cell_count(case, racket_label):
    supplied = deepcopy(case["input"])
    assert racket_label(supplied) == case["output"]
    assert MODULE.expected_output(supplied) == case["output"]
    reasons = MODULE.self_check(supplied)
    strict = MODULE.strict_canonical_like(supplied)
    if case["positive_generator_domain"]:
        assert reasons == []
        assert strict is True or strict == []
    else:
        assert reasons
        assert strict is False or (isinstance(strict, list) and strict)
    assert supplied == case["input"]
