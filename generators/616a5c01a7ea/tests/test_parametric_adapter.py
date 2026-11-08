"""Behavioral tests for the native parametric family of 616a5c01a7ea."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

try:
    from reviewer_support import canonical_path, find_root
except ModuleNotFoundError as error:
    if error.name != "reviewer_support":
        raise
    for ancestor in Path(__file__).resolve().parents:
        helper = ancestor / "shared" / "runtime" / "reviewer_support.py"
        if helper.is_file():
            sys.path.insert(0, str(helper.parent))
            break
    else:
        raise
    from reviewer_support import canonical_path, find_root

TASK_ID = "616a5c01a7ea"
ROOT = find_root(__file__)
ADAPTER_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "adapter.py"
SPEC = importlib.util.spec_from_file_location("_parametric_616a5c01a7ea", ADAPTER_PATH)
assert SPEC is not None and SPEC.loader is not None
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ADAPTER
SPEC.loader.exec_module(ADAPTER)

CANONICAL = {"right_policy": "fixed_half_turn"}
MARKER = {"right_policy": "marker_row_control"}


def _authority_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    matches = [row["program_solution"] for row in rows if row.get("task_id") == TASK_ID]
    assert len(set(matches)) == 1
    return matches[0]


def _rotate90(panel):
    return [list(row) for row in zip(*panel[::-1])]


def _rotations(panel):
    values = [deepcopy(panel)]
    for _ in range(3):
        values.append(_rotate90(values[-1]))
    return values


def _manual_output(grid, marker_control):
    n = len(grid)
    source = [row[:n] for row in grid]
    turns = _rotations(source)
    middle = turns[1]
    marker_row = next(r for r, row in enumerate(middle) if 8 in row)
    right = turns[3] if marker_control and 2 * marker_row >= n else turns[2]
    out = [[0 for _ in range(3 * n + 2)] for _ in range(n)]
    for r in range(n):
        out[r][:n] = source[r]
        out[r][n] = 5
        out[r][n + 1 : 2 * n + 1] = middle[r]
        out[r][2 * n + 1] = 5
        out[r][2 * n + 2 :] = right[r]
    return out, marker_row


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_selected_canonical():
    assert ADAPTER.program(CANONICAL) == _authority_program()


def test_determinism_settings_neutrality_and_count_prefixes():
    canonical = ADAPTER.generate(17, CANONICAL, 6, 4)
    marker = ADAPTER.generate(17, MARKER, 6, 4)
    assert _inputs(canonical) == _inputs(marker)
    assert canonical == ADAPTER.generate(17, CANONICAL, 6, 4)

    shorter = ADAPTER.generate(17, CANONICAL, 2, 1)
    assert shorter["train"] == canonical["train"][:2]
    assert shorter["test"] == canonical["test"][:1]
    assert len({json.dumps(grid) for grid in _inputs(canonical)}) == 10


def test_labels_match_independent_rotations_and_first_two_demos_teach_branch():
    canonical = ADAPTER.generate(0, CANONICAL, 3, 4)
    marker = ADAPTER.generate(0, MARKER, 3, 4)
    marker_rows = []
    equality = []
    for left, right in zip(canonical["train"] + canonical["test"], marker["train"] + marker["test"]):
        assert left["input"] == right["input"]
        expected_canonical, row = _manual_output(left["input"], False)
        expected_marker, _ = _manual_output(right["input"], True)
        assert left["output"] == expected_canonical
        assert right["output"] == expected_marker
        marker_rows.append((row, len(left["input"])))
        equality.append(left["output"] == right["output"])

    # First demo takes the lower branch and distinguishes the programs; second
    # takes the upper branch and proves the alternate is conditional, not CCW-only.
    assert 2 * marker_rows[0][0] >= marker_rows[0][1]
    assert 2 * marker_rows[1][0] < marker_rows[1][1]
    assert equality[0] is False
    assert equality[1] is True


def test_every_source_is_d4_discriminative_with_one_marker():
    episode = ADAPTER.generate(9, MARKER, 6, 4)
    branches = set()
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        n = len(grid)
        source = [row[:n] for row in grid]
        signatures = set()
        current = source
        for _ in range(4):
            signatures.add(tuple(tuple(row) for row in current))
            signatures.add(tuple(tuple(reversed(row)) for row in current))
            current = _rotate90(current)
        assert len(signatures) == 8
        assert sum(value == 8 for row in source for value in row) == 1
        _, marker_row = _manual_output(grid, True)
        branches.add(2 * marker_row >= n)
    assert branches == {False, True}


def test_query_bank_reaches_maximum_lawful_strip_size():
    episode = ADAPTER.generate(5, MARKER, 2, 4)
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (9, 29)
    assert sum(value != 0 for row in stress for value in row[:9]) >= 50


def _mirror_lr(panel):
    return [list(reversed(row)) for row in panel]


def _wrong_outputs(grid):
    n = len(grid)
    source = [row[:n] for row in grid]
    turns = _rotations(source)
    marker_row = next(r for r, row in enumerate(turns[1]) if 8 in row)

    def assemble(middle, right):
        out = [[0 for _ in range(3 * n + 2)] for _ in range(n)]
        for r in range(n):
            out[r][:n] = source[r]
            out[r][n] = 5
            out[r][n + 1 : 2 * n + 1] = middle[r]
            out[r][2 * n + 1] = 5
            out[r][2 * n + 2 :] = right[r]
        return out

    return {
        "copy-all-panels": assemble(source, source),
        "counterclockwise-middle": assemble(turns[3], turns[2]),
        "swapped-right-middle": assemble(turns[2], turns[1]),
        "mirror-middle": assemble(_mirror_lr(source), turns[2]),
        "always-counterclockwise-right": assemble(turns[1], turns[3]),
        "inverted-marker-branch": assemble(
            turns[1], turns[2] if 2 * marker_row >= n else turns[3]
        ),
    }


def test_visible_demos_reject_named_rotation_shortcuts():
    for seed in (0, 17):
        for settings in (CANONICAL, MARKER):
            episode = ADAPTER.generate(seed, settings, 2, 4)
            intended = [pair["output"] for pair in episode["train"]]
            survivors = []
            for name in _wrong_outputs(episode["train"][0]["input"]):
                claims = [_wrong_outputs(pair["input"])[name] for pair in episode["train"]]
                if claims == intended:
                    survivors.append(name)
            assert survivors == []


def test_structured_self_audit_tool_passes():
    audit_path = ADAPTER_PATH.with_name("audit.py")
    spec = importlib.util.spec_from_file_location("_audit_tool_616a5c01a7ea", audit_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    report = module.run()
    assert report["status"] == "passed"
    assert report["task_id"] == TASK_ID
    assert report["racket_executed"] is False


@pytest.mark.parametrize(
    "args, message",
    [
        ((True, CANONICAL, 2, 1), "seed"),
        ((0, CANONICAL, 1, 1), "demos"),
        ((0, CANONICAL, 2, 5), "queries"),
        ((0, {"right_policy": "unknown"}, 2, 1), "right_policy"),
        ((0, {"right_policy": True}, 2, 1), "right_policy"),
    ],
)
def test_invalid_requests_fail_closed(args, message):
    with pytest.raises(ValueError, match=message):
        ADAPTER.generate(*args)
