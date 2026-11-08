from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
TASK_ID = "12b35b7402b6"
HOME = ROOT / f"generators/{TASK_ID}/workspace/parametric"
PROTOTYPE = HOME / "prototype.py"
ADAPTER = HOME / "adapter.py"
PROMOTION = HOME / "promotion.json"
PROBE = HOME / "adversarial_probe.py"
SWEEP = HOME / "semantic_sweep.py"


def _load(name: str, path: Path):
    assert path.is_file(), path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


@pytest.fixture(scope="module")
def p():
    return _load("parametric_12b35b7402b6", PROTOTYPE)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_12b35b7402b6_adapter", ADAPTER)


def test_required_artifacts_and_exact_canonical_default(p):
    for path in (PROTOTYPE, ADAPTER, PROMOTION, PROBE, SWEEP, HOME / "canonical.rkt", HOME / "linked_payload.rkt", HOME / "skip_stage_a.rkt"):
        assert path.is_file(), path
    canonical = _canonical_program()
    assert p.program({"mode": "canonical"}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == p.CANONICAL_SHA256
    alt = p.program({"mode": "linked_payload"})
    assert alt != canonical
    assert "stage-a" in alt.lower() or "stage_a" in alt.lower()


def test_strict_settings_counts_and_grid_validation(p, adapter):
    for bad in ({}, {"mode": "bad"}, {"mode": True}, {"mode": "canonical", "extra": 1}):
        with pytest.raises(ValueError):
            p.program(bad)
    for kwargs in (
        {"seed": True, "settings": p.DEFAULT, "demos": 3, "queries": 4},
        {"seed": 1, "settings": p.DEFAULT, "demos": 1, "queries": 4},
        {"seed": 1, "settings": p.DEFAULT, "demos": 7, "queries": 4},
        {"seed": 1, "settings": p.DEFAULT, "demos": 3, "queries": 3},
        {"seed": 1, "settings": p.DEFAULT, "demos": 3, "queries": 5},
    ):
        with pytest.raises(ValueError):
            adapter.generate(**kwargs)
    for grid in ([], [[]], [[True]], [[0], [0, 1]], [[10]], [[0, 1], [0, 2]]):
        with pytest.raises(ValueError):
            p.transform(grid, p.DEFAULT)


def test_scene_has_real_stage_dependency_and_decoys(p):
    scene = p.build_scene(17, 0, 16, 20, profile="demo_a")
    grid = scene["grid"]
    facts = p.scene_facts(grid)
    assert facts["marker_count"] == scene["marker_count"]
    assert facts["marker_span"] > facts["marker_count"]
    assert facts["unique_blue_match"]
    assert facts["pre_stage_largest_red_size"] == scene["skip_key_size"]
    assert facts["post_stage_largest_red_size"] == scene["true_key_size"]
    assert scene["true_key_size"] != scene["skip_key_size"]
    assert facts["azure_sizes"].count(scene["true_key_size"]) == 1
    assert facts["azure_sizes"].count(scene["skip_key_size"]) == 1
    assert scene["true_key_size"] + scene["diagonal_satellite_size"] in facts["azure_sizes"]

    canonical = p.transform(grid, {"mode": "canonical"})
    linked = p.transform(grid, {"mode": "linked_payload"})
    skipped = p.skip_stage_a_transform(grid)
    assert canonical != linked
    assert skipped != linked
    assert p.stage_a_grid(grid) == canonical
    assert p.changed_cells(grid, linked, old=1, new=2) == scene["marker_count"]
    assert p.changed_cells(canonical, linked, old=8, new=4) == scene["true_key_size"]


def test_generation_is_deterministic_setting_neutral_and_two_demo_identifiable(p):
    random.seed(4001)
    state = random.getstate()
    canonical = p.generate(101, {"mode": "canonical"}, demos=2, queries=4)
    assert random.getstate() == state
    assert canonical == p.generate(101, {"mode": "canonical"}, demos=2, queries=4)
    linked = p.generate(101, {"mode": "linked_payload"}, demos=2, queries=4)
    assert [pair["input"] for pair in canonical["train"] + canonical["test"]] == [
        pair["input"] for pair in linked["train"] + linked["test"]
    ]
    assert canonical["certificate"]["survivors"] == [{"mode": "canonical"}]
    assert linked["certificate"]["survivors"] == [{"mode": "linked_payload"}]
    assert all(linked["certificate"]["shortcut_refutations"].values())
    assert len({p.grid_sha256(pair["input"]) for pair in linked["train"] + linked["test"]}) == 6

    maximum = p.generate(101, {"mode": "linked_payload"}, demos=6, queries=4)
    assert len(maximum["train"]) == 6 and len(maximum["test"]) == 4


def test_fourth_query_is_substantive_30x30_cross_quadrant_stress(p):
    episode = p.generate(303, {"mode": "linked_payload"}, demos=2, queries=4)
    grid = episode["test"][-1]["input"]
    assert len(grid) == 30 and len(grid[0]) == 30
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 120
    assert {int(r >= 15) * 2 + int(c >= 15) for r, c in nonzero} == {0, 1, 2, 3}
    assert min(r for r, _ in nonzero) == 0
    assert max(r for r, _ in nonzero) >= 27
    assert min(c for _, c in nonzero) == 0
    assert max(c for _, c in nonzero) >= 27


def test_racket_replays_both_rules_and_skip_a_witness(p):
    scene = p.build_scene(44, 1, 18, 22, profile="demo_b")
    grid = scene["grid"]
    with p.RacketRunner() as execute:
        for settings in p.SETTINGS:
            assert execute(p.program(settings), grid) == p.transform(grid, settings)
        skipped = execute(p.skip_stage_a_program(), grid)
        linked = execute(p.program({"mode": "linked_payload"}), grid)
        assert skipped == p.skip_stage_a_transform(grid)
        assert skipped != linked


def test_public_projection_and_first_turn_hide_private_and_future_data(p):
    episode = p.generate(77, {"mode": "linked_payload"}, demos=3, queries=4)
    body = public_challenge_bytes(episode)
    visible = json.loads(body)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert len(visible["test"]) == 4

    public_id = public_challenge_id(episode)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"mode": "canonical"}
    changed["program_solution"] = "private replacement"
    changed["test"][0]["output"][0][0] ^= 1
    assert public_challenge_id(changed) == public_id

    first = p.public_turn_bytes(episode, 0)
    first_visible = json.loads(first)
    assert len(first_visible["test"]) == 1
    future = copy.deepcopy(episode)
    future["test"][2]["input"][2][2] ^= 1
    future["test"][3]["output"][3][3] ^= 1
    future["program_solution"] = "changed"
    assert p.public_turn_bytes(future, 0) == first
    now = copy.deepcopy(episode)
    now["test"][0]["input"][2][2] ^= 1
    assert p.public_turn_bytes(now, 0) != first


def test_promotion_contract_and_adapter_are_strict(p, adapter, monkeypatch):
    contract = json.loads(PROMOTION.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/12b35b7402b6/workspace/parametric/adapter.py",
        "parameters": {"mode": ["canonical", "linked_payload"]},
        "default": {"mode": "canonical"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            "generators/12b35b7402b6/workspace/parametric/prototype.py",
            "generators/12b35b7402b6/workspace/parametric/canonical.rkt",
            "generators/12b35b7402b6/workspace/parametric/linked_payload.rkt",
            "generators/12b35b7402b6/workspace/parametric/skip_stage_a.rkt",
        ],
    }
    assert adapter.program({"mode": "canonical"}) == _canonical_program()
    monkeypatch.setattr(p, "RacketRunner", lambda: pytest.fail("adapter generation must be Racket-free"))
    claims = adapter.generate(9, {"mode": "linked_payload"}, 2, 4)
    assert set(claims) == {"train", "test", "program_solution"}


def test_bounded_semantic_sweep_finds_no_surviving_shortcut(p):
    sweep = _load("semantic_sweep_12b", SWEEP)
    result = sweep.run(range(12), demos=2)
    assert result["episodes"] == 24
    assert result["ambiguous_episodes"] == 0
    assert result["surviving_rivals"] == {}
    assert result["crossed_controls"]["marker_spans"] >= 3
    assert result["crossed_controls"]["true_payload_ranks"] >= 3


def test_protected_racket_rival_bank_is_total(p):
    probe = _load("adversarial_probe_12b_totality", PROBE)
    banks = probe.racket_rivals()
    with p.RacketRunner() as execute:
        for mode, bank in banks.items():
            episode = p.generate(0, {"mode": mode}, demos=2, queries=4)
            for name, source in bank.items():
                output = execute(source, episode["train"][0]["input"])
                assert len(output) == len(episode["train"][0]["input"]), name
                assert len(output[0]) == len(episode["train"][0]["input"][0]), name


def test_minimum_lesson_crosses_skip_and_connectivity_deltas(p):
    first = p.build_scene(23, 0, 15, 20, profile="demo_a")
    second = p.build_scene(23, 1, 16, 21, profile="demo_b")
    assert {
        first["true_key_size"] - first["skip_key_size"],
        second["true_key_size"] - second["skip_key_size"],
    } == {1, 2}
    assert {
        first["diagonal_satellite_size"],
        second["diagonal_satellite_size"],
    } == {0, 1}


def test_stage_a_bridges_multiple_red_components_not_one_anchor_arithmetic(p):
    for profile, index, shape in (("demo_a", 0, (15, 20)), ("demo_b", 1, (16, 21))):
        scene = p.build_scene(31, index, *shape, profile=profile)
        grid = scene["grid"]
        target = set(p._unique_component_by_size(grid, 1, scene["marker_count"]))
        touching = []
        for comp in p.components(grid, 2):
            if any(
                (r + dr, c + dc) in target
                for r, c in comp
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                touching.append(comp)
        assert len(touching) >= 2
        assert scene["marker_count"] + max(map(len, touching)) != scene["true_key_size"]


def test_seed12_minimum_lesson_refutes_target_bbox_area_shortcut(p):
    episode = p.generate(12, {"mode": "linked_payload"}, demos=2, queries=4)
    assert episode["certificate"]["shortcut_refutations"]["target_bbox_area"] is True


def test_seed4_minimum_lesson_refutes_farthest_from_markers_shortcut(p):
    episode = p.generate(4, {"mode": "linked_payload"}, demos=2, queries=4)

    def center2(cells):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return min(rows) + max(rows), min(cols) + max(cols)

    rivals = []
    for pair in episode["train"]:
        grid = pair["input"]
        stage = p.stage_a_grid(grid)
        marker_center = center2(p._marker_cells(grid))
        azure = p.components(stage, 8)
        target = max(
            azure,
            key=lambda cells: (
                (center2(cells)[0] - marker_center[0]) ** 2
                + (center2(cells)[1] - marker_center[1]) ** 2,
                cells[0],
            ),
        )
        rivals.append(p._paint(stage, target, 4))
    assert any(rival != pair["output"] for rival, pair in zip(rivals, episode["train"]))


def test_certificate_rejects_forged_program_labels_duplicates_and_pair_shape(p):
    episode = p.generate(88, {"mode": "linked_payload"}, demos=2, queries=4)

    forged_program = copy.deepcopy(episode)
    forged_program["program_solution"] = p.program({"mode": "canonical"})
    with pytest.raises(ValueError, match="program"):
        p.certify(forged_program)

    forged_label = copy.deepcopy(episode)
    forged_label["train"][0]["output"][0][0] = (
        forged_label["train"][0]["output"][0][0] + 1
    ) % 10
    with pytest.raises(ValueError, match="label"):
        p.certify(forged_label)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    with pytest.raises(ValueError, match="distinct"):
        p.certify(duplicate)

    extra_field = copy.deepcopy(episode)
    extra_field["train"][0]["private"] = True
    with pytest.raises(ValueError, match="exactly input and output"):
        p.certify(extra_field)
