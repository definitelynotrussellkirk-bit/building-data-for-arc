from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_ROOT / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "alignment_scope prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "b8d6fabb411e_alignment_scope_prototype", PROTOTYPE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_source_and_boundary_rewrite_is_guarded():
    proto = load_prototype()
    canonical = proto.canonical_program()
    assert proto.render_program("span") == canonical
    assert canonical.count(proto.ROW_SPAN_SITE) == 2
    assert canonical.count(proto.COL_SPAN_SITE) == 2
    boundary = proto.render_program("boundary")
    assert boundary != canonical
    assert boundary.count(proto.ROW_BOUNDARY_SITE) == 2
    assert boundary.count(proto.COL_BOUNDARY_SITE) == 2
    assert proto.ROW_SPAN_SITE not in boundary
    assert proto.COL_SPAN_SITE not in boundary


def test_parameter_is_chosen_once_deterministically_and_validated_strictly():
    proto = load_prototype()
    assert proto.choose_parameters(0) == {"alignment_scope": "span"}
    assert proto.choose_parameters(1) == {"alignment_scope": "boundary"}
    assert proto.choose_parameters(2) == {"alignment_scope": "span"}
    for bad_seed in (True, False, -1, 1.0, "1", None):
        with pytest.raises(ValueError):
            proto.choose_parameters(bad_seed)
    for bad_setting in (True, 1, "interior", None):
        with pytest.raises(ValueError):
            proto.render_program(bad_setting)


def test_fixtures_are_unique_lawful_side_four_inputs_that_separate_settings():
    proto = load_prototype()
    generator, _path, _digest = proto.load_generator()
    grids = proto.fixture_inputs(23)
    assert len(grids) == 4
    assert len({proto.json_sha256(grid) for grid in grids}) == 4
    for grid in grids:
        assert generator.self_check(grid, difficulty="hard") == []
        analysis = generator._analyze(grid)
        assert analysis["square_side"] == 4
        assert analysis["interior_span"]
        span = proto.python_reference(grid, "span")
        boundary = proto.python_reference(grid, "boundary")
        assert span != boundary
        assert boundary != grid


def test_real_racket_matches_python_for_both_settings_and_canonical_default():
    proto = load_prototype()
    grids = proto.fixture_inputs(31)[:2]
    outputs = proto.racket_outputs_all(grids)
    for setting in proto.SETTINGS:
        assert outputs[setting] == [
            proto.python_reference(grid, setting) for grid in grids
        ]
    canonical_report = proto.verify_canonical_default()
    assert canonical_report["pairs_checked"] == 8
    assert canonical_report["all_match"] is True


@pytest.mark.parametrize("seed,setting", [(0, "span"), (1, "boundary")])
def test_complete_episode_is_identifiable_before_query_and_public_copy_is_redacted(
    seed, setting
):
    proto = load_prototype()
    episode = proto.build_episode(seed)
    assert episode["parameters"] == {"alignment_scope": setting}
    assert episode["parameter_draw_count"] == 1
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert episode["rival"]["refuting_demonstration_indices"]
    assert episode["rival"]["query_differs"] is True

    public = proto.public_challenge(episode)
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in (
        "alignment_scope",
        "span",
        "boundary",
        "program",
        "rival",
        "seed",
        "sha256",
    ):
        assert forbidden not in serialized
    assert "output" not in public["test"][0]
    assert all("output" in pair for pair in public["train"])


def test_evidence_bundle_is_self_hashing_and_materializes_both_settings(tmp_path):
    proto = load_prototype()
    report = proto.build_evidence(0, tmp_path)
    assert report["status"] == "verified_prototype"
    assert set(report["settings_verified"]) == {"span", "boundary"}
    assert report["canonical_default"]["all_match"] is True
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["files"]
    for row in manifest["files"]:
        path = tmp_path / row["path"]
        assert path.is_file()
        assert proto.sha256_bytes(path.read_bytes()) == row["sha256"]
