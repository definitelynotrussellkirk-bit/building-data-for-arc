"""Focused tests for the task-local threshold parameter prototype."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
GENERATOR = HOME / "generator.py"
AUTHORITY = ROOT / "shared/data/base/solutions/training/6773b310__a9c4475d7cda.json"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def _load(path: Path, name: str):
    assert path.is_file(), f"required implementation is absent: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE, "threshold_parametric_prototype")


def _generator():
    return _load(GENERATOR, "threshold_parametric_generator")


def _canonical_program():
    data = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    return data["racket_target"]["target_code"]


def _panel_counts(grid):
    height, width = len(grid), len(grid[0])
    separator_rows = [r for r in range(height) if all(value == 8 for value in grid[r])]
    separator_cols = [
        c for c in range(width) if all(grid[r][c] == 8 for r in range(height))
    ]
    row_bands = (
        (0, separator_rows[0]),
        (separator_rows[0] + 1, separator_rows[1]),
        (separator_rows[1] + 1, height),
    )
    col_bands = (
        (0, separator_cols[0]),
        (separator_cols[0] + 1, separator_cols[1]),
        (separator_cols[1] + 1, width),
    )
    return [
        [
            sum(
                grid[r][c] == 6
                for r in range(row_start, row_end)
                for c in range(col_start, col_end)
            )
            for col_start, col_end in col_bands
        ]
        for row_start, row_end in row_bands
    ]


def test_declares_three_typed_thresholds_and_pins_canonical_program_bytes():
    proto = _prototype()
    assert proto.THRESHOLDS == (1, 2, 3)
    assert proto.DEFAULT_THRESHOLD == 2
    assert proto.rule_text(2) == _canonical_program()
    assert (PARAMETRIC / "programs/threshold-2.rkt").read_text(encoding="utf-8") == _canonical_program()
    assert proto.rule_text(1) != proto.rule_text(2) != proto.rule_text(3)


@pytest.mark.parametrize("value", [True, False, 1.0, "2", None, 0, 4])
def test_rule_text_rejects_bool_noninteger_and_undeclared_thresholds(value):
    proto = _prototype()
    with pytest.raises(ValueError):
        proto.rule_text(value)


def test_shared_lawful_grid_exposes_the_threshold_change():
    proto = _prototype()
    gen = _generator()
    grid = gen.generate(
        1701,
        19,
        grid_h=11,
        grid_w=11,
        count_profile="balanced",
    )
    counts = _panel_counts(grid)
    assert Counter(value for row in counts for value in row) == Counter({2: 3, 0: 2, 1: 2, 3: 2})

    outputs = {threshold: proto.apply_python(grid, threshold) for threshold in proto.THRESHOLDS}
    assert len({json.dumps(output) for output in outputs.values()}) == 3
    for threshold, output in outputs.items():
        assert output == [
            [int(count >= threshold) for count in row]
            for row in counts
        ]
    assert any(
        counts[r][c] == 3
        and outputs[1][r][c] == 1
        and outputs[2][r][c] == 1
        and outputs[3][r][c] == 1
        for r in range(3)
        for c in range(3)
    )
    assert any(
        counts[r][c] == 2
        and outputs[1][r][c] == 1
        and outputs[2][r][c] == 1
        and outputs[3][r][c] == 0
        for r in range(3)
        for c in range(3)
    )


def _all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_auto_threshold_is_seed_deterministic_and_independent_of_pair_counts():
    proto = _prototype()
    small = proto.generate_episode(17, threshold="auto", demos=1, queries=1)
    large = proto.generate_episode(17, threshold="auto", demos=3, queries=4)
    repeat = proto.generate_episode(17, threshold="auto", demos=3, queries=4)
    assert small["threshold"] == large["threshold"] == proto.choose_threshold(17)
    assert large == repeat
    assert large["program_solution"] == proto.rule_text(large["threshold"])


@pytest.mark.parametrize("threshold", [1, 2, 3])
def test_one_demo_identifies_threshold_and_four_queries_are_distinct_and_labeled(threshold):
    proto = _prototype()
    episode = proto.generate_episode(20261023, threshold=threshold, demos=1, queries=4)
    assert episode["threshold"] == threshold
    assert len(episode["train"]) == 1
    assert len(episode["test"]) == 4
    assert proto.surviving_thresholds(episode["train"]) == [threshold]
    inputs = _all_inputs(episode)
    assert len({json.dumps(grid) for grid in inputs}) == len(inputs)
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == proto.apply_python(pair["input"], threshold)


def test_same_seed_uses_shared_inputs_across_threshold_settings_but_changes_labels():
    proto = _prototype()
    episodes = {
        threshold: proto.generate_episode(41, threshold=threshold, demos=3, queries=4)
        for threshold in proto.THRESHOLDS
    }
    baseline_inputs = _all_inputs(episodes[1])
    assert all(_all_inputs(episode) == baseline_inputs for episode in episodes.values())
    assert any(
        episodes[1][split][index]["output"] != episodes[3][split][index]["output"]
        for split in ("train", "test")
        for index in range(len(episodes[1][split]))
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": -1},
        {"seed": 2**63},
        {"threshold": False},
        {"threshold": "bad"},
        {"demos": True},
        {"demos": 0},
        {"demos": 17},
        {"queries": 0},
        {"queries": 17},
        {"max_attempts": True},
        {"max_attempts": 0},
        {"max_attempts": 4097},
    ],
)
def test_episode_generation_rejects_invalid_typed_counts_and_settings(kwargs):
    proto = _prototype()
    defaults = {"seed": 0, "threshold": 2, "demos": 3, "queries": 4}
    defaults.update(kwargs)
    with pytest.raises(ValueError):
        proto.generate_episode(**defaults)


def test_declared_count_boundary_returns_exactly_32_distinct_inputs():
    proto = _prototype()
    episode = proto.generate_episode(99, threshold=2, demos=16, queries=16)
    inputs = _all_inputs(episode)
    assert len(episode["train"]) == 16
    assert len(episode["test"]) == 16
    assert len({json.dumps(grid) for grid in inputs}) == 32
    assert proto.surviving_thresholds(episode["train"]) == [2]


def test_sampler_fails_explicitly_instead_of_shortening_requested_episode():
    proto = _prototype()
    with pytest.raises(RuntimeError, match="distinct"):
        proto.generate_episode(0, threshold=2, demos=2, queries=2, max_attempts=3)


def _adapter():
    return _load(PARAMETRIC / "adapter.py", "threshold_parametric_adapter")


def test_promotion_adapter_is_thin_exact_and_count_preserving():
    proto = _prototype()
    adapter = _adapter()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/a9c4475d7cda/workspace/parametric/adapter.py",
        "parameters": {"threshold": [1, 2, 3]},
        "default": {"threshold": 2},
        "limits": {"demos": [1, 16], "queries": [1, 16]},
    }
    assert adapter.program({"threshold": 2}) == _canonical_program()
    generated = adapter.generate(17, {"threshold": 3}, demos=1, queries=4)
    assert generated["program_solution"] == proto.rule_text(3)
    assert len(generated["train"]) == 1
    assert len(generated["test"]) == 4
    assert proto.surviving_thresholds(generated["train"]) == [3]


@pytest.mark.parametrize(
    "settings",
    [{}, {"threshold": True}, {"threshold": 4}, {"threshold": 2, "extra": 1}],
)
def test_adapter_rejects_nonexact_settings(settings):
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.program(settings)


def test_public_projection_omits_private_fields_and_query_answers():
    proto = _prototype()
    episode = proto.generate_episode(17, threshold=2, demos=3, queries=4)
    public = proto.public_payload(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("threshold", "seed", "program_solution", "accepted_inputs"):
        assert forbidden not in serialized


def test_public_identifier_depends_only_on_visible_content():
    import copy

    proto = _prototype()
    episode = proto.generate_episode(17, threshold=2, demos=3, queries=4)
    original = proto.public_id(episode)

    private_change = copy.deepcopy(episode)
    private_change["seed"] = 999
    private_change["threshold"] = 3
    private_change["program_solution"] = "private replacement"
    private_change["test"][0]["output"] = [[9]]
    assert proto.public_id(private_change) == original

    visible_change = copy.deepcopy(episode)
    visible_change["test"][0]["input"][0][0] = (
        visible_change["test"][0]["input"][0][0] + 1
    ) % 10
    assert proto.public_id(visible_change) != original


def test_batch_writer_rejects_duplicate_visible_payload_before_creating_output(tmp_path):
    import copy

    proto = _prototype()
    episode = proto.generate_episode(17, threshold=2, demos=3, queries=4)
    duplicate = copy.deepcopy(episode)
    duplicate["seed"] = 18
    destination = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate visible"):
        proto.write_episodes(destination, [episode, duplicate])
    assert not destination.exists()


def test_batch_writer_uses_opaque_visible_hash_names_and_separate_private_records(tmp_path):
    proto = _prototype()
    episodes = [
        proto.generate_episode(41, threshold=threshold, demos=3, queries=4)
        for threshold in reversed(proto.THRESHOLDS)
    ]
    destination = tmp_path / "export"
    written = proto.write_episodes(destination, episodes)
    ids = [item["public_id"] for item in written]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids)) == 3
    for item in written:
        public_path = Path(item["public_path"])
        private_path = Path(item["private_path"])
        program_path = Path(item["program_path"])
        assert public_path.name == f"challenge-{item['public_id']}.json"
        assert private_path.name == f"episode-{item['public_id']}.json"
        assert program_path.name == f"program-{item['public_id']}.rkt"
        public = json.loads(public_path.read_text(encoding="utf-8"))
        private = json.loads(private_path.read_text(encoding="utf-8"))
        assert all("output" not in pair for pair in public["test"])
        assert private["threshold"] in proto.THRESHOLDS
        assert private["test"][0]["output"]
        assert program_path.read_text(encoding="utf-8") == proto.rule_text(private["threshold"])


def test_writer_rejects_a_tampered_private_label(tmp_path):
    import copy

    proto = _prototype()
    episode = proto.generate_episode(17, threshold=2, demos=3, queries=4)
    tampered = copy.deepcopy(episode)
    tampered["test"][0]["output"][0][0] ^= 1
    with pytest.raises(ValueError, match="label"):
        proto.write_episodes(tmp_path / "tampered", [tampered])
