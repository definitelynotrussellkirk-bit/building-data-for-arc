"""Focused contract tests for the proposed episode-level match-mode family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators/860cbb625ca0/workspace/parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"
CONTRACT_PATH = HOME / "promotion.json"
PROBE_PATH = HOME / "adversarial_probe.py"
GENERATOR_PATH = ROOT / "generators/860cbb625ca0/generator.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_task_local_parametric_artifacts_are_present():
    assert PROTOTYPE_PATH.is_file(), "the task-local prototype must exist"
    assert ADAPTER_PATH.is_file(), "the task-local promotion adapter must exist"
    assert CONTRACT_PATH.is_file(), "the task-local promotion contract must exist"
    assert PROBE_PATH.is_file(), "the bounded adversarial probe must exist"


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_860cbb625ca0", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    sys.path.insert(0, str(HOME))
    try:
        return _load("parametric_860cbb625ca0_adapter", ADAPTER_PATH)
    finally:
        sys.path.remove(str(HOME))


@pytest.fixture(scope="module")
def probe():
    sys.path.insert(0, str(HOME))
    try:
        return _load("parametric_860cbb625ca0_probe", PROBE_PATH)
    finally:
        sys.path.remove(str(HOME))


@pytest.fixture(scope="module")
def racket_bridge(prototype):
    with prototype.RacketBridge() as bridge:
        yield bridge


@pytest.fixture(scope="module")
def base_generator():
    return _load("generator_860cbb625ca0", GENERATOR_PATH)


def _witness(prototype):
    template = [[1, 2, 3], [4, 5, 6]]
    board = [[0 for _ in range(10)] for _ in range(7)]
    prototype.paste_grid(board, template, 0, 0)
    prototype.paste_grid(board, prototype.rotate_cw(template), 2, 4)
    prototype.paste_grid(board, prototype.flip_lr(template), 5, 7)
    return prototype.compose_input(template, board)


def test_programs_preserve_exact_canonical_default_and_guard_the_patch(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "4754a7505a361039de000d52fb1eb78ba6c2ffa84dc298adc55d5311493745cb"
    )
    assert prototype.program_for("exact", root=ROOT) == canonical

    rotations = prototype.program_for("rotations", root=ROOT)
    dihedral = prototype.program_for("dihedral", root=ROOT)
    assert rotations != canonical and dihedral != canonical and rotations != dihedral
    assert "(matches (find-matches board template 1))" in rotations
    assert "(matches (find-matches board template 2))" in dihedral
    assert rotations.count("(matches (find-matches board template 1))") == 1
    assert dihedral.count("(matches (find-matches board template 2))") == 1

    for value in ("rotation", "", 0, None, True):
        with pytest.raises(ValueError, match="match_mode"):
            prototype.program_for(value, root=ROOT)


def test_real_racket_and_independent_mirror_distinguish_all_modes(
    prototype, racket_bridge
):
    grid = _witness(prototype)
    expected = {
        "exact": [[1, 0, 0, 0, 0, 0, 0]],
        "rotations": [[1, 0, 1, 0, 0, 0, 0]],
        "dihedral": [[1, 0, 1, 0, 0, 1, 0]],
    }
    before = copy.deepcopy(grid)
    for mode in prototype.ALLOWED_MODES:
        actual = prototype.execute_rule(
            prototype.program_for(mode, root=ROOT), grid, bridge=racket_bridge
        )
        assert actual == expected[mode]
        assert prototype.python_mirror(grid, match_mode=mode) == expected[mode]
    assert grid == before


def test_episode_is_fixed_per_mode_and_has_four_distinct_queries(
    prototype, racket_bridge
):
    episodes = {
        mode: prototype.make_episode(
            17,
            match_mode=mode,
            demos=3,
            queries=4,
            root=ROOT,
            bridge=racket_bridge,
        )
        for mode in prototype.ALLOWED_MODES
    }
    replay = prototype.make_episode(
        17,
        match_mode="exact",
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    assert episodes["exact"] == replay

    reference_inputs = [
        pair["input"]
        for pair in episodes["exact"]["train"] + episodes["exact"]["test"]
    ]
    for mode, episode in episodes.items():
        assert episode["parameters"] == {"match_mode": mode}
        assert episode["selection_scope"] == "once_per_episode"
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert [
            pair["input"] for pair in episode["train"] + episode["test"]
        ] == reference_inputs
        assert len({prototype.grid_sha256(pair["input"]) for pair in episode["test"]}) == 4
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == prototype.python_mirror(
                pair["input"], match_mode=mode
            )
        assert len(episode["parameter_rivals"]) == 2
        assert all(
            rival["status"] == "refuted_by_demonstrations"
            and rival["demonstration_mismatch_indices"]
            for rival in episode["parameter_rivals"]
        )
        assert episode["ambiguities"] == []


def test_demo_bounds_are_2_through_6_and_queries_are_exactly_four(
    prototype, adapter
):
    for demos in (2, 6):
        claims = adapter.generate(
            29, {"match_mode": "rotations"}, demos=demos, queries=4
        )
        assert len(claims["train"]) == demos
        assert len(claims["test"]) == 4
    for demos in (1, 7, True):
        with pytest.raises(ValueError, match="demos"):
            adapter.generate(29, {"match_mode": "exact"}, demos=demos, queries=4)
    for queries in (0, 3, 5, True):
        with pytest.raises(ValueError, match="queries"):
            adapter.generate(29, {"match_mode": "exact"}, demos=3, queries=queries)


def test_last_query_is_a_substantive_30_by_30_stress_case(prototype, racket_bridge):
    episode = prototype.make_episode(
        31,
        match_mode="dihedral",
        demos=2,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    grid = episode["test"][-1]["input"]
    assert len(grid) == 30 and len(grid[0]) == 30
    template, board = prototype.split_input(grid)
    assert len(template) >= 2 and len(template[0]) >= 2
    occupied = [
        (r, c)
        for r, row in enumerate(board)
        for c, value in enumerate(row)
        if value != 0
    ]
    assert len(occupied) >= 50
    rows = [r for r, _ in occupied]
    cols = [c for _, c in occupied]
    assert min(rows) == 0 and max(rows) == len(board) - 1
    assert min(cols) == 0 and max(cols) == len(board[0]) - 1
    assert len({r for r, _ in occupied}) >= 12
    assert len({c for _, c in occupied}) >= 12


def test_public_and_first_turn_projections_hide_private_and_future_data(
    prototype, racket_bridge
):
    episode = prototype.make_episode(
        41,
        match_mode="rotations",
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    public_id = prototype.public_id(episode)
    private_change = copy.deepcopy(episode)
    private_change["program"] = "private replacement"
    private_change["parameters"]["match_mode"] = "dihedral"
    private_change["test"][0]["output"][0][0] ^= 1
    assert prototype.public_id(private_change) == public_id

    first = prototype.first_turn_bytes(episode)
    first_public = json.loads(first)
    assert len(first_public["train"]) == 3
    assert len(first_public["test"]) == 1
    future_change = copy.deepcopy(episode)
    future_change["test"][1]["input"][0][0] ^= 1
    future_change["test"][3]["output"][0][0] ^= 1
    future_change["program"] = "different private program"
    assert prototype.first_turn_bytes(future_change) == first

    visible_change = copy.deepcopy(episode)
    visible_change["test"][0]["input"][0][0] ^= 1
    assert prototype.first_turn_bytes(visible_change) != first


def test_promotion_contract_and_adapter_are_strict_and_racket_free(
    prototype, adapter, monkeypatch
):
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/860cbb625ca0/workspace/parametric/adapter.py",
        "parameters": {"match_mode": ["exact", "rotations", "dihedral"]},
        "default": {"match_mode": "exact"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    assert adapter.program({"match_mode": "exact"}) == prototype.canonical_source(
        root=ROOT
    )
    assert adapter.program({"match_mode": "dihedral"}) == prototype.program_for(
        "dihedral", root=ROOT
    )
    for settings in ({}, {"match_mode": "bad"}, {"extra": "exact"}):
        with pytest.raises(ValueError):
            adapter.program(settings)

    monkeypatch.setattr(
        adapter.prototype,
        "RacketBridge",
        lambda: pytest.fail("adapter must leave protected Racket replay to worker"),
    )
    # Native promotion workers pass demo/query counts positionally.
    claims = adapter.generate(53, {"match_mode": "dihedral"}, 3, 4)
    assert set(claims) == {"train", "test", "program_solution"}
    assert len(claims["train"]) == 3 and len(claims["test"]) == 4
    assert claims["program_solution"] == prototype.program_for("dihedral", root=ROOT)


def test_evidence_writer_replays_all_modes_and_binds_public_files(
    prototype, racket_bridge, monkeypatch, tmp_path
):
    out = tmp_path / "match-mode-evidence"
    monkeypatch.setattr(
        prototype,
        "RacketBridge",
        lambda: pytest.fail("write_evidence ignored its supplied bridge"),
    )
    report = prototype.write_evidence(
        seed=59,
        out=out,
        root=ROOT,
        demos=3,
        queries=4,
        bridge=racket_bridge,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["approved"] is False
    assert report["parameter"] == {
        "name": "match_mode",
        "allowed_values": ["exact", "rotations", "dihedral"],
        "original_default": "exact",
        "selection_scope": "once_per_episode",
        "input_constraints_depend_on_parameter": False,
    }
    assert report["counts"]["episodes"] == 3
    assert report["counts"]["train_pairs"] == 9
    assert report["counts"]["query_pairs"] == 12
    assert report["counts"]["distinct_input_grids"] == 7
    assert report["counts"]["canonical_pairs_checked"] >= 3
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["shortcut_rivals_checked"] == 11
    assert report["counts"]["shortcut_rivals_refuted"] == 11
    assert report["counts"]["semantic_placements"] >= 20
    assert report["counts"]["near_misses"] >= 7
    assert all(row["shortcut_rivals_survived"] == 0 for row in report["episodes"])

    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["schema"] == "arcpuzzles-parametric-evidence-manifest-v1"
    for row in manifest["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        rule_path = out / row["racket_path"]
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", public_path.name)
        private = json.loads(private_path.read_text())
        public = json.loads(public_path.read_text())
        assert public == prototype.public_challenge(private)
        assert public_path.name == f"challenge-{prototype.public_id(private)}.json"
        assert hashlib.sha256(rule_path.read_bytes()).hexdigest() == private["program_sha256"]
        assert len(private["train"]) == 3 and len(private["test"]) == 4
        assert all("output" not in pair for pair in public["test"])

    with pytest.raises(FileExistsError):
        prototype.write_evidence(
            seed=59,
            out=out,
            root=ROOT,
            demos=3,
            queries=4,
            bridge=racket_bridge,
        )


def test_duplicate_public_ids_abort_before_public_writes(
    prototype, racket_bridge, monkeypatch, tmp_path
):
    out = tmp_path / "duplicate-public"
    public_writes = []
    real_write = Path.write_bytes
    monkeypatch.setattr(prototype, "public_id", lambda episode: "0" * 64)

    def recording_write(path, data):
        if path.parent.name == "public":
            public_writes.append(path.name)
        return real_write(path, data)

    monkeypatch.setattr(Path, "write_bytes", recording_write)
    with pytest.raises(ValueError, match="duplicate public challenge id"):
        prototype.write_evidence(
            seed=61,
            out=out,
            root=ROOT,
            demos=2,
            queries=4,
            bridge=racket_bridge,
        )
    assert public_writes == []
    assert not out.exists()


def test_bounded_adversarial_probe_covers_modes_counts_and_boundaries(
    probe, racket_bridge
):
    report = probe.run_probe(
        seeds=[0, 1], demo_counts=[2, 6], bridge=racket_bridge
    )
    assert report["status"] == "pass"
    assert report["modes"] == ["exact", "rotations", "dihedral"]
    assert report["demo_counts"] == [2, 6]
    assert report["episodes_checked"] == 12
    assert report["queries_per_episode"] == 4
    assert report["max_input_shape"] == [30, 30]



def _nonzero_rows(output):
    return tuple(index for index, value in enumerate(output[0]) if value)


def test_base_generator_consumes_declared_geometry_semantic_and_palette_axes(
    base_generator, prototype
):
    grid = base_generator.generate(
        101,
        0,
        grid_h=12,
        grid_w=24,
        n_match_rows=4,
        palette_kind="cool",
        n_distinct_colors=2,
        position_bias="bottom",
        density="dense",
    )
    assert [len(grid), len(grid[0])] == [12, 24]
    assert base_generator.self_check(grid) == []
    template, board = prototype.split_input(grid)
    assert len(template) == 3 and len(template[0]) == 3
    output = prototype.python_mirror(grid, match_mode="exact")
    assert len(_nonzero_rows(output)) == 4
    assert min(output[0][row] for row in _nonzero_rows(output)) >= 2
    used = {cell for row in grid for cell in row}
    assert 9 in used and 0 in used
    assert len(used - {0, 9}) == 2

    one_color = base_generator.generate(
        101,
        0,
        grid_h=12,
        grid_w=24,
        n_match_rows=4,
        palette_kind="cool",
        n_distinct_colors=1,
        position_bias="bottom",
        density="dense",
    )
    assert len({cell for row in one_color for cell in row} - {0, 9}) == 1
    assert one_color != grid

    top = base_generator.generate(
        101,
        0,
        grid_h=12,
        grid_w=24,
        n_match_rows=3,
        palette_kind="default",
        n_distinct_colors=1,
        position_bias="top",
        density="sparse",
    )
    bottom = base_generator.generate(
        101,
        0,
        grid_h=12,
        grid_w=24,
        n_match_rows=3,
        palette_kind="default",
        n_distinct_colors=1,
        position_bias="bottom",
        density="sparse",
    )
    assert _nonzero_rows(prototype.python_mirror(top, match_mode="exact")) != _nonzero_rows(
        prototype.python_mirror(bottom, match_mode="exact")
    )

    for bad in (True, 12.0, "12"):
        with pytest.raises((TypeError, ValueError)):
            base_generator.generate(101, 0, grid_h=bad)


def test_sampler_breaks_the_retained_fixed_row_shortcut(prototype):
    exact_profiles = set()
    exact_rows = set()
    exact_counts = set()
    semantic_anchor_rows = {"exact": set(), "rotation_only": set(), "reflection_only": set()}
    for seed in range(12):
        for sample in prototype._sample_inputs(seed, 7, "medium"):
            output = prototype.python_mirror(sample["grid"], match_mode="exact")
            profile = tuple(output[0])
            exact_profiles.add(profile)
            exact_rows.update(_nonzero_rows(output))
            exact_counts.update(value for value in output[0] if value)
            old = prototype.fixed_row_shortcut(sample["grid"], match_mode="exact")
            assert old != output
            for placement in sample["semantic_placements"]:
                semantic_anchor_rows[placement["category"]].add(placement["row"])
    assert len(exact_profiles) >= 12
    assert exact_rows - {0}
    assert any(value >= 2 for value in exact_counts)
    assert all(len(rows) >= 6 for rows in semantic_anchor_rows.values())


def test_two_demo_lessons_refute_color_mask_wildcard_and_partial_intermediate_rivals(
    prototype, racket_bridge
):
    for seed in range(4):
        family = prototype.make_episode_family(
            seed,
            demos=2,
            queries=4,
            difficulty="medium",
            root=ROOT,
            bridge=racket_bridge,
        )
        for mode, episode in family.items():
            diagnostics = prototype.rival_diagnostics(episode)
            assert diagnostics
            assert all(row["demonstration_mismatch_indices"] for row in diagnostics), (
                seed,
                mode,
                diagnostics,
            )
            names = {row["name"] for row in diagnostics}
            assert {"fixed_row", "mask_only", "zero_is_background"} <= names
            if mode != "exact":
                assert "partial_intermediate" in names


def test_crossed_controls_vary_intermediate_at_fixed_shape_and_preserve_palette_invariance(
    prototype, racket_bridge
):
    left = prototype._build_input(3, 2, 7, "medium")
    right = prototype._build_input(19, 2, 7, "medium")
    assert left["shape"] == right["shape"]
    assert left["row_histograms"] != right["row_histograms"]
    assert left["semantic_placements"] != right["semantic_placements"]

    recolored = prototype.recolor_input(left["grid"], salt=97)
    assert recolored != left["grid"]
    assert [len(recolored), len(recolored[0])] == left["shape"]
    for mode in prototype.ALLOWED_MODES:
        expected = prototype.python_mirror(left["grid"], match_mode=mode)
        assert prototype.python_mirror(recolored, match_mode=mode) == expected
        assert prototype.execute_rule(
            prototype.program_for(mode, root=ROOT), recolored, bridge=racket_bridge
        ) == expected


def test_grid_validation_rejects_boolean_float_and_ragged_numeric_payloads(prototype):
    valid = [[[1, 2], [3, 4]], [[0, 0], [0, 0]]]
    prototype.compose_input(*valid)
    for bad in (
        [[True, 2], [3, 4]],
        [[1.0, 2], [3, 4]],
        [[1, 2], [3]],
        [[1, 10], [3, 4]],
    ):
        with pytest.raises(ValueError):
            prototype.compose_input(bad, valid[1])


def test_episode_persists_intermediate_and_shortcut_evidence(prototype, racket_bridge):
    family = prototype.make_episode_family(
        7,
        demos=2,
        queries=4,
        difficulty="medium",
        root=ROOT,
        bridge=racket_bridge,
    )
    for mode, episode in family.items():
        assert episode["shortcut_rivals"] == prototype.rival_diagnostics(episode)
        assert all(
            row["status"] == "refuted_by_demonstrations"
            for row in episode["shortcut_rivals"]
        )
        assert len(episode["sampling"]) == 6
        for sample in episode["sampling"]:
            assert {
                "input_sha256",
                "sample_index",
                "shape",
                "stamp_anchors",
                "semantic_placements",
                "near_misses",
                "row_histograms",
                "match_records",
            } <= set(sample)
            assert set(sample["row_histograms"]) == set(prototype.ALLOWED_MODES)
            assert set(sample["match_records"]) == set(prototype.ALLOWED_MODES)


def test_base_generator_rejects_unobservable_scattered_single_row_at_min_height(
    base_generator,
):
    with pytest.raises(ValueError, match="scattered"):
        base_generator.generate(
            11,
            0,
            grid_h=6,
            grid_w=16,
            n_match_rows=1,
            palette_kind="default",
            n_distinct_colors=1,
            position_bias="scattered",
            density="sparse",
        )


def test_adversarial_probe_reports_shortcuts_crossed_controls_and_base_surface(
    probe, racket_bridge
):
    report = probe.run_probe(
        seeds=[0, 1], demo_counts=[2, 6], bridge=racket_bridge
    )
    assert report["pairs_checked"] == 96
    assert report["parameter_rivals_checked"] == 24
    assert report["shortcut_rivals_checked"] == 44
    assert report["shortcut_rivals_refuted"] == 44
    assert report["minimum_lesson_episodes"] == 6
    assert report["palette_invariance_checks"] == 6
    assert report["crossed_control_checks"] == 2
    assert report["stress_cases_checked"] == 12
    assert report["base_generator_cases"] >= 100
    assert report["base_generator_rejections"] >= 4
