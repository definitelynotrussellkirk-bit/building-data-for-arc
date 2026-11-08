"""Proposed strip-stack order parameter; default is the exact canonical program.

Source family: training:aab50785, generator 6b88648ff0e0.
Only the ordering of whole two-row strips changes. Marker detection, cropping,
intra-strip row order, output palette and input grammar remain canonical.
"""
from functools import lru_cache
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "6b88648ff0e0"
SETTINGS = ("top_to_bottom", "bottom_to_top")
DEFAULT = "top_to_bottom"
PARAMETER = "stack_order"
REPO = Path(__file__).resolve().parents[4]


def _setting(value):
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("stack_order must be top_to_bottom or bottom_to_top")
    return value


@lru_cache(maxsize=1)
def _generator():
    return load_selected_generator(TASK_ID, root=REPO)[0]


@lru_cache(maxsize=1)
def _canonical():
    programs = {row["program_solution"]
                for row in map(json.loads, (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
                if row.get("task_id") == TASK_ID}
    if len(programs) != 1:
        raise ValueError("expected one exact canonical strip-extraction program")
    return programs.pop()


def render_program(setting=DEFAULT):
    _setting(setting)
    source = _canonical()
    if setting == DEFAULT:
        return source
    anchor = "(sorted-rows (sort (hash-keys row-groups) <))"
    if source.count(anchor) != 1:
        raise ValueError("canonical program no longer has the expected row-order expression")
    return source.replace(anchor, "(sorted-rows (sort (hash-keys row-groups) >))")


def sample_input(seed, index):
    if type(seed) is not int or type(index) is not int or index < 0:
        raise ValueError("seed/index must be exact integers and index nonnegative")
    profile = ("groups2_narrow", "groups3_wide", "groups4_narrow", "groups1_wide")[index % 4]
    return _generator().generate(seed, index, scene_profile=profile)


def python_expected(grid, setting=DEFAULT):
    _setting(setting)
    generator = _generator()
    errors = generator.self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = generator.rule_mirror(grid)
    if setting == DEFAULT:
        return output
    blocks = [output[i:i + 2] for i in range(0, len(output), 2)]
    return [row[:] for block in reversed(blocks) for row in block]
