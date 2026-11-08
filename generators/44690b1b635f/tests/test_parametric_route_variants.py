"""Focused checks for the proposed maze connectivity/phase prototype.

These tests do not modify or approve the canonical generator.  They exercise a
separate task-local episode prototype whose labels are executed by Racket.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
import re
import sys

import pytest


TASK_ID = "44690b1b635f"
TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
PROTOTYPE_PATH = TASK_ROOT / "workspace" / "parametric" / "prototype.py"
CANONICAL_SHA256 = "d78c0152b4b3f003a6ceaf2601ffb3234247354b626267c771a1bcf51d25e618"
SETTINGS = (
    {"connectivity": "cardinal", "phase": "center_even"},
    {"connectivity": "cardinal", "phase": "arm_even"},
    {"connectivity": "king", "phase": "center_even"},
    {"connectivity": "king", "phase": "arm_even"},
)


@lru_cache(maxsize=1)
def prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_route_variants_44690b1b635f", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket_bridge():
    p = prototype()
    with p.RacketBridge(max_calls_before_restart=128) as bridge:
        yield bridge


def witness_grid():
    # A cardinal corridor plus a chamber reachable only by the center's
    # southeast diagonal.  A second zero pocket remains unreachable by either
    # connectivity, so reachability and preservation are both exercised.
    return [
        [8, 8, 8, 8, 8, 8, 8],
        [8, 0, 0, 0, 8, 0, 8],
        [8, 3, 0, 2, 8, 0, 8],
        [8, 8, 8, 8, 0, 0, 8],
        [8, 0, 0, 8, 0, 3, 8],
        [8, 0, 0, 8, 8, 8, 8],
        [8, 8, 8, 8, 8, 8, 8],
    ]


def test_exact_default_rule_and_four_racket_backed_variants(racket_bridge):
    p = prototype()
    canonical = p.canonical_source(root=REPO_ROOT)
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == CANONICAL_SHA256
    assert p.materialize_rule(root=REPO_ROOT) == canonical

    programs = []
    outputs = []
    for settings in SETTINGS:
        source = p.materialize_rule(settings, root=REPO_ROOT)
        assert p.recognize_rule(source, root=REPO_ROOT) == settings
        programs.append(source)
        expected = p.independent_output(witness_grid(), settings)
        actual = p.execute_rule(
            source, witness_grid(), bridge=racket_bridge, root=REPO_ROOT
        )
        assert actual == expected
        outputs.append(actual)

    assert len(set(programs)) == 4
    assert len({p.grid_sha256(output) for output in outputs}) == 4


@pytest.mark.parametrize(
    "bad",
    [
        {"connectivity": "diagonal", "phase": "center_even"},
        {"connectivity": "cardinal", "phase": "unknown"},
        {"connectivity": "cardinal"},
        {"phase": "center_even"},
        {"connectivity": "cardinal", "phase": "center_even", "extra": "x"},
        [],
    ],
)
def test_rule_settings_are_strict(bad):
    p = prototype()
    with pytest.raises(ValueError):
        p.materialize_rule(bad, root=REPO_ROOT)


def _episode_input_hashes(p, episode):
    return [
        p.grid_sha256(pair["input"])
        for pair in list(episode["train"]) + list(episode["test"])
    ]


def test_procedural_inputs_are_deterministic_distinct_and_topology_rich():
    p = prototype()
    first = p.episode_inputs(17, demos=3, queries=4, root=REPO_ROOT)
    second = p.episode_inputs(17, demos=3, queries=4, root=REPO_ROOT)
    other = p.episode_inputs(18, demos=3, queries=4, root=REPO_ROOT)

    assert first == second
    assert len(first) == 7
    assert len({p.grid_sha256(grid) for grid in first}) == 7
    assert {p.grid_sha256(grid) for grid in first} != {
        p.grid_sha256(grid) for grid in other
    }

    shapes = set()
    wall_masks = set()
    for grid in first:
        certificate = p.input_certificate(grid)
        shapes.add((len(grid), len(grid[0])))
        wall_masks.add(certificate["wall_mask_sha256"])
        assert certificate["cardinal_reachable_zero_count"] >= 3
        assert certificate["king_only_reachable_zero_count"] >= 3
        assert certificate["unreachable_zero_count_king"] >= 3
        assert certificate["four_setting_outputs_pairwise_distinct"] is True
    assert len(wall_masks) == 7
    assert len(shapes) >= 2


def test_episode_setting_is_fixed_identified_by_demos_and_needed_by_queries(
    racket_bridge,
):
    p = prototype()
    assert [p.parameter_for_seed(seed) for seed in range(4)] == list(SETTINGS)

    selected = p.parameter_for_seed(0)
    episode = p.generate_episode(
        0, demos=3, queries=4, bridge=racket_bridge, root=REPO_ROOT
    )
    assert episode["settings"] == selected
    assert episode["demo_count"] == 3
    assert episode["query_count"] == 4
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert len(set(_episode_input_hashes(p, episode))) == 7
    assert episode["surviving_settings_from_demonstrations"] == [selected]
    assert episode["program_solution"] == p.materialize_rule(
        selected, root=REPO_ROOT
    )
    for pair in list(episode["train"]) + list(episode["test"]):
        assert pair["output"] == p.independent_output(pair["input"], selected)
    for report in episode["query_identification"]:
        assert report["selected_setting"] == selected
        assert len(report["eliminated_rivals_that_disagree"]) == 3
        assert report["query_answer_used_for_demo_fit"] is False


def test_inputs_do_not_depend_on_forced_hidden_setting(racket_bridge):
    p = prototype()
    raw = p.episode_inputs(29, demos=2, queries=4, root=REPO_ROOT)
    episode = p.generate_episode(
        29,
        settings=SETTINGS[-1],
        demos=2,
        queries=4,
        bridge=racket_bridge,
        root=REPO_ROOT,
    )
    assert [p.grid_sha256(grid) for grid in raw] == _episode_input_hashes(p, episode)
    first_setting_outputs = [p.independent_output(grid, SETTINGS[0]) for grid in raw]
    assert first_setting_outputs != [
        pair["output"] for pair in episode["train"] + episode["test"]
    ]


@pytest.mark.parametrize("bad_seed", [True, -1, 2**63, 1.5, "1"])
def test_episode_seed_validation_is_strict(bad_seed):
    p = prototype()
    with pytest.raises(ValueError):
        p.parameter_for_seed(bad_seed)


@pytest.mark.parametrize(
    ("field", "value"),
    [("demos", 0), ("demos", 9), ("demos", True), ("queries", 0), ("queries", 9), ("queries", 2.0)],
)
def test_episode_count_validation_is_strict(field, value):
    p = prototype()
    kwargs = {"demos": 3, "queries": 4, field: value}
    with pytest.raises(ValueError):
        p.episode_inputs(0, root=REPO_ROOT, **kwargs)




def test_public_identity_depends_only_on_visible_demo_and_query_inputs():
    p = prototype()
    episode = {
        "seed": 7,
        "settings": dict(SETTINGS[0]),
        "program_solution": "private",
        "train": [{"input": [[1]], "output": [[2]]}],
        "test": [{"input": [[3]], "output": [[4]]}],
    }
    public = p.public_payload(episode)
    public_id = p.public_challenge_id(public)

    private_only = copy.deepcopy(episode)
    private_only["seed"] = 999
    private_only["settings"] = dict(SETTINGS[-1])
    private_only["program_solution"] = "different-private-rule"
    private_only["test"][0]["output"] = [[9]]
    assert p.public_challenge_id(p.public_payload(private_only)) == public_id

    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"] = [[8]]
    assert p.public_challenge_id(p.public_payload(visible_change)) != public_id

    public["train"][0]["input"][0][0] = 9
    assert episode["train"][0]["input"] == [[1]]

def test_evidence_writer_hash_names_redacts_public_and_hashes_retained_files(
    racket_bridge, tmp_path,
):
    p = prototype()
    out = tmp_path / "evidence"
    manifest = p.write_evidence(
        out,
        seeds=(1, 0),
        demos=3,
        queries=4,
        bridge=racket_bridge,
        root=REPO_ROOT,
    )

    assert manifest["schema"] == "44690b1b635f-maze-connectivity-phase-evidence-v1"
    assert manifest["status"] == "proposed_unapproved"
    assert manifest["approved"] is False
    assert manifest["canonical_default_unchanged"] is True
    assert manifest["counts"] == {
        "episodes": 2,
        "train_pairs": 6,
        "query_pairs": 8,
        "distinct_input_grids": 14,
        "settings_exercised": 2,
    }
    assert {tuple(sorted(row["settings"].items())) for row in manifest["episodes"]} == {
        tuple(sorted(settings.items())) for settings in SETTINGS[:2]
    }
    assert [row["public_id"] for row in manifest["episodes"]] == sorted(
        row["public_id"] for row in manifest["episodes"]
    )

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    private_paths = sorted((out / "private" / "episodes").glob("*.json"))
    rule_paths = sorted((out / "private" / "rules").glob("*.rkt"))
    assert len(public_paths) == len(private_paths) == 2
    assert len(rule_paths) == 4

    for row in manifest["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", public_path.name)
        public_raw = public_path.read_bytes()
        public = json.loads(public_raw)
        expected_raw = (
            json.dumps(
                public,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf-8")
        public_id = hashlib.sha256(expected_raw).hexdigest()
        assert public_raw == expected_raw
        assert public_path.name == f"challenge-{public_id}.json"
        assert row["public_id"] == public_id
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        public_text = public_raw.decode("utf-8")
        for forbidden in (
            '"seed"',
            '"settings"',
            '"program_solution"',
            '"program_sha256"',
            '"query_answers"',
            "center_even",
            "arm_even",
        ):
            assert forbidden not in public_text

        private = json.loads(private_path.read_text(encoding="utf-8"))
        assert private["public_id"] == public_id
        assert len(private["query_answers"]) == 4
        assert private["query_answers"] == [pair["output"] for pair in private["test"]]
        assert isinstance(private["program_solution"], str)
        assert p.public_payload(private) == public

    for settings in SETTINGS:
        key = f"{settings['connectivity']}-{settings['phase']}"
        assert (out / "private" / "rules" / f"{key}.rkt").read_text(
            encoding="utf-8"
        ) == p.materialize_rule(settings, root=REPO_ROOT)

    manifest_on_disk = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_on_disk == manifest
    assert manifest["files"] == sorted(manifest["files"], key=lambda row: row["path"])
    for row in manifest["files"]:
        payload = (out / row["path"]).read_bytes()
        assert len(payload) == row["bytes"]
        assert hashlib.sha256(payload).hexdigest() == row["sha256"]

    with pytest.raises(FileExistsError):
        p.write_evidence(out, seeds=(0,), bridge=racket_bridge, root=REPO_ROOT)


def test_evidence_writer_refuses_duplicate_visible_challenges_and_cleans_partial(
    racket_bridge, monkeypatch, tmp_path,
):
    p = prototype()
    base = p.generate_episode(
        0, demos=1, queries=1, bridge=racket_bridge, root=REPO_ROOT
    )

    def duplicate_episode(seed, **kwargs):
        del kwargs
        episode = copy.deepcopy(base)
        episode["seed"] = seed
        episode["settings"] = p.parameter_for_seed(seed)
        return episode

    monkeypatch.setattr(p, "generate_episode", duplicate_episode)
    out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="same visible public challenge"):
        p.write_evidence(
            out,
            seeds=(0, 1),
            demos=1,
            queries=1,
            bridge=racket_bridge,
            root=REPO_ROOT,
        )
    assert not out.exists()


def test_promotion_adapter_and_manifest_contract(racket_bridge):
    p = prototype()
    adapter_path = TASK_ROOT / "workspace" / "parametric" / "adapter.py"
    promotion_path = TASK_ROOT / "workspace" / "parametric" / "promotion.json"
    assert adapter_path.is_file()
    assert promotion_path.is_file()

    spec = importlib.util.spec_from_file_location(
        "parametric_route_adapter_44690b1b635f", adapter_path
    )
    assert spec is not None and spec.loader is not None
    adapter = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = adapter
    try:
        spec.loader.exec_module(adapter)
    finally:
        sys.modules.pop(spec.name, None)

    selected = SETTINGS[2]
    assert adapter.program(selected) == p.materialize_rule(selected, root=REPO_ROOT)
    episode = adapter.generate(
        2,
        selected,
        1,
        1,
        bridge=racket_bridge,
        root=REPO_ROOT,
    )
    assert episode["settings"] == selected
    assert len(episode["train"]) == len(episode["test"]) == 1

    promotion = json.loads(promotion_path.read_text(encoding="utf-8"))
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "adapter": "generators/44690b1b635f/workspace/parametric/adapter.py",
        "parameters": {
            "connectivity": ["cardinal", "king"],
            "phase": ["center_even", "arm_even"],
        },
        "default": {"connectivity": "cardinal", "phase": "center_even"},
        "limits": {"demos": [1, 8], "queries": [1, 8]},
    }


def test_prototype_inventory_binds_reviewed_files():
    inventory_path = (
        TASK_ROOT / "workspace" / "parametric" / "evidence" / "manifest.json"
    )
    assert inventory_path.is_file()
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert inventory["schema"] == "arcpuzzles-parametric-prototype-evidence-v1"
    assert inventory["task_id"] == TASK_ID
    assert inventory["status"] == "proposed_unapproved"
    assert inventory["variant_approved"] is False
    assert inventory["production_parametric_api"] is False
    assert inventory["canonical_source_sha256"] == CANONICAL_SHA256

    expected_paths = {
        f"generators/{TASK_ID}/workspace/parametric/README.md",
        f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        f"generators/{TASK_ID}/workspace/parametric/promotion.json",
        f"generators/{TASK_ID}/tests/test_parametric_route_variants.py",
    }
    rows = inventory["files"]
    assert [row["path"] for row in rows] == sorted(expected_paths)
    for row in rows:
        payload = (REPO_ROOT / row["path"]).read_bytes()
        assert len(payload) == row["bytes"]
        assert hashlib.sha256(payload).hexdigest() == row["sha256"]

    generator_payload = (TASK_ROOT / "generator.py").read_bytes()
    assert inventory["generator_sha256"] == hashlib.sha256(
        generator_payload
    ).hexdigest()
    assert inventory["parameters"] == {
        "connectivity": ["cardinal", "king"],
        "phase": ["center_even", "arm_even"],
    }

