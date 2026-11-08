from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

TASK_ID = "9ea9f1e62275"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = HOME / "workspace/parametric"
SETTINGS = tuple({"metric": metric} for metric in ("manhattan", "chebyshev", "euclidean_sq"))


def _load(name: str):
    path = PARAMETRIC / name
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{path.stem}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    record = json.loads(
        (ROOT / "shared/data/base/solutions/banks/3c7b85b8eeb1/H42__9ea9f1e62275.json").read_text()
    )
    return record["racket_target"]["target_code"]


def _inputs(episode):
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def test_default_program_is_exact_canonical_bytes_and_alternatives_are_distinct():
    adapter = _load("adapter.py")
    programs = [adapter.program(setting) for setting in SETTINGS]
    assert programs[0] == _canonical_program()
    assert len(set(programs)) == 3
    assert all(program.startswith("(rule!") for program in programs)


def test_settings_and_count_contract_is_strict_and_bool_safe():
    adapter = _load("adapter.py")
    with pytest.raises(ValueError):
        adapter.program({})
    with pytest.raises(ValueError):
        adapter.program({"metric": "manhattan", "extra": 1})
    with pytest.raises(ValueError):
        adapter.program({"metric": "taxicab"})
    with pytest.raises(TypeError):
        adapter.generate(True, {"metric": "manhattan"}, 2, 4)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"metric": "manhattan"}, True, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"metric": "manhattan"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"metric": "manhattan"}, 2, 3)


def test_inputs_are_matched_across_settings_and_selected_labels_are_exact():
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    episodes = [adapter.generate(17, setting, 2, 4) for setting in SETTINGS]
    assert all(_inputs(episode) == _inputs(episodes[0]) for episode in episodes[1:])
    assert len({json.dumps(grid) for grid in _inputs(episodes[0])}) == 6

    for setting, episode in zip(SETTINGS, episodes):
        assert episode["program_solution"] == adapter.program(setting)
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        for pair in [*episode["train"], *episode["test"]]:
            assert pair["output"] == prototype.apply_metric(pair["input"], setting["metric"])


def test_minimum_two_demos_identify_each_metric_and_refute_named_bypasses():
    prototype = _load("prototype.py")
    for seed in (0, 17, 91):
        bank = prototype.build_input_bank(seed, demos=2, queries=4)
        assert prototype.metric_survivors(bank["train"], "manhattan") == ["manhattan"]
        assert prototype.metric_survivors(bank["train"], "chebyshev") == ["chebyshev"]
        assert prototype.metric_survivors(bank["train"], "euclidean_sq") == ["euclidean_sq"]
        for metric in prototype.METRICS:
            assert prototype.rival_survivors(bank["train"], metric) == []


def test_query_bank_is_demo_count_independent_and_contains_real_30x30_stress():
    adapter = _load("adapter.py")
    two = adapter.generate(1234, {"metric": "manhattan"}, 2, 4)
    six = adapter.generate(1234, {"metric": "manhattan"}, 6, 4)
    assert [pair["input"] for pair in two["test"]] == [pair["input"] for pair in six["test"]]
    assert any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30 for pair in two["test"])
    assert any(len(pair["input"]) <= 10 and len(pair["input"][0]) >= 22 for pair in two["test"])
    assert any(len(pair["input"]) >= 22 and len(pair["input"][0]) <= 12 for pair in two["test"])


def test_determinism_and_fresh_return_objects():
    adapter = _load("adapter.py")
    first = adapter.generate(77, {"metric": "chebyshev"}, 3, 4)
    frozen = json.dumps(first, sort_keys=True)
    first["train"][0]["input"][0][0] = 9
    second = adapter.generate(77, {"metric": "chebyshev"}, 3, 4)
    assert json.dumps(second, sort_keys=True) == frozen


def test_fixed_canvas_stress_varies_frame_geometry_and_keeps_boundary_contacts():
    prototype = _load("prototype.py")
    boxes = set()
    for seed in range(12):
        bank = prototype.build_input_bank(seed, demos=2, queries=4)
        stress = next(grid for grid in bank["test"] if len(grid) == 30 and len(grid[0]) == 30)
        facts = prototype._analyze(stress)
        bbox = tuple(facts["frame_bbox"])
        boxes.add(bbox)
        r0, c0, r1, c1 = bbox
        assert (r1 - r0 - 1) * (c1 - c0 - 1) >= 400
        assert any(
            row in {r0 + 1, r1 - 1} or col in {c0 + 1, c1 - 1}
            for row, col, _color in facts["seeds"]
        )
    assert len(boxes) >= 4


def test_every_retained_scene_has_a_nontrivial_metric_disagreement_margin():
    prototype = _load("prototype.py")
    for seed in (0, 17, 91):
        bank = prototype.build_input_bank(seed, demos=6, queries=4)
        for grid in bank["train"] + bank["test"]:
            facts = prototype._analyze(grid)
            r0, c0, r1, c1 = facts["frame_bbox"]
            threshold = max(3, ((r1 - r0 - 1) * (c1 - c0 - 1)) // 50)
            outputs = {metric: prototype.apply_metric(grid, metric) for metric in prototype.METRICS}
            for index, left in enumerate(prototype.METRICS):
                for right in prototype.METRICS[index + 1 :]:
                    disagreement = sum(
                        a != b
                        for row_a, row_b in zip(outputs[left], outputs[right])
                        for a, b in zip(row_a, row_b)
                    )
                    assert disagreement >= threshold


def test_certificate_rejects_bool_cells_even_when_python_equality_matches_color_one():
    import copy

    prototype = _load("prototype.py")
    episode = prototype.generate(5, {"metric": "manhattan"}, 2, 4)
    forged = copy.deepcopy(episode)
    output = forged["train"][0]["output"]
    row, col = next(
        (r, c)
        for r, values in enumerate(output)
        for c, value in enumerate(values)
        if value == 1
    )
    output[row][col] = True
    with pytest.raises(ValueError, match="output|integer|grid"):
        prototype.certify(forged)
