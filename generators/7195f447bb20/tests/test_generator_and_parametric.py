from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
PARAMETRIC = HOME / "workspace" / "parametric" / "prototype.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _generator():
    return _load("generator_7195", HOME / "generator.py")


def _parametric():
    assert PARAMETRIC.is_file(), "parametric prototype has not been implemented"
    return _load("parametric_7195", PARAMETRIC)


def _canonical_record():
    with (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "7195f447bb20":
                return row
    raise AssertionError("canonical task missing")


def test_canonical_pairs_are_accepted_and_rule_mirror_matches_exactly():
    gen = _generator()
    record = _canonical_record()
    for pair in record["train"] + record["test"]:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_generated_scene_honors_shape_and_gap_overrides_and_contains_guard_witness():
    gen = _generator()
    grid = gen.generate(91, 7, difficulty="medium", grid_h=16, grid_w=17, n_gaps=4)
    assert (len(grid), len(grid[0])) == (16, 17)
    facts = gen.semantic_signature(grid)
    assert facts["eligible_gap_count"] == 4
    assert facts["guarded_gap_count"] >= 1
    assert gen.self_check(grid) == []
    assert gen.no_guard_rival(grid) != gen.rule_mirror(grid)


def test_generation_is_deterministic_and_unknown_overrides_fail_loudly():
    gen = _generator()
    kwargs = dict(difficulty="hard", grid_h=18, grid_w=19, n_gaps=5)
    assert gen.generate(1234, 2, **kwargs) == gen.generate(1234, 2, **kwargs)
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)


def test_three_demo_lesson_refutes_named_competitors():
    gen = _generator()
    pairs = []
    for index in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(881, index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[: gen.EXAMPLES_NEEDED], pairs[-1]) == []
    for name, competitor in gen.LESSON_COMPETITORS.items():
        assert not all(competitor(pair["input"]) == pair["output"]
                       for pair in pairs[: gen.EXAMPLES_NEEDED]), name


def test_parametric_default_program_is_exact_canonical_bytes():
    proto = _parametric()
    assert proto.program({"mode": "canonical"}) == _canonical_record()["program_solution"]


def test_parametric_counts_settings_and_prefix_are_strict_and_stable():
    proto = _parametric()
    one = proto.generate(17, {"mode": "cascade"}, 3, 1)
    four = proto.generate(17, {"mode": "cascade"}, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    visible_inputs = [pair["input"] for pair in four["train"] + four["test"]]
    assert len({repr(grid) for grid in visible_inputs}) == 7
    for bad in (1, 7, True):
        with pytest.raises((TypeError, ValueError)):
            proto.generate(0, {"mode": "canonical"}, bad, 4)
    with pytest.raises(ValueError):
        proto.generate(0, {"mode": "unknown"}, 3, 4)


def test_cascade_step_b_consumes_centers_newly_written_by_step_a():
    proto = _parametric()
    grid = [[0] * 9 for _ in range(8)]
    grid[1][1] = 4
    grid[3][3] = 4
    grid[2][4] = 4
    canonical = proto.python_oracle(grid, {"mode": "canonical"})
    cascade = proto.python_oracle(grid, {"mode": "cascade"})
    assert canonical[2][2] == 4
    assert canonical[2][3] == 0
    assert cascade[2][2] == 4
    assert cascade[2][3] == 4
    assert canonical != cascade


def test_generated_lessons_teach_guard_and_include_substantive_30x30_query():
    proto = _parametric()
    for mode in proto.MODES:
        episode = proto.generate(0, {"mode": mode}, 2, 4)
        other = next(candidate for candidate in proto.MODES if candidate != mode)
        assert all(proto.guard_witness(pair["input"]) for pair in episode["train"])
        assert any(pair["output"] != proto.python_oracle(pair["input"], {"mode": other})
                   for pair in episode["train"])
        last = episode["test"][-1]
        assert (len(last["input"]), len(last["input"][0])) == (30, 30)
        changed = sum(a != b for in_row, out_row in zip(last["input"], last["output"])
                      for a, b in zip(in_row, out_row))
        assert changed >= (8 if mode == "cascade" else 4)
