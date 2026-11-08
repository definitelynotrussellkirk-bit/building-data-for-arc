"""Base and parametric regressions for mirror-guide task 02dc25c0440b."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "02dc25c0440b"
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric visible-size prototype is missing"
    name = "_test_parametric_02dc25c0440b"
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


def selected_source() -> str:
    root = find_root(__file__)
    rows = [json.loads(line) for line in canonical_path(root).read_text(encoding="utf-8").splitlines() if line]
    sources = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(sources) == 1
    return next(iter(sources))


def test_base_generator_is_deterministic_and_self_checked():
    root = find_root(__file__)
    gen, _, _ = load_selected_generator(TASK_ID, root=root)
    random.seed(20261026)
    before = random.getstate()
    first = gen.generate(71, 9, difficulty="medium")
    assert random.getstate() == before
    second = gen.generate(71, 9, difficulty="medium")
    assert first == second and first is not second
    assert gen.self_check(first, difficulty="medium") == []
    assert gen.generate(72, 9, difficulty="medium") != first


def test_selected_canonical_program_labels_all_original_pairs(prototype, engine):
    root = find_root(__file__)
    source = selected_source()
    assert prototype.program({"right_label": "source_color"}) == source
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert engine.apply(source, pair["input"]) == pair["output"]


def test_partial_clip_changes_visible_component_size(prototype, engine):
    grid = prototype.sample_input(0, "demo", 0, 11, 13)
    stage = prototype.mirror_stage(grid)
    components = prototype.right_components(stage)
    assert components
    assert any(row["visible_size"] < row["source_size"] for row in prototype.component_correspondence(grid, stage))
    source = prototype.transform(grid, {"right_label": "source_color"})
    visible = prototype.transform(grid, {"right_label": "visible_size"})
    assert source == stage
    assert visible != source
    assert engine.apply(prototype.program({"right_label": "source_color"}), grid) == source
    assert engine.apply(prototype.program({"right_label": "visible_size"}), grid) == visible


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_counts_distinctness_and_all_racket_labels(prototype, engine, demos):
    settings = ({"right_label": "source_color"}, {"right_label": "visible_size"})
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
            correspondence = prototype.component_correspondence(pair["input"], prototype.mirror_stage(pair["input"]))
            assert correspondence and any(row["visible_size"] < row["source_size"] for row in correspondence)
            assert engine.apply(episode["program_solution"], pair["input"]) == pair["output"]
    for split in ("train", "test"):
        assert [pair["input"] for pair in episodes[0][split]] == [pair["input"] for pair in episodes[1][split]]
    assert all(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


def _source_side_relabel(prototype, grid, labeler):
    stage = prototype.mirror_stage(grid)
    out = [row[:] for row in stage]
    for component in prototype.component_correspondence(grid, stage):
        label = labeler(component)
        for r, c in component["visible_cells"]:
            out[r][c] = label
    return out


def test_two_demo_lessons_reject_fixed_clip_and_minus_one_shortcuts(prototype):
    rivals = (
        lambda row: 4 if row["visible_size"] < row["source_size"] else row["source_size"],
        lambda row: row["source_size"] - 1
        if row["visible_size"] < row["source_size"] else row["source_size"],
    )
    for seed in range(64):
        episode = prototype.generate(seed, {"right_label": "visible_size"}, 2, 1)
        assert not any(
            all(_source_side_relabel(prototype, pair["input"], rival) == pair["output"]
                for pair in episode["train"])
            for rival in rivals
        ), seed


def test_generate_emits_claim_labels_without_starting_nested_racket(prototype, monkeypatch):
    class ForbiddenEngine:
        def __init__(self, *args, **kwargs):
            raise AssertionError("adapter generation must not start a nested Racket audit")

    monkeypatch.setattr(prototype, "RacketEngine", ForbiddenEngine)
    episode = prototype.generate(0, {"right_label": "source_color"}, 2, 1)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 1
    assert all(pair["output"] == prototype.transform(pair["input"], {"right_label": "source_color"})
               for pair in episode["train"] + episode["test"])


@pytest.mark.parametrize(
    "case",
    [
        {"seed": True, "settings": {"right_label": "source_color"}, "demos": 2, "queries": 4},
        {"seed": -1, "settings": {"right_label": "source_color"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"right_label": "other"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"right_label": "source_color"}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"right_label": "source_color"}, "demos": 2, "queries": 5},
    ],
)
def test_invalid_requests_fail_before_generation(prototype, case):
    with pytest.raises(ValueError):
        prototype.generate(**case)
