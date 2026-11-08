"""Focused tests for the task-local component-connectivity prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "a631936f7715"
ROOT = find_root(__file__)
PARAMETRIC_DIR = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC_DIR / "prototype.py"
VERIFY_PATH = PARAMETRIC_DIR / "verify.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "component-connectivity prototype is missing"
    spec = importlib.util.spec_from_file_location("a631936f7715_parametric", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_verify():
    assert VERIFY_PATH.is_file(), "component-connectivity verifier is missing"
    spec = importlib.util.spec_from_file_location("a631936f7715_parametric_verify", VERIFY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    assert stripped.startswith("(rule!") and stripped.endswith(")")
    return stripped[len("(rule!") : -1].strip()


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def test_parameter_is_bounded_and_default_is_exact_canonical_authority():
    proto = _load_prototype()
    assert proto.ALLOWED_CONNECTIVITIES == (4, 8)
    assert proto.DEFAULT_CONNECTIVITY == 4
    assert proto.PARAMETERS == {"component_connectivity": (4, 8)}
    assert proto.program_for(4) == _canonical_program()
    assert proto.program_for(8) != proto.program_for(4)
    assert {proto.choose_connectivity(seed) for seed in range(8)} == {4, 8}
    for invalid in (True, 0, 6, "4", None):
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(invalid)


def test_default_setting_preserves_every_canonical_label():
    proto = _load_prototype()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 6
    assert all(proto.apply_python(pair["input"], 4) == pair["output"] for pair in pairs)


def test_each_setting_builds_a_lawful_complete_distinguishing_episode():
    proto = _load_prototype()
    generator, _path, _sha = load_selected_generator(TASK_ID, root=ROOT)
    for connectivity in proto.ALLOWED_CONNECTIVITIES:
        episode = proto.build_episode(20261023, connectivity=connectivity, n_train=3, n_test=1)
        assert episode["parameters"] == {"component_connectivity": connectivity}
        assert episode["program"] == proto.program_for(connectivity)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert proto.episode_errors(episode) == []
        rival = 8 if connectivity == 4 else 4
        for pair in episode["train"] + episode["test"]:
            assert generator.self_check(pair["input"]) == []
            assert proto.apply_python(pair["input"], connectivity) == pair["output"]
            assert proto.apply_python(pair["input"], rival) != pair["output"]

        public = proto.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        blob = json.dumps(public, sort_keys=True)
        assert "component_connectivity" not in blob
        assert "program" not in blob


def test_retained_episode_labels_are_executed_by_each_exact_racket_program():
    proto = _load_prototype()
    with RacketBridge(timeout=30, max_calls_before_restart=32) as bridge:
        for connectivity in proto.ALLOWED_CONNECTIVITIES:
            episode = proto.build_episode(20261023, connectivity=connectivity, n_train=3, n_test=4)
            assert len(episode["test"]) == 4
            all_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs}) == 7
            source = proto.program_for(connectivity)
            for pair in episode["train"] + episode["test"]:
                actual = bridge.eval_text(_application(source, pair["input"]))
                assert actual == pair["output"]


def test_episode_counts_are_independent_and_finite_support_never_clones_pairs():
    proto = _load_prototype()
    assert proto.MAX_UNIQUE_INPUTS == 1680

    episode = proto.build_episode(20261023, connectivity=4, n_train=2, n_test=4)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 6
    assert proto.episode_errors(episode) == []

    full_support = proto.build_inputs(17, proto.MAX_UNIQUE_INPUTS)
    assert len(full_support) == proto.MAX_UNIQUE_INPUTS
    assert len({json.dumps(grid, separators=(",", ":")) for grid in full_support}) == proto.MAX_UNIQUE_INPUTS
    with pytest.raises(ValueError, match="finite support"):
        proto.build_inputs(17, proto.MAX_UNIQUE_INPUTS + 1)


def test_public_artifact_name_uses_only_visible_demonstrations_and_query_inputs():
    proto = _load_prototype()
    episode = proto.build_episode(20261023, connectivity=4, n_train=2, n_test=4)
    original_name = proto.public_artifact_name(episode)
    public = proto.public_challenge(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", original_name)
    assert original_name == f"challenge-{public_challenge_id(public)}.json"

    private_changes = deepcopy(episode)
    private_changes["seed"] = 999999
    private_changes["parameters"] = {"component_connectivity": 8}
    private_changes["program"] = "private program changed"
    private_changes["generator_source"] = "private/path.py"
    private_changes["generator_sha256"] = "0" * 64
    private_changes["train"][0]["sampling"] = {"seed": -1, "input_index": 99}
    private_changes["test"][0]["sampling"] = {"seed": -2, "input_index": 100}
    private_changes["test"][0]["output"] = [[0]]
    assert proto.public_artifact_name(private_changes) == original_name

    visible_demo_change = deepcopy(episode)
    visible_demo_change["train"][0]["output"][0][0] = (
        visible_demo_change["train"][0]["output"][0][0] + 1
    ) % 10
    assert proto.public_artifact_name(visible_demo_change) != original_name

    visible_query_change = deepcopy(episode)
    visible_query_change["test"][0]["input"][0][0] = (
        visible_query_change["test"][0]["input"][0][0] + 1
    ) % 10
    assert proto.public_artifact_name(visible_query_change) != original_name


def test_writer_separates_opaque_public_files_from_private_setting_artifacts(tmp_path):
    proto = _load_prototype()
    verifier = _load_verify()
    episodes = {
        connectivity: proto.build_episode(
            20261023, connectivity=connectivity, n_train=2, n_test=4
        )
        for connectivity in proto.ALLOWED_CONNECTIVITIES
    }
    programs = {
        connectivity: proto.program_for(connectivity)
        for connectivity in proto.ALLOWED_CONNECTIVITIES
    }
    generator_sha = next(iter(episodes.values()))["generator_sha256"]

    manifest = verifier.materialize_artifacts(
        tmp_path,
        episodes=episodes,
        programs=programs,
        seed=20261023,
        generator_sha=generator_sha,
    )

    public_dir = tmp_path / "public"
    public_paths = sorted(path.relative_to(public_dir) for path in public_dir.glob("*.json"))
    expected_names = sorted(proto.public_artifact_name(episode) for episode in episodes.values())
    assert [path.as_posix() for path in public_paths] == expected_names
    assert all("connectivity" not in path.as_posix() for path in public_paths)
    assert all("20261023" not in path.as_posix() for path in public_paths)

    for episode in episodes.values():
        path = public_dir / proto.public_artifact_name(episode)
        raw = path.read_bytes()
        payload = json.loads(raw)
        visible = proto.public_challenge(episode)
        assert raw == public_challenge_bytes(visible)
        assert hashlib.sha256(raw).hexdigest() == path.stem.removeprefix("challenge-")
        assert payload == visible
        record = manifest["public_files"][path.name]
        assert record == {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        assert len(payload["train"]) == 2
        assert len(payload["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in payload["train"])
        assert all(set(pair) == {"input"} for pair in payload["test"])

    assert (tmp_path / "private" / "connectivity-4-episode.json").is_file()
    assert (tmp_path / "private" / "connectivity-8-episode.json").is_file()
    assert list(manifest["public_files"]) == sorted(expected_names)
    assert set(manifest["private_settings"]) == {"4", "8"}

    class DuplicateVisibleEpisodes(dict):
        def items(self):
            episode = episodes[4]
            return [(4, episode), (4, deepcopy(episode))]

    with pytest.raises(ValueError, match="duplicate visible public challenge"):
        verifier.materialize_artifacts(
            tmp_path / "duplicate",
            episodes=DuplicateVisibleEpisodes(),
            programs={4: programs[4]},
            seed=20261023,
            generator_sha=generator_sha,
        )
