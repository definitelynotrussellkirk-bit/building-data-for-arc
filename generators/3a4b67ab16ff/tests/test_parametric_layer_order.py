from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "3a4b67ab16ff"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
CANONICAL_PATH = (
    ROOT
    / "shared"
    / "data"
    / "base"
    / "solutions"
    / "training"
    / "1c02dbbe__3a4b67ab16ff.json"
)


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "layer-order prototype has not been implemented"
    name = "_test_parametric_" + hashlib.sha256(PROTOTYPE_PATH.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket_bridge():
    with RacketBridge(max_calls_before_restart=512) as bridge:
        yield bridge


def _canonical_source() -> str:
    return json.loads(CANONICAL_PATH.read_text())["racket_target"]["raw_code"]


def _visible_grids(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_materializes_exact_canonical_source_and_alternative_changes_only_order():
    module = _load_prototype()
    canonical = _canonical_source()
    assert hashlib.sha256(canonical.encode()).hexdigest() == module.CANONICAL_PROGRAM_SHA256
    assert canonical.count("(range 1 10)") == 1
    assert module.DEFAULT_LAYER_ORDER == "ascending"
    assert module.ALLOWED_LAYER_ORDERS == ("ascending", "descending")
    assert module.materialize_rule("ascending") == canonical
    assert module.materialize_rule("descending") == canonical.replace(
        "(range 1 10)", "(reverse (range 1 10))"
    )


def test_racket_backed_episodes_hold_one_setting_and_refute_the_rival(racket_bridge):
    module = _load_prototype()
    for index, setting in enumerate(module.ALLOWED_LAYER_ORDERS):
        episode = module.build_episode(
            700 + index,
            layer_order=setting,
            train_count=3,
            test_count=4,
            bridge=racket_bridge,
        )
        assert episode["parameters"] == {"layer_order": setting}
        assert episode["defaults"] == {"layer_order": "ascending"}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        grids = _visible_grids(episode)
        serialized = [json.dumps(grid, separators=(",", ":")) for grid in grids]
        assert len(serialized) == len(set(serialized)) == 7
        assert episode["checks"]["setting_selected_once"] is True
        assert episode["checks"]["all_labels_from_racket"] is True
        assert episode["checks"]["demonstrations_refute_rival"] is True
        assert episode["checks"]["all_queries_differ_from_rival"] is True
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] != pair["rival_output"]
            assert pair["distinguishes_rival"] is True


def test_input_draws_are_deterministic_and_independent_of_hidden_setting(racket_bridge):
    module = _load_prototype()
    ascending = module.build_episode(812, layer_order="ascending", bridge=racket_bridge)
    descending = module.build_episode(812, layer_order="descending", bridge=racket_bridge)
    assert _visible_grids(ascending) == _visible_grids(descending)
    assert [pair["output"] for pair in ascending["train"] + ascending["test"]] != [
        pair["output"] for pair in descending["train"] + descending["test"]
    ]
    replay = module.build_episode(812, layer_order="ascending", bridge=racket_bridge)
    assert replay == ascending


def test_public_projection_and_identifier_depend_only_on_visible_challenge_bytes(racket_bridge):
    module = _load_prototype()
    episode = module.build_episode(913, layer_order="ascending", bridge=racket_bridge)
    public = module.public_challenge(episode)
    expected_bytes = public_challenge_bytes(episode)
    assert module.public_bytes(episode) == expected_bytes
    assert public == json.loads(expected_bytes)
    assert module.public_id(episode) == public_challenge_id(episode)
    assert module.public_filename(episode) == f"challenge-{public_challenge_id(episode)}.json"
    assert all(set(pair) == {"input"} for pair in public["test"])

    private_only_change = deepcopy(episode)
    private_only_change["seed"] += 1000
    private_only_change["parameters"]["layer_order"] = "descending"
    private_only_change["program"]["source"] = "private mutation"
    for pair in private_only_change["test"]:
        pair["output"] = [[9]]
        pair["rival_output"] = [[8]]
    assert module.public_bytes(private_only_change) == expected_bytes
    assert module.public_filename(private_only_change) == module.public_filename(episode)


def test_materializer_retains_two_settings_with_exact_public_files(tmp_path: Path, racket_bridge):
    module = _load_prototype()
    out = tmp_path / "evidence"
    report = module.materialize(
        out,
        seed_start=1200,
        train_count=3,
        test_count=4,
        bridge=racket_bridge,
    )
    assert report["parameter"] == {
        "name": "layer_order",
        "allowed_values": ["ascending", "descending"],
        "default": "ascending",
    }
    assert report["episode_count"] == 2
    assert report["all_racket_labels"] is True
    assert report["all_demonstrations_refute_rival"] is True
    assert report["all_queries_differ_from_rival"] is True
    ids = [row["public_id"] for row in report["episodes"]]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids)) == 2
    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        episode = json.loads(private_path.read_text())
        assert public_path.read_bytes() == public_challenge_bytes(episode)
        assert public_path.name == f"challenge-{public_challenge_id(episode)}.json"
        public_text = public_path.read_text()
        assert "layer_order" not in public_text
        assert "rival_output" not in public_text
        assert '"seed"' not in public_text
        assert '"program"' not in public_text

    with pytest.raises(FileExistsError):
        module.materialize(out, seed_start=1200)


def test_materializer_emits_public_files_in_visible_id_order(
    tmp_path: Path,
    racket_bridge,
    monkeypatch,
):
    module = _load_prototype()
    observed_public_writes: list[str] = []
    original_write_bytes = Path.write_bytes

    def record_public_write(path: Path, payload: bytes) -> int:
        if path.parent.name == "public":
            observed_public_writes.append(path.name)
        return original_write_bytes(path, payload)

    monkeypatch.setattr(Path, "write_bytes", record_public_write)
    report = module.materialize(
        tmp_path / "evidence",
        seed_start=1,
        train_count=3,
        test_count=4,
        bridge=racket_bridge,
    )
    manifest_order = [Path(row["public_path"]).name for row in report["episodes"]]

    assert observed_public_writes == manifest_order == sorted(manifest_order)


def test_duplicate_public_payload_is_rejected_before_any_public_write(
    tmp_path: Path,
    racket_bridge,
    monkeypatch,
):
    module = _load_prototype()
    retained_episode = module.build_episode(
        3,
        layer_order="ascending",
        train_count=3,
        test_count=4,
        bridge=racket_bridge,
    )
    observed_public_writes: list[str] = []
    original_write_bytes = Path.write_bytes

    def record_public_write(path: Path, payload: bytes) -> int:
        if path.parent.name == "public":
            observed_public_writes.append(path.name)
        return original_write_bytes(path, payload)

    def duplicate_visible_episode(seed: int, **kwargs):
        episode = deepcopy(retained_episode)
        episode["seed"] = seed
        episode["parameters"][module.PARAMETER_NAME] = module.choose_layer_order(seed)
        return episode

    monkeypatch.setattr(Path, "write_bytes", record_public_write)
    monkeypatch.setattr(module, "build_episode", duplicate_visible_episode)

    with pytest.raises(ValueError, match="duplicate visible public challenge payload"):
        module.materialize(
            tmp_path / "evidence",
            seed_start=1,
            train_count=3,
            test_count=4,
            bridge=racket_bridge,
        )

    assert observed_public_writes == []


@pytest.mark.parametrize("value", [True, -1, "7"])
def test_seed_validation_fails_closed(value):
    module = _load_prototype()
    with pytest.raises((TypeError, ValueError)):
        module.build_episode(value)


@pytest.mark.parametrize("value", [None, "sideways", 1, True])
def test_layer_order_validation_fails_closed(value):
    module = _load_prototype()
    with pytest.raises((TypeError, ValueError)):
        module.build_episode(1, layer_order=value)


@pytest.mark.parametrize(
    ("train_count", "test_count"),
    [(0, 4), (3, 0), (True, 4), (3, False), (21, 4), (3, 21)],
)
def test_count_validation_fails_closed(train_count, test_count):
    module = _load_prototype()
    with pytest.raises((TypeError, ValueError)):
        module.build_episode(1, train_count=train_count, test_count=test_count)
