"""Observe real public writes: private seed order must not leak through ordering."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root


ROOT = find_root(__file__)
SOURCE = ROOT / "generators/f59691ac00f3/workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def prepared():
    spec = importlib.util.spec_from_file_location("f596_write_order", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with RacketBridge() as bridge:
        episodes = {
            seed: module.make_episode(seed, root=ROOT, bridge=bridge)
            for seed in (0, 1)
        }
        yield module, bridge, episodes


def observe_public_writes(monkeypatch):
    writes = []
    original = Path.write_bytes

    def record(path, body):
        if path.parent.name == "public":
            writes.append((path.name, body))
        return original(path, body)

    monkeypatch.setattr(Path, "write_bytes", record)
    return writes


def test_public_files_are_physically_written_in_visible_hash_order(
    prepared, monkeypatch, tmp_path
):
    prototype, bridge, episodes = prepared
    seeds = sorted(episodes, key=lambda seed: episodes[seed]["public_id"], reverse=True)
    monkeypatch.setattr(
        prototype, "make_episode", lambda seed, **kwargs: copy.deepcopy(episodes[seed])
    )
    writes = observe_public_writes(monkeypatch)
    result = prototype.materialize(
        tmp_path / "sorted", seeds=seeds, root=ROOT, bridge=bridge
    )
    names = [name for name, _ in writes]
    assert len(names) == 2
    assert names == sorted(names), "public filesystem creation order leaks seed ordering"
    assert [row["public_id"] for row in result["episodes"]] == sorted(
        episode["public_id"] for episode in episodes.values()
    )


def test_duplicate_visible_lessons_fail_before_any_public_write(
    prepared, monkeypatch, tmp_path
):
    prototype, bridge, episodes = prepared

    def colliding_episode(seed, **kwargs):
        episode = copy.deepcopy(episodes[0])
        episode["seed"] = seed  # Private metadata cannot distinguish visible content.
        return episode

    monkeypatch.setattr(prototype, "make_episode", colliding_episode)
    writes = observe_public_writes(monkeypatch)
    destination = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate visible public challenge"):
        prototype.materialize(destination, seeds=(0, 2), root=ROOT, bridge=bridge)
    assert writes == [], "duplicate preflight happened after public files were written"
    assert not destination.exists()
    assert not destination.with_name(destination.name + ".tmp").exists()
