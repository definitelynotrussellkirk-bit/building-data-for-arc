"""Focused tests for the isolated output-extent parametric prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
WORKSPACE = HOME / "workspace"
PROTOTYPE_PATH = WORKSPACE / "parametric" / "prototype.py"
sys.path.insert(0, str(WORKSPACE))
from reference_probe import canonical_program, recover_details  # noqa: E402

REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), f"missing prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "output_extent_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_parameter_contract_and_exact_canonical_default():
    prototype = _load_prototype()
    assert prototype.PARAMETER == "output_extent"
    assert prototype.VALUES == ("full_grid", "tile_only")
    assert prototype.DEFAULT == "full_grid"

    programs = prototype.materialize_programs()
    assert programs["full_grid"] == canonical_program()
    assert programs["tile_only"] != programs["full_grid"]
    assert programs["tile_only"].count("(build-grid tile-pr") == 1
    assert programs["tile_only"].count("(list r c)") == 1
    assert "(build-grid hh" not in programs["tile_only"]


def test_real_racket_episode_is_fixed_identifiable_and_four_query():
    prototype = _load_prototype()
    episode = prototype.build_episode(
        seed=73_001,
        parameter="tile_only",
        n_train=3,
        n_test=4,
    )

    assert episode["parameter_name"] == "output_extent"
    assert episode["parameter"] == "tile_only"
    assert episode["default"] == "full_grid"
    assert episode["n_train"] == 3
    assert episode["n_test"] == 4
    assert episode["label_source"] == "real_racket"
    assert episode["rival_parameter"] == "full_grid"
    assert episode["rival_fits_all_demos"] is False
    assert episode["all_demos_distinguish"] is True
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4

    pairs = episode["pairs"]
    assert len({_grid_key(pair["input"]) for pair in pairs}) == 7
    for pair in pairs:
        assert pair["settings_disagree"] is True
        details = recover_details(deepcopy(pair["input"]))
        assert details is not None
        full_grid, pr, pc = details
        assert pair["outputs_by_parameter"]["full_grid"] == full_grid
        assert pair["outputs_by_parameter"]["tile_only"] == [
            row[:pc] for row in full_grid[:pr]
        ]
        assert pair["selected_output"] == pair["outputs_by_parameter"]["tile_only"]

    public = episode["public_challenge"]
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert episode["public_id"] == public_challenge_id(public)
    assert episode["public_bytes_sha256"] == episode["public_id"]
    assert public_challenge_bytes(public).endswith(b"\n")


def test_writer_uses_visible_content_id_and_keeps_private_data_out_of_public(tmp_path):
    prototype = _load_prototype()
    episode = prototype.build_episode(
        seed=73_002,
        parameter="full_grid",
        n_train=3,
        n_test=4,
    )
    paths = prototype.write_episode(episode, tmp_path)

    public_path = Path(paths["public"])
    private_path = Path(paths["private"])
    summary_path = Path(paths["summary"])
    assert public_path.stem == episode["public_id"]
    assert private_path.stem == episode["public_id"]
    assert public_path.read_bytes() == public_challenge_bytes(episode["public_challenge"])

    public_text = public_path.read_text(encoding="utf-8")
    for hidden in ("output_extent", "full_grid", "tile_only", "73002", "program"):
        assert hidden not in public_text

    retained = json.loads(private_path.read_text(encoding="utf-8"))
    assert retained["parameter"] == "full_grid"
    assert len(retained["test"]) == 4
    assert all("selected_output" in pair for pair in retained["test"])
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["public_id"] == episode["public_id"]
    assert summary["label_source"] == "real_racket"


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"seed": True}, TypeError),
        ({"seed": 1, "parameter": "other"}, ValueError),
        ({"seed": 1, "n_train": 0}, ValueError),
        ({"seed": 1, "n_test": 0}, ValueError),
    ],
)
def test_invalid_episode_requests_fail_loudly(kwargs, error):
    prototype = _load_prototype()
    with pytest.raises(error):
        prototype.build_episode(**kwargs)


def test_writer_rejects_duplicate_visible_payload(tmp_path):
    prototype = _load_prototype()
    public = {
        "train": [{"input": [[1]], "output": [[1]]}],
        "test": [{"input": [[2]]}],
    }
    episode = {
        "schema": "writer-regression-v1",
        "public_id": public_challenge_id(public),
        "public_challenge": public,
        "parameter_name": "output_extent",
        "parameter": "full_grid",
        "default": "full_grid",
        "n_train": 1,
        "n_test": 1,
        "label_source": "test_fixture",
        "program_sha256": {"full_grid": "a", "tile_only": "b"},
        "all_demos_distinguish": True,
        "rival_fits_all_demos": False,
        "pairs": [{"settings_disagree": True}],
    }
    prototype.write_episode(episode, tmp_path)
    with pytest.raises(FileExistsError, match="duplicate public challenge"):
        prototype.write_episode(episode, tmp_path)
