"""Focused tests for reusable teaching and public-projection audit tools."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def adapter():
    return _load("test_629ec8fd452e_audit_adapter", PARAMETRIC / "adapter.py")


def verify():
    assert (PARAMETRIC / "verify.py").is_file(), "reusable verify.py is missing"
    return _load("test_629ec8fd452e_verify", PARAMETRIC / "verify.py")


def test_finite_rival_audit_has_no_demo_survivor_that_disagrees_on_a_query():
    report = verify().finite_rival_audit(seeds=range(12), demo_counts=(2, 3, 6))
    assert report["status"] == "passed"
    assert report["episodes_checked"] == 12 * 3 * 2
    assert report["failures"] == []
    assert {
        "declared_other_setting",
        "first_hole_color_broadcast",
        "largest_foreground_color_broadcast",
        "winning_source_only",
        "bbox_interior_missing",
    }.issubset(report["finite_rivals"])


def test_one_query_projection_is_private_invariant_and_first_turn_stable():
    module = adapter()
    audit = verify()
    episode = module.generate(5, {"output_scope": "largest_hole_color_relay"}, 3, 4)
    projection = audit.one_query_projection(episode, 0)
    assert set(projection) == {"train", "test"}
    assert len(projection["train"]) == 3
    assert len(projection["test"]) == 1
    assert set(projection["test"][0]) == {"input"}
    assert projection["test"][0]["input"] == episode["test"][0]["input"]

    public_id = audit.public_projection_id(episode, 0)
    hidden = deepcopy(episode)
    hidden["seed"] = 999
    hidden["settings"] = {"output_scope": "all_holes"}
    hidden["program_solution"] = "private replacement"
    for pair in hidden["test"]:
        pair["output"] = [[9]]
    assert audit.public_projection_id(hidden, 0) == public_id

    four_query_episode = module.generate(5, {"output_scope": "largest_hole_color_relay"}, 3, 4)
    one_query_episode = module.generate(5, {"output_scope": "largest_hole_color_relay"}, 3, 1)
    assert audit.public_projection_payload(four_query_episode, 0) == audit.public_projection_payload(
        one_query_episode, 0
    )


@pytest.mark.parametrize("bad", [True, -1, 4, 1.0, "0"])
def test_one_query_projection_rejects_nonliteral_or_out_of_range_index(bad):
    episode = adapter().generate(0, {"output_scope": "all_holes"}, 2, 4)
    with pytest.raises(ValueError):
        verify().one_query_projection(episode, bad)


def test_public_projection_writer_preflights_duplicates_and_existing_destination(tmp_path):
    module = adapter()
    audit = verify()
    episode = module.generate(3, {"output_scope": "all_holes"}, 2, 4)
    records = [{"seed": 3, "output_scope": "all_holes", "episode": episode}]
    destination = tmp_path / "public"
    rows = audit.write_public_projection_batch(records, destination)
    assert len(rows) == 4
    assert len({row["public_id"] for row in rows}) == 4
    assert all((destination / row["filename"]).is_file() for row in rows)
    for row in rows:
        raw = (destination / row["filename"]).read_bytes()
        assert row["public_id"] == row["filename"].removesuffix(".json")
        parsed = json.loads(raw)
        assert len(parsed["test"]) == 1
        assert set(parsed["test"][0]) == {"input"}

    with pytest.raises(FileExistsError):
        audit.write_public_projection_batch(records, destination)
    with pytest.raises(ValueError, match="duplicate visible challenge"):
        audit.write_public_projection_batch(records + records, tmp_path / "duplicates")



def test_normalize_public_check_paths_makes_paths_repository_relative(tmp_path):
    repo = tmp_path / "repo"
    public = repo / "generators" / "task" / "public" / "challenge.json"
    public.parent.mkdir(parents=True)
    public.write_text("{}\n")
    report = {
        "status": "passed",
        "files": [{"path": str(public), "sha256": "abc"}],
        "findings": [{"path": str(public), "code": "example", "detail": "example"}],
    }

    normalized = verify().normalize_public_check_paths(report, repo)

    expected = "generators/task/public/challenge.json"
    assert normalized["files"][0]["path"] == expected
    assert normalized["findings"][0]["path"] == expected
    assert report["files"][0]["path"] == str(public)


def test_normalize_public_check_paths_rejects_paths_outside_repository(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    report = {
        "status": "passed",
        "files": [{"path": str(tmp_path / "outside.json"), "sha256": "abc"}],
        "findings": [],
    }
    with pytest.raises(ValueError, match="outside repository root"):
        verify().normalize_public_check_paths(report, repo)
