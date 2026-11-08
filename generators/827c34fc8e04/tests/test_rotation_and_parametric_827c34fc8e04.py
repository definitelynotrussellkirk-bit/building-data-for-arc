"""Rotation-policy and parametric regressions for 827c34fc8e04."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "827c34fc8e04"
ROOT = find_root(__file__)
GEN, _SOURCE, _SHA = load_selected_generator(TASK, root=ROOT)


def _load(name: str):
    path = ROOT / f"generators/{TASK}/workspace/parametric/{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK and isinstance(row.get("program_solution"), str):
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def test_every_holdout_from_four_default_draws_remains_identifiable():
    seeds = (2263286116, 17, 991)
    for difficulty in ("easy", "medium", "hard"):
        for seed in seeds:
            for start in range(4):
                pairs = []
                for sample_index in range(start, start + 4):
                    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                    pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
                for held_out in range(4):
                    demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                    assert GEN.lesson_identifiable(demos, pairs[held_out]) == [], (
                        difficulty,
                        seed,
                        start,
                        held_out,
                    )


def test_parametric_default_is_exact_authority_and_inputs_are_matched():
    adapter = _load("adapter")
    prototype = _load("prototype")
    default = {"trail_mode": "all_markers"}
    alternate = {"trail_mode": "max_color_marker"}
    assert adapter.program(default) == _canonical_program()

    left = adapter.generate(31, default, 3, 4)
    right = adapter.generate(31, alternate, 3, 4)
    assert [p["input"] for p in left["train"] + left["test"]] == [
        p["input"] for p in right["train"] + right["test"]
    ]
    assert left["train"][0]["output"] != right["train"][0]["output"]
    for settings, episode in ((default, left), (alternate, right)):
        survivors = [
            candidate
            for candidate in prototype.SETTINGS
            if all(
                prototype.transform(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [settings]


def test_parametric_prefix_independence_and_30x30_output():
    adapter = _load("adapter")
    settings = {"trail_mode": "max_color_marker"}
    short = adapter.generate(72, settings, 2, 1)
    long = adapter.generate(72, settings, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    stress = long["test"][3]
    assert (len(stress["input"]), len(stress["input"][0])) == (15, 15)
    assert (len(stress["output"]), len(stress["output"][0])) == (30, 30)
    inputs = [json.dumps(pair["input"]) for pair in long["train"] + long["test"]]
    assert len(inputs) == len(set(inputs))


def test_max_color_marker_supplies_the_only_trail_anchor():
    prototype = _load("prototype")
    grid = [
        [0, 0, 2, 0],
        [0, 9, 0, 0],
        [0, 0, 0, 0],
        [0, 4, 0, 0],
    ]
    expected = [
        [1, 0, 0, 0, 2, 2, 0, 0],
        [0, 1, 0, 0, 2, 2, 0, 0],
        [0, 0, 9, 9, 0, 0, 0, 0],
        [0, 0, 9, 9, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 4, 4, 0, 0, 1, 0],
        [0, 0, 4, 4, 0, 0, 0, 1],
    ]
    assert prototype.transform(grid, {"trail_mode": "max_color_marker"}) == expected
    assert prototype.transform(grid, {"trail_mode": "all_markers"}) != expected
