"""Portable regressions for the color-keyed stencil-library generator."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (canonical_pairs, center_col_anchor_output,
                             center_row_anchor_output, exhaustive_axis_probe,
                             geometry_output, has_off_center_anchor,
                             isolated_anchor_witness, load_generator, observed,
                             panel_center_output, parse, racket_outputs)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {"grid_h", "grid_w", "lib_h", "n_entries", "stencil_size", "n_body"}


def test_contract_is_small_exact_and_rule_bound():
    assert gen.RULE_HASH == "66637f26ea98"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    expected_rivals = {"panel_center_anchor", "center_row_anchor", "center_col_anchor"}
    assert set(gen.SEMANTIC_RIVALS) == expected_rivals
    assert set(gen.CANONICAL_SHORTCUTS) == expected_rivals
    assert set(gen.LESSON_COMPETITORS) == expected_rivals


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_canonical_pairs_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]


def test_panel_center_shortcut_fits_every_labeled_canonical_pair():
    assert all(panel_center_output(pair["input"]) == pair["output"] for pair in canonical_pairs())
    assert all(center_row_anchor_output(pair["input"]) == pair["output"] for pair in canonical_pairs())
    assert all(center_col_anchor_output(pair["input"]) == pair["output"] for pair in canonical_pairs())


def test_distribution_teaches_both_anchor_coordinates_and_broad_stencils():
    saw_nonlocal_stencil = False
    for index in range(96):
        grid = gen.generate(53000 + index, index * 23 + 5)
        parsed = parse(grid)
        for entry in parsed["entries"]:
            c1, c2 = entry["span"]
            center = (parsed["separator"] // 2, (c1 + c2) // 2)
            assert entry["anchor"][0] != center[0]
            assert entry["anchor"][1] != center[1]
            saw_nonlocal_stencil |= any(max(abs(dr), abs(dc)) > 1
                                        for dr, dc in entry["offsets"])
        intended = geometry_output(grid)
        assert intended != panel_center_output(grid)
        assert intended != center_row_anchor_output(grid)
        assert intended != center_col_anchor_output(grid)
    assert saw_nonlocal_stencil


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("options", [
    dict(grid_h=10, grid_w=13, lib_h=3, n_entries=2, stencil_size=1, n_body=4),
    dict(grid_h=16, grid_w=21, lib_h=6, n_entries=4, stencil_size=5, n_body=8),
])
def test_every_exact_override_is_honored_in_every_band(band, options):
    grid = gen.generate(73, 11, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("grid_h", 9), ("grid_h", 17), ("grid_w", 12), ("grid_w", 22),
    ("lib_h", 2), ("lib_h", 7), ("n_entries", 1), ("n_entries", 5),
    ("stencil_size", 0), ("stencil_size", 6), ("n_body", 3), ("n_body", 9),
    ("grid_h", True), ("grid_w", 13.0), ("lib_h", "5"),
    ("n_entries", False), ("stencil_size", 2.0), ("n_body", "4"),
])
def test_rejects_invalid_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("sample_index", [-1, True, False, 1.0, "1"])
def test_rejects_invalid_sample_index(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, sample_index)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_deterministic_and_teaches_anchor_use(difficulty):
    canonical_profile_hits = 0
    shapes = set()
    inputs = set()
    for index in range(96):
        grid = gen.generate(3000 + index, index * 13 + 7, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(3000 + index, index * 13 + 7, difficulty=difficulty)
        assert has_off_center_anchor(grid)
        assert isolated_anchor_witness(grid)
        intended = geometry_output(grid)
        assert intended != panel_center_output(grid)
        assert intended != center_row_anchor_output(grid)
        assert intended != center_col_anchor_output(grid)
        assert gen.SEMANTIC_WITNESSES["biaxial_off_center_anchors"](grid)
        assert gen.SEMANTIC_RIVALS["panel_center_anchor"](grid) == panel_center_output(grid)
        assert gen.SEMANTIC_RIVALS["center_row_anchor"](grid) == center_row_anchor_output(grid)
        assert gen.SEMANTIC_RIVALS["center_col_anchor"](grid) == center_col_anchor_output(grid)
        stats = observed(grid)
        canonical_profile_hits += (stats["grid_h"] in (12, 13)
                                   and stats["grid_w"] == 17
                                   and stats["n_entries"] == 3)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        inputs.add(tuple(tuple(row) for row in grid))
    assert canonical_profile_hits >= 20
    assert len(shapes) >= 4
    assert len(inputs) == 96


def test_joint_axis_probe_covers_all_endpoint_combinations():
    endpoint_values = {
        "grid_h": (10, 16), "grid_w": (13, 21), "lib_h": (3, 6),
        "n_entries": (2, 4), "stencil_size": (1, 5), "n_body": (4, 8),
    }
    report = exhaustive_axis_probe(gen, value_sets=endpoint_values, bands=(None,))
    assert report["cases"] == 64
    assert report["failures"] == []
    assert report["isolated_witnesses"] == 64


def test_deliberate_anchor_witness_is_isolated_from_other_stamps():
    # Regression seed: the earlier distance heuristic let a second seed touch
    # one cell of the designated witness's intended-vs-rival disagreement.
    grid = gen.generate(120254, 4833)
    assert isolated_anchor_witness(grid)


def test_generated_panels_use_unique_colors_and_all_are_exercised_in_body():
    for index in range(64):
        grid = gen.generate(8800, index)
        parsed = parse(grid)
        colors = [entry["color"] for entry in parsed["entries"]]
        body_colors = {color for _, _, color in parsed["body"]}
        assert len(colors) == len(set(colors))
        assert set(colors) == body_colors


@pytest.mark.parametrize("mutation", ["extra_anchor", "duplicate_panel_color", "unknown_body_color", "erase_separator"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(41, 5, grid_h=13, grid_w=17, lib_h=5,
                        n_entries=3, stencil_size=3, n_body=5)
    parsed = parse(grid)
    if mutation == "extra_anchor":
        entry = parsed["entries"][0]
        c1, c2 = entry["span"]
        target = next((r, c) for r in range(parsed["separator"]) for c in range(c1, c2 + 1)
                      if grid[r][c] == 0)
        grid[target[0]][target[1]] = 9
    elif mutation == "duplicate_panel_color":
        first, second = parsed["entries"][:2]
        for r in range(parsed["separator"]):
            for c in range(second["span"][0], second["span"][1] + 1):
                if grid[r][c] == second["color"]:
                    grid[r][c] = first["color"]
    elif mutation == "unknown_body_color":
        r, c, _ = parsed["body"][0]
        unused = next(color for color in range(1, 9)
                      if color not in {entry["color"] for entry in parsed["entries"]})
        grid[r][c] = unused
    else:
        grid[parsed["separator"]][0] = parsed["entries"][0]["color"]
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 13 for _ in range(10)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_retained_panel_center_counterexample_is_source_bound_and_reproducible():
    artifact_path = HOME / "counterexamples/current-shortcut/checks/panel-center-anchor.json"
    manifest_path = HOME / "counterexamples/current-shortcut.json"
    artifact = json.loads(artifact_path.read_text())
    manifest = json.loads(manifest_path.read_text())

    source_path = Path(gen.__file__).resolve()
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert artifact["generator_sha256"] == source_hash
    assert manifest["generator_sha256"] == source_hash
    assert artifact["rule_hash"] == gen.RULE_HASH
    assert artifact["authority"]["status"] == "passed"

    witness = artifact["generated_witness"]
    regenerated = gen.generate(
        witness["seed"], witness["sample_index"],
        difficulty=witness["difficulty"], **witness["overrides"],
    )
    assert regenerated == witness["input"]
    assert gen.self_check(regenerated) == []
    assert isolated_anchor_witness(regenerated)
    assert geometry_output(regenerated) == witness["intended_output"]
    expected_rivals = {
        "panel_center_anchor": panel_center_output(regenerated),
        "center_row_anchor": center_row_anchor_output(regenerated),
        "center_col_anchor": center_col_anchor_output(regenerated),
    }
    assert witness["rival_outputs"] == expected_rivals
    assert all(witness["intended_output"] != output for output in expected_rivals.values())
    assert all(all(item["rival_matches"].values()) for item in artifact["canonical_pairs"])

    retained = manifest["files"][0]
    assert retained["path"] == "generators/fdffdd0bbde7/counterexamples/current-shortcut/checks/panel-center-anchor.json"
    assert retained["sha256"] == hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    assert retained["bytes"] == artifact_path.stat().st_size


def test_oracles_and_rivals_are_pure():
    grid = gen.generate(91, 8)
    original = deepcopy(grid)
    geometry_output(grid)
    panel_center_output(grid)
    center_row_anchor_output(grid)
    center_col_anchor_output(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = ("import json,sys;sys.path.insert(0,sys.argv[1]);"
              "from reference_probe import load_generator;"
              "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))" )
    outputs = []
    for seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")], env=env, text=True))
    assert outputs[0] == outputs[1]


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(712, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(24)]
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]
