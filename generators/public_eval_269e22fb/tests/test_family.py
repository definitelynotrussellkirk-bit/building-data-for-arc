from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return load(HOME / "generator.py", "crop_completion_base")


@pytest.fixture(scope="module")
def adapter():
    return load(HOME / "workspace/parametric/adapter.py", "crop_completion_adapter")


def official_pairs():
    raw = REPO / "shared/data/raw"
    challenges = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["269e22fb"]
    solutions = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["269e22fb"]
    return challenges["train"] + [
        {"input": pair["input"], "output": output}
        for pair, output in zip(challenges["test"], solutions, strict=True)
    ]


@pytest.mark.parametrize("index", range(7))
def test_all_official_labels(base, index):
    pair = official_pairs()[index]
    assert base.solve(pair["input"], "preserve") == pair["output"]


def test_reference_and_canonical_are_byte_identical(adapter):
    reference = (HOME / "reference.rkt").read_text()
    canonical = (HOME / "workspace/parametric/canonical.rkt").read_text()
    assert reference == canonical == adapter.program({"pocket_policy": "preserve"})
    assert adapter.program({"pocket_policy": "mark_enclosed"}) != reference


def test_stage_a_recovers_unique_pose_and_crop(base):
    for pair in official_pairs():
        analysis = base.analyze(pair["input"], "preserve")
        assert len(analysis["matches"]) == 1
        pose, row, col = analysis["matches"][0]
        assert 0 <= pose < 8 and row >= 0 and col >= 0
        h, w = len(pair["input"]), len(pair["input"][0])
        binary = [[int(v == analysis["foreground"]) for v in line] for line in pair["input"]]
        assert [line[col : col + w] for line in analysis["binary_completion"][row : row + h]] == binary


def test_mark_enclosed_depends_on_completed_canvas(base):
    pair = official_pairs()[0]
    marked = base.solve(pair["input"], "mark_enclosed")
    preserved = base.solve(pair["input"], "preserve")
    assert len(marked) == len(preserved) == 20
    assert sum(v == 2 for row in marked for v in row) == 51
    assert all(m == 2 or m == p for mr, pr in zip(marked, preserved) for m, p in zip(mr, pr))


@pytest.mark.parametrize("policy", ["preserve", "mark_enclosed"])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_adapter_counts_labels_and_distinct_inputs(adapter, policy, demos, queries):
    episode = adapter.generate(31, {"pocket_policy": policy}, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    inputs = [p["input"] for split in ("train", "test") for p in episode[split]]
    assert len({json.dumps(g, separators=(",", ":")) for g in inputs}) == len(inputs)
    for pair in episode["train"] + episode["test"]:
        assert adapter.mirror(pair["input"], {"pocket_policy": policy}) == pair["output"]


def test_settings_preserve_matched_input_stream(adapter):
    a = adapter.generate(43, {"pocket_policy": "preserve"}, 2, 4)
    b = adapter.generate(43, {"pocket_policy": "mark_enclosed"}, 2, 4)
    for split in ("train", "test"):
        assert [p["input"] for p in a[split]] == [p["input"] for p in b[split]]
        assert all(x["output"] != y["output"] for x, y in zip(a[split], b[split], strict=True))


def test_query_prefix_is_stable_and_order_is_not_source_ordinal(adapter):
    one = adapter.generate(17, {"pocket_policy": "preserve"}, 2, 1)
    four = adapter.generate(17, {"pocket_policy": "preserve"}, 2, 4)
    assert one["test"] == four["test"][:1]
    assert four["private"]["query_permutation"] != [0, 1, 2, 3]


def test_public_turn_reveals_exactly_one_input(adapter):
    episode = adapter.generate(17, {"pocket_policy": "mark_enclosed"}, 2, 4)
    visible = adapter.public_turn(episode, 2)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    assert visible["test"][0]["input"] == episode["test"][2]["input"]
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    raw = json.dumps(visible)
    assert "pocket_policy" not in raw and "program_solution" not in raw and "query_permutation" not in raw


def test_base_worker_generation_accepts_preflight_seeds(base):
    for seed, index in ((17, 0), (43, 1)):
        grid = base.generate(seed=seed, sample_index=index, difficulty="medium")
        assert base.self_check(grid) == []


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [[1]],
        [[1, 1], [1]],
        [[True, False], [False, True]],
        [[1.0, 0.0], [0.0, 1.0]],
        [[10, 0], [0, 10]],
        [[0, 1], [1, 0]],  # tied colors cannot identify background
        [[0, 0], [0, 0]],
    ],
)
def test_strict_input_contract(base, bad):
    with pytest.raises((TypeError, ValueError)):
        base.solve(copy.deepcopy(bad))


@pytest.mark.parametrize(
    "settings",
    [{}, {"pocket_policy": "other"}, {"pocket_policy": "preserve", "extra": 1}],
)
def test_strict_settings(adapter, settings):
    with pytest.raises(ValueError):
        adapter.generate(0, settings, 2, 4)
