from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parents[1]
PROTOTYPE = HERE / "prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "tile_color_mode prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "f4f11295a6f5_tile_color_mode_prototype", PROTOTYPE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_byte_identical_to_canonical_and_alternative_is_guarded():
    proto = load_prototype()
    canonical = proto.canonical_program()
    assert proto.render_program("exact") == canonical
    selector = proto.render_program("selector")
    assert selector != canonical
    assert selector.count(proto.ALTERNATIVE_SITE) == 1
    assert canonical.count(proto.CANONICAL_SITE) == 1


def test_parameter_is_chosen_once_and_both_settings_are_reachable():
    proto = load_prototype()
    assert proto.choose_parameters(0) == {"tile_color_mode": "exact"}
    assert proto.choose_parameters(1) == {"tile_color_mode": "selector"}
    for bad in (True, 1.0, "1", None, -1):
        with pytest.raises(ValueError):
            proto.choose_parameters(bad)


def test_fixture_inputs_are_unique_lawful_multicolor_family_members():
    proto = load_prototype()
    generator, _path, _digest = proto.load_generator()
    grids = proto.fixture_inputs(23)
    assert len(grids) == 4
    assert len({proto.json_sha256(grid) for grid in grids}) == 4
    for grid in grids:
        assert generator.self_check(grid) == []
        _coerced, features, errors = generator._scene_analysis(grid)
        assert errors == []
        assert features["color_count"] >= 2


def test_real_racket_outputs_match_both_python_rules_and_disagree():
    proto = load_prototype()
    generator, _path, _digest = proto.load_generator()
    grids = proto.fixture_inputs(31)[:2]
    exact = proto.racket_outputs(grids, tile_color_mode="exact")
    selector = proto.racket_outputs(grids, tile_color_mode="selector")
    assert exact == [generator.rule_mirror(grid) for grid in grids]
    assert selector == [generator._selector_colored_tiles(grid) for grid in grids]
    assert all(left != right for left, right in zip(exact, selector))


@pytest.mark.parametrize("seed,setting", [(0, "exact"), (1, "selector")])
def test_complete_episode_is_identifiable_before_query(seed, setting):
    proto = load_prototype()
    episode = proto.make_episode(seed)
    assert episode["parameters"] == {"tile_color_mode": setting}
    assert episode["parameter_draw_count"] == 1
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert episode["rival"]["refuting_demonstration_indices"]
    assert episode["rival"]["query_differs"] is True
    public = proto.public_episode(episode)
    serialized = json.dumps(public, sort_keys=True)
    assert "tile_color_mode" not in serialized
    assert "program" not in serialized
    assert "rival" not in serialized
    assert "seed" not in serialized
    assert "output" not in public["test"][0]
    assert all("output" in pair for pair in public["train"])


def test_evidence_bundle_is_self_hashing_and_contains_both_settings(tmp_path):
    proto = load_prototype()
    report = proto.build_evidence(0, tmp_path)
    assert report["status"] == "verified_prototype"
    assert set(report["settings_verified"]) == {"exact", "selector"}
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["files"]
    for row in manifest["files"]:
        path = tmp_path / row["path"]
        assert path.is_file()
        assert proto.sha256_bytes(path.read_bytes()) == row["sha256"]
