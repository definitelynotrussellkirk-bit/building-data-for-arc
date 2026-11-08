"""Focused contract tests for the L-ray crossing parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric crossing prototype is missing"
    name = "_test_parametric_8a802749348c"
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


@pytest.fixture(scope="module")
def engine(prototype):
    with prototype.RacketEngine() as value:
        yield value


def canonical_program() -> str:
    root = find_root(__file__)
    rows = [json.loads(line) for line in canonical_path(root).read_text(encoding="utf-8").splitlines() if line]
    sources = {row["program_solution"] for row in rows if row.get("task_id") == "8a802749348c"}
    assert len(sources) == 1
    return next(iter(sources))


def test_default_program_is_byte_exact_canonical(prototype):
    assert prototype.program({"postprocess": "none"}) == canonical_program()


def test_crossing_marker_is_a_real_second_stage(prototype, engine):
    grid = prototype.sample_input(0, "demo", 0, 13, 15)
    stage = prototype.canonical_transform(grid)
    centers = prototype.crossing_centers(grid, stage)
    assert centers
    marked = prototype.transform(grid, {"postprocess": "mark_crossings"})
    plain = prototype.transform(grid, {"postprocess": "none"})
    assert plain == stage
    assert marked != plain
    for r, c in centers:
        assert marked[r][c] == 9
        assert any(marked[r + dr][c + dc] == 9 for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    assert engine.apply(prototype.program({"postprocess": "none"}), grid) == plain
    assert engine.apply(prototype.program({"postprocess": "mark_crossings"}), grid) == marked


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_counts_distinctness_and_all_racket_labels(prototype, engine, demos):
    settings = ({"postprocess": "none"}, {"postprocess": "mark_crossings"})
    episodes = [prototype.generate(17, value, demos, 4) for value in settings]
    for episode, value in zip(episodes, settings):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == prototype.program(value)
        pairs = episode["train"] + episode["test"]
        keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
        assert len(set(keys)) == len(keys)
        assert [len(episode["test"][-1]["input"]), len(episode["test"][-1]["input"][0])] == [30, 30]
        for pair in pairs:
            assert prototype.crossing_centers(pair["input"], prototype.canonical_transform(pair["input"]))
            assert engine.apply(episode["program_solution"], pair["input"]) == pair["output"]
    for split in ("train", "test"):
        assert [pair["input"] for pair in episodes[0][split]] == [pair["input"] for pair in episodes[1][split]]
    assert all(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


def _fixed_center_offset_output(prototype, grid, dr, dc):
    out = prototype.canonical_transform(grid)
    center_r = len(grid) // 2 + dr
    center_c = len(grid[0]) // 2 + dc
    for rr, cc in ((center_r, center_c), (center_r - 1, center_c),
                   (center_r + 1, center_c), (center_r, center_c - 1),
                   (center_r, center_c + 1)):
        out[rr][cc] = 9
    return out


def test_two_demo_lessons_reject_every_fixed_near_center_marker(prototype):
    offsets = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
    for seed in range(128):
        episode = prototype.generate(seed, {"postprocess": "mark_crossings"}, 2, 1)
        assert not any(
            all(_fixed_center_offset_output(prototype, pair["input"], dr, dc) == pair["output"]
                for pair in episode["train"])
            for dr, dc in offsets
        ), seed


def test_generate_emits_claim_labels_without_starting_nested_racket(prototype, monkeypatch):
    class ForbiddenEngine:
        def __init__(self, *args, **kwargs):
            raise AssertionError("adapter generation must not start a nested Racket audit")

    monkeypatch.setattr(prototype, "RacketEngine", ForbiddenEngine)
    episode = prototype.generate(0, {"postprocess": "none"}, 2, 1)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 1
    assert all(pair["output"] == prototype.transform(pair["input"], {"postprocess": "none"})
               for pair in episode["train"] + episode["test"])


@pytest.mark.parametrize(
    "case",
    [
        {"seed": True, "settings": {"postprocess": "none"}, "demos": 2, "queries": 4},
        {"seed": -1, "settings": {"postprocess": "none"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"postprocess": "other"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"postprocess": "none"}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"postprocess": "none"}, "demos": 2, "queries": 5},
    ],
)
def test_invalid_requests_fail_before_generation(prototype, case):
    with pytest.raises(ValueError):
        prototype.generate(**case)
