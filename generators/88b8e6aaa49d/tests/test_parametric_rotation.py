"""Focused tests for the task-local quarter-turn parameter prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_rule_family_materializes_exact_default_and_three_distinct_turns():
    assert PROTOTYPE.is_file(), "the requested runnable parametric prototype is absent"
    proto = _load_module("rotation_parametric_rule_test", PROTOTYPE)

    assert proto.ALLOWED_QUARTER_TURNS == (1, 2, 3)
    assert proto.DEFAULT_QUARTER_TURNS == 2
    assert proto.rule_source(1) == "(rule! (lambda (g) (rotate-cw g)))"
    assert proto.rule_source(2) == "(rule! (lambda (g) (flip-ud (flip-lr g))))"
    assert proto.rule_source(3) == "(rule! (lambda (g) (rotate-ccw g)))"

    grid = [[1, 2, 3], [4, 5, 6]]
    assert proto.python_mirror(grid, 1) == [[4, 1], [5, 2], [6, 3]]
    assert proto.python_mirror(grid, 2) == [[6, 5, 4], [3, 2, 1]]
    assert proto.python_mirror(grid, 3) == [[3, 6], [2, 5], [1, 4]]

import json
import pytest


class MirrorEngine:
    """Fast real-behavior double: independent literal rotations, no Racket process."""

    def __init__(self):
        self.executions = []

    def apply(self, grid, quarter_turns):
        if quarter_turns == 1:
            output = [list(row) for row in zip(*reversed(grid))]
        elif quarter_turns == 2:
            output = [list(reversed(row)) for row in reversed(grid)]
        elif quarter_turns == 3:
            output = [list(row) for row in reversed(list(zip(*grid)))]
        else:
            raise ValueError("invalid test setting")
        self.executions.append((quarter_turns, json.dumps(grid), json.dumps(output)))
        return output


def _input_key(grid):
    return json.dumps(grid, sort_keys=True, separators=(",", ":"))


def test_episode_generation_uses_one_setting_and_independent_demo_query_counts():
    proto = _load_module("rotation_parametric_episode_test", PROTOTYPE)
    engine = MirrorEngine()
    episode = proto.generate_episode(
        17, quarter_turns=3, demos=2, queries=4, max_attempts=32, engine=engine
    )

    assert episode["quarter_turns"] == 3
    assert episode["demo_count"] == 2
    assert episode["query_count"] == 4
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert len({_input_key(grid) for grid in inputs}) == 6

    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == MirrorEngine().apply(pair["input"], 3)

    assert len(episode["query_identification"]) == 4
    for report, pair in zip(episode["query_identification"], episode["test"], strict=True):
        assert report["status"] == "identified_within_declared_rivals"
        assert report["consistent_settings"] == [3]
        assert report["query_answer_used_for_demo_fit"] is False
        assert report["determined_output_sha256"] == proto.digest(pair["output"])


def test_setting_choice_is_deterministic_count_independent_and_covers_family():
    proto = _load_module("rotation_parametric_setting_test", PROTOTYPE)
    observed = {proto.choose_setting(seed) for seed in range(64)}
    assert observed == {1, 2, 3}
    for seed in (0, 17, 63):
        first = proto.generate_episode(seed, demos=1, queries=1, engine=MirrorEngine())
        second = proto.generate_episode(seed, demos=3, queries=4, engine=MirrorEngine())
        assert first["quarter_turns"] == second["quarter_turns"] == proto.choose_setting(seed)


def test_empty_demonstrations_remain_ambiguous_across_all_declared_settings():
    proto = _load_module("rotation_parametric_ambiguity_test", PROTOTYPE)
    query = proto.generator().generate(5, 0)
    report = proto.identify_query([], query, engine=MirrorEngine())
    assert report["status"] == "ambiguous_within_declared_rivals"
    assert report["consistent_settings"] == [1, 2, 3]
    assert report["query_answer_used_for_demo_fit"] is False
    assert len({row["query_prediction_sha256"] for row in report["rivals"]}) == 3


@pytest.mark.parametrize("value", [True, False, 0, 4, -1, 1.0, "2", None])
def test_invalid_parameter_values_fail_closed(value):
    proto = _load_module(f"rotation_parametric_bad_setting_{value!r}", PROTOTYPE)
    with pytest.raises((TypeError, ValueError)):
        proto.rule_source(value)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": -1},
        {"seed": 2**63},
        {"seed": 1.0},
        {"seed": 0, "demos": 0},
        {"seed": 0, "demos": True},
        {"seed": 0, "queries": 0},
        {"seed": 0, "queries": 17},
        {"seed": 0, "max_attempts": 0},
    ],
)
def test_invalid_episode_controls_fail_before_sampling(kwargs):
    proto = _load_module(f"rotation_parametric_bad_controls_{len(str(kwargs))}", PROTOTYPE)
    with pytest.raises((TypeError, ValueError)):
        proto.generate_episode(engine=MirrorEngine(), **kwargs)

import copy


def test_public_projection_depends_only_on_visible_demonstrations_and_query_inputs():
    proto = _load_module("rotation_parametric_public_projection_test", PROTOTYPE)
    episode = proto.generate_episode(
        17, quarter_turns=2, demos=2, queries=4, engine=MirrorEngine()
    )
    original_bytes = proto.public_bytes(episode)
    original_id = proto.public_id(episode)
    visible = json.loads(original_bytes)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert all(set(pair) == {"input"} for pair in visible["test"])

    private_change = copy.deepcopy(episode)
    private_change["seed"] = 999999
    private_change["quarter_turns"] = 1
    private_change["program_solution"] = "PRIVATE CANARY"
    for pair in private_change["test"]:
        pair["output"] = [[9]]
    assert proto.public_bytes(private_change) == original_bytes
    assert proto.public_id(private_change) == original_id

    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] = 9
    assert proto.public_id(visible_change) != original_id


def test_batch_writer_rejects_duplicate_visible_payloads_before_any_write(tmp_path):
    proto = _load_module("rotation_parametric_duplicate_writer_test", PROTOTYPE)
    episode = proto.generate_episode(
        17, quarter_turns=1, demos=2, queries=4, engine=MirrorEngine()
    )
    duplicate = copy.deepcopy(episode)
    duplicate["seed"] = 12345
    duplicate["private_canary"] = "different private metadata"

    with pytest.raises(ValueError, match="duplicate visible payload"):
        proto.write_episodes(tmp_path, [episode, duplicate], engine=MirrorEngine())
    assert not (tmp_path / "public").exists()
    assert not (tmp_path / "private").exists()


def test_batch_writer_validates_sorts_and_separates_public_private(tmp_path):
    proto = _load_module("rotation_parametric_sorted_writer_test", PROTOTYPE)
    episodes = [
        proto.generate_episode(23, quarter_turns=turns, demos=2, queries=4, engine=MirrorEngine())
        for turns in (3, 1, 2)
    ]
    records = proto.write_episodes(tmp_path, episodes, engine=MirrorEngine())
    expected_ids = sorted(proto.public_id(episode) for episode in episodes)
    assert [record["public_id"] for record in records] == expected_ids

    for record in records:
        public_path = Path(record["public_path"])
        private_path = Path(record["private_path"])
        rule_path = Path(record["rule_path"])
        assert public_path.name == record["public_id"] + ".json"
        assert public_path.read_bytes() == proto.public_bytes(
            next(episode for episode in episodes if proto.public_id(episode) == record["public_id"])
        )
        public = json.loads(public_path.read_bytes())
        assert all("output" not in pair for pair in public["test"])
        private = json.loads(private_path.read_text())
        assert private["quarter_turns"] in (1, 2, 3)
        assert all("output" in pair for pair in private["test"])
        assert rule_path.read_text() == private["program_solution"]


def test_writer_rejects_corrupted_query_label_before_any_write(tmp_path):
    proto = _load_module("rotation_parametric_corrupt_writer_test", PROTOTYPE)
    episode = proto.generate_episode(
        17, quarter_turns=3, demos=2, queries=4, engine=MirrorEngine()
    )
    episode["test"][2]["output"] = [[9]]
    with pytest.raises(ValueError, match="label mismatch"):
        proto.write_episodes(tmp_path, [episode], engine=MirrorEngine())
    assert not (tmp_path / "public").exists()
    assert not (tmp_path / "private").exists()

ADAPTER = HOME / "workspace/parametric/adapter.py"
PROMOTION = HOME / "workspace/parametric/promotion.json"


def test_canonical_default_is_source_bound_and_real_racket_executes_all_settings():
    proto = _load_module("rotation_parametric_racket_test", PROTOTYPE)
    assert proto.canonical_rule_source() == "(rule! (lambda (g) (flip-ud (flip-lr g))))"
    assert proto.rule_source(2) == proto.canonical_rule_source()

    grid = [[5, 5, 2], [1, 0, 0], [0, 0, 0]]
    with proto.RuleEngine() as engine:
        assert engine.apply(grid, 1) == [[0, 1, 5], [0, 0, 5], [0, 0, 2]]
        assert engine.apply(grid, 2) == [[0, 0, 0], [0, 0, 1], [2, 5, 5]]
        assert engine.apply(grid, 3) == [[2, 0, 0], [5, 0, 0], [5, 1, 0]]
        assert len(engine.executions) == 3
        assert all(row["backend"] == "racket" for row in engine.executions)


def test_promotion_adapter_accepts_native_positional_counts_for_racket_episode():
    assert ADAPTER.is_file(), "promotion adapter is absent"
    assert PROMOTION.is_file(), "promotion contract is absent"
    adapter = _load_module("rotation_parametric_adapter_test", ADAPTER)
    contract = json.loads(PROMOTION.read_text())

    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/88b8e6aaa49d/workspace/parametric/adapter.py",
        "parameters": {"quarter_turns": [1, 2, 3]},
        "default": {"quarter_turns": 2},
        "limits": {"demos": [1, 16], "queries": [1, 16]},
    }
    assert adapter.program({"quarter_turns": 2}) == "(rule! (lambda (g) (flip-ud (flip-lr g))))"
    episode = adapter.generate(31, {"quarter_turns": 1}, 2, 4)
    assert episode["quarter_turns"] == 1
    assert episode["demo_count"] == 2
    assert episode["query_count"] == 4
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert all(check["backend"] == "racket" for check in episode["label_checks"])


def test_evidence_builder_pairs_all_settings_and_writes_portable_receipts(tmp_path):
    proto = _load_module("rotation_parametric_evidence_test", PROTOTYPE)
    report = proto.build_evidence(
        tmp_path,
        seed=41,
        demos=2,
        queries=4,
        engine=MirrorEngine(),
    )

    assert report["schema"] == "arc-rotation-parametric-evidence-v1"
    assert report["status"] == "proposed_unapproved"
    assert report["settings"] == [1, 2, 3]
    assert report["default_quarter_turns"] == 2
    assert report["canonical_default_exact"] is True
    assert report["shared_input_sequence"] is True
    assert report["all_queries_identified"] is True
    assert report["distinct_public_ids"] is True
    assert {row["quarter_turns"] for row in report["episodes"]} == {1, 2, 3}
    assert all(row["demo_count"] == 2 and row["query_count"] == 4 for row in report["episodes"])
    assert all(row["label_backend"] == "test-mirror" for row in report["episodes"])
    assert len({tuple(row["accepted_sample_indices"]) for row in report["episodes"]}) == 1
    assert len({tuple(row["input_sha256s"]) for row in report["episodes"]}) == 1
    assert len({row["program_sha256"] for row in report["episodes"]}) == 3

    assert (tmp_path / "report.json").is_file()
    assert (tmp_path / "manifest.json").is_file()
    assert len(list((tmp_path / "public").glob("*.json"))) == 3
    assert len(list((tmp_path / "private/episodes").glob("*.json"))) == 3
    assert len(list((tmp_path / "private/rules").glob("*.rkt"))) == 3
    on_disk = json.loads((tmp_path / "report.json").read_text())
    assert on_disk == report
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["schema"] == "arc-rotation-parametric-manifest-v1"
    assert "manifest.json" not in manifest["files"]
    assert "report.json" in manifest["files"]
    assert all(not Path(path).is_absolute() for path in manifest["files"])
