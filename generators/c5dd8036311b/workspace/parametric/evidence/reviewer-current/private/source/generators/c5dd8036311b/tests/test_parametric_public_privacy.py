"""Public export metadata must not reveal the suite's hidden setting."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest

from reviewer_support import find_root


ROOT = find_root(__file__)
FOLDER = ROOT / "generators/c5dd8036311b/workspace/parametric"
SPEC = importlib.util.spec_from_file_location("c5dd_parametric_exporter", FOLDER / "build_evidence.py")
E = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = E
sys.path.insert(0, str(FOLDER))
try:
    SPEC.loader.exec_module(E)
finally:
    sys.path.pop(0)


@pytest.fixture(scope="module")
def suite(tmp_path_factory):
    folder = tmp_path_factory.mktemp("height-privacy") / "suite"
    manifest = E.build_suite(folder, seed_start=17, episodes_per_setting=1, n_train=1)
    return folder, manifest


def private_episodes(folder):
    return [(path.stem, json.loads(path.read_text()))
            for path in sorted((folder / "private/episodes").glob("*.json"))]


def test_public_filenames_and_index_do_not_encode_setting_order(suite):
    folder, manifest = suite
    files = list((folder / "public").glob("*.json"))
    challenges = [path for path in files if path.name != "index.json"]
    assert len(challenges) == manifest["episode_count"] == 16
    assert all(re.fullmatch(r"[0-9a-f]{32}\.json", path.name) for path in challenges), (
        "Public filenames must be random opaque IDs, not the ordered setting index"
    )
    index = json.loads((folder / "public/index.json").read_text())
    assert set(index) == {"challenges"}
    assert len(index["challenges"]) == len(set(index["challenges"])) == 16
    assert set(index["challenges"]) == {path.name for path in challenges}
    for path in challenges:
        challenge = json.loads(path.read_text())
        assert set(challenge) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])


def test_suite_inputs_do_not_identify_parameters_by_seed_lookup(suite):
    folder, manifest = suite
    episodes = [episode for _, episode in private_episodes(folder)]
    assert len({tuple(sorted(episode["parameters"].items())) for episode in episodes}) == 16
    assert {episode["seed"] for episode in episodes} == {manifest["seed_start"]}, (
        "Every setting must share the same input seed for a matched replica; "
        "a setting-specific seed search can disclose parameters through input lookup"
    )
    signatures = {json.dumps([pair["input"] for pair in episode["pairs"]]) for episode in episodes}
    assert len(signatures) == 1
    assert all(episode["parameter_selection"] == "explicit" for episode in episodes)


def test_reexport_randomizes_public_identity_without_changing_content(suite, tmp_path):
    folder, _ = suite
    episodes = private_episodes(folder)
    first = E.export_public(episodes, tmp_path / "first")
    second = E.export_public(episodes, tmp_path / "second")
    first_paths = {row["public_filename"] for row in first}
    second_paths = {row["public_filename"] for row in second}
    assert first_paths.isdisjoint(second_paths)
    assert {row["private_episode_id"] for row in first} == {name for name, _ in episodes}
    assert {row["private_episode_id"] for row in second} == {name for name, _ in episodes}

    def contents(path):
        return Counter(json.dumps(json.loads(file.read_text()), sort_keys=True)
                       for file in path.glob("*.json") if file.name != "index.json")

    assert contents(tmp_path / "first") == contents(tmp_path / "second")
    for name in ("first", "second"):
        index = json.loads((tmp_path / name / "index.json").read_text())
        assert set(index) == {"challenges"}
        assert len(index["challenges"]) == 16
