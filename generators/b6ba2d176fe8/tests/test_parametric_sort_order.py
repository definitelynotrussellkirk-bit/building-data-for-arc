"""Focused tests for the separate b6ba2d176fe8 sort-order prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / "workspace/parametric/prototype.py"
ADAPTER = TASK_HOME / "workspace/parametric/adapter.py"
PROMOTION = TASK_HOME / "workspace/parametric/promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"required task-local file is missing: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_prototype():
    return _load(PROTOTYPE, "b6ba2d176fe8_parametric")


def load_adapter():
    return _load(ADAPTER, "b6ba2d176fe8_parametric_adapter")


def test_settings_validation_and_once_per_episode_selection():
    proto = load_prototype()
    assert proto.DEFAULT.sort_order == "left_to_right"
    with pytest.raises(ValueError):
        proto.Settings("sideways")
    first = proto.select_settings(20261023, sort_order="sample")
    second = proto.select_settings(20261023, sort_order="sample")
    assert first == second
    assert first in proto.ALL_SETTINGS


def test_default_program_is_exact_authority_and_alternate_is_bounded_edit():
    proto = load_prototype()
    default = proto.program(proto.DEFAULT)
    alternate = proto.program(proto.Settings("right_to_left"))
    assert default == proto.canonical_program()
    assert default == proto.selected_target_program()
    assert alternate != default
    assert "(reverse (sort-by objs" in alternate
    assert proto.text_digest(default) == proto.authority_identity()["canonical_program_sha256"]


def test_real_racket_outputs_separate_both_settings():
    proto = load_prototype()
    grid = proto.sample_inputs(911, count=1)[0]
    with proto.RacketLabels() as labels:
        left = labels.output(grid, proto.Settings("left_to_right"))
        right = labels.output(grid, proto.Settings("right_to_left"))
    assert left == proto.transform(grid, proto.Settings("left_to_right"))
    assert right == proto.transform(grid, proto.Settings("right_to_left"))
    assert left != right


def test_complete_episodes_have_independent_counts_and_four_distinct_queries():
    proto = load_prototype()
    evidence = proto.build_evidence(
        20261023,
        proto.ALL_SETTINGS,
        demos=3,
        queries=4,
    )
    assert evidence["status"] == "pass"
    assert evidence["episode_policy"]["demonstrations"] == 3
    assert evidence["episode_policy"]["queries"] == 4
    assert len(evidence["episodes"]) == 2
    for episode in evidence["episodes"]:
        assert episode["demo_count"] == 3
        assert episode["query_count"] == 4
        assert len(episode["pairs"]) == 7
        assert [pair["split"] for pair in episode["pairs"]] == [
            "train",
            "train",
            "train",
            "test",
            "test",
            "test",
            "test",
        ]
        assert len({pair["input_sha256"] for pair in episode["pairs"]}) == 7
        assert len(episode["rivals"]) == 1
        rival = episode["rivals"][0]
        assert rival["status"] == "refuted_by_demonstrations"
        assert len(rival["demo_matches"]) == 3
        assert len(rival["query_matches"]) == 4
        assert not all(rival["demo_matches"])
        assert rival["query_matches"] == [False, False, False, False]


@pytest.mark.parametrize(
    ("demos", "queries"),
    [
        (2, 4),
        (9, 4),
        (True, 4),
        (3.0, 4),
        (3, 0),
        (3, 9),
        (3, False),
        (3, "4"),
    ],
)
def test_episode_count_limits_are_strict_and_checked_before_racket(demos, queries):
    proto = load_prototype()
    with pytest.raises(ValueError):
        proto.build_evidence(17, (proto.DEFAULT,), demos=demos, queries=queries)


def test_public_identity_uses_only_exact_visible_bytes():
    proto = load_prototype()
    evidence = proto.build_evidence(20261023, (proto.DEFAULT,), demos=3, queries=4)
    episode = evidence["episodes"][0]
    visible = proto.public_episode(episode)
    identifier = public_challenge_id(visible)

    assert proto.public_identity(episode) == identifier
    assert episode["public_id"] == identifier
    assert episode["public_path"] == f"public/{identifier}.json"

    hidden_change = copy.deepcopy(episode)
    hidden_change["seed"] = 999
    hidden_change["parameters"] = {"sort_order": "private-only-change"}
    hidden_change["program"] = "private-only-change"
    hidden_change["program_sha256"] = "private-only-change"
    for pair in hidden_change["pairs"]:
        if pair["split"] == "test":
            pair["output"] = [[9]]
            pair["output_sha256"] = "private-only-change"
    assert proto.public_identity(hidden_change) == identifier

    visible_change = copy.deepcopy(episode)
    visible_change["pairs"][0]["output"][0][0] = (
        visible_change["pairs"][0]["output"][0][0] + 1
    ) % 10
    assert proto.public_identity(visible_change) != identifier


def test_emit_and_verify_public_bundle_has_four_queries_and_canonical_bytes(tmp_path):
    proto = load_prototype()
    bundle = tmp_path / "bundle"
    receipt = proto.emit_bundle(
        20261023,
        proto.ALL_SETTINGS,
        bundle,
        demos=3,
        queries=4,
    )
    assert receipt["status"] == "pass"

    public_files = sorted((bundle / "public").glob("*.json"))
    assert len(public_files) == 2
    for path in public_files:
        public = json.loads(path.read_text())
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert path.read_bytes() == public_challenge_bytes(public)
        assert path.name == public_challenge_id(public) + ".json"
        leaked = path.read_text().lower()
        for forbidden in ("sort_order", "program", "seed", "query_output"):
            assert forbidden not in leaked

    verification = proto.verify_bundle(bundle)
    assert verification["status"] == "pass"
    assert verification["episodes_reexecuted"] == 2
    assert verification["pairs_reexecuted"] == 14


def test_cli_forwards_independent_demo_and_query_counts(monkeypatch, tmp_path, capsys):
    proto = load_prototype()
    captured = {}

    def fake_emit(seed, settings, output, *, demos, queries):
        captured.update(
            seed=seed,
            settings=tuple(settings),
            output=Path(output),
            demos=demos,
            queries=queries,
        )
        return {"schema": proto.SCHEMA, "status": "pass"}

    monkeypatch.setattr(proto, "emit_bundle", fake_emit)
    result = proto.main(
        [
            "emit",
            "--seed",
            "17",
            "--sort-order",
            "right_to_left",
            "--demos",
            "4",
            "--queries",
            "2",
            "--out",
            str(tmp_path / "bundle"),
        ]
    )
    assert result == 0
    assert captured == {
        "seed": 17,
        "settings": (proto.Settings("right_to_left"),),
        "output": tmp_path / "bundle",
        "demos": 4,
        "queries": 2,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "pass"


def test_cli_returns_nonzero_when_emitted_evidence_fails(monkeypatch, tmp_path):
    proto = load_prototype()
    monkeypatch.setattr(
        proto,
        "emit_bundle",
        lambda seed, settings, output, *, demos, queries: {
            "schema": proto.SCHEMA,
            "status": "fail",
            "bundle": str(output),
        },
    )
    assert proto.main(["emit", "--out", str(tmp_path / "failed")]) == 1


def test_promotion_adapter_is_thin_and_contract_supports_four_queries():
    proto = load_prototype()
    adapter = load_adapter()
    promotion = json.loads(PROMOTION.read_text())

    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/b6ba2d176fe8/workspace/parametric/adapter.py",
        "parameters": {"sort_order": ["left_to_right", "right_to_left"]},
        "default": {"sort_order": "left_to_right"},
        "limits": {"demos": [3, 8], "queries": [1, 8]},
    }

    settings = {"sort_order": "right_to_left"}
    episode = adapter.generate(29, settings, demos=3, queries=4)
    assert set(episode) == {"train", "test", "program_solution"}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert len(
        {
            proto.digest(pair["input"])
            for split in ("train", "test")
            for pair in episode[split]
        }
    ) == 7
    assert episode["program_solution"] == adapter.program(settings)
    assert episode["program_solution"] == proto.program(proto.Settings("right_to_left"))
    for split in ("train", "test"):
        for pair in episode[split]:
            assert pair["output"] == proto.transform(
                pair["input"], proto.Settings("right_to_left")
            )
