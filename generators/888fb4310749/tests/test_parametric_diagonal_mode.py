"""Focused tests for the proposed episode-level diagonal-mode prototype."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "888fb4310749"
ROOT = find_root(__file__)
TASK_DIR = ROOT / "generators" / TASK_ID
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
COUNTEREXAMPLE_PATH = (
    TASK_DIR / "counterexamples" / "fixed_36_color_shortcut.json"
)
GENERATOR, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "task_888fb4310749_parametric_diagonal_mode", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json_sha256(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _fixed_36_shortcut(grid):
    """Canonical geometry with a hard-coded 3/6 alternate-color pair."""
    facts = GENERATOR._rule_facts(grid)
    height, width = len(grid), len(grid[0])
    row0, col0 = facts["row0"], facts["col0"]
    block_height = facts["block_height"]
    block_width = facts["block_width"]
    step = facts["step"]
    alt_color = 6 if facts["color"] == 3 else 3
    output = [list(row) for row in grid]

    for multiple in range(-40, 41):
        for sign in (1, -1):
            diagonal_row = row0 + multiple * step
            diagonal_col = col0 + sign * multiple * step
            rotated_row = diagonal_row + block_height
            rotated_col = diagonal_col + (
                block_width if sign == 1 else -block_height
            )
            if GENERATOR._intersects(
                rotated_row,
                rotated_col,
                block_width,
                block_height,
                height,
                width,
            ):
                GENERATOR._stamp(
                    output,
                    rotated_row,
                    rotated_col,
                    block_width,
                    block_height,
                    alt_color,
                )

    same_anchors = []
    for multiple in range(-40, 41):
        for sign in (1, -1):
            anchor = (
                row0 + multiple * step,
                col0 + sign * multiple * step,
            )
            if (
                GENERATOR._intersects(
                    anchor[0],
                    anchor[1],
                    block_height,
                    block_width,
                    height,
                    width,
                )
                and anchor not in same_anchors
            ):
                same_anchors.append(anchor)
    for anchor_row, anchor_col in same_anchors:
        GENERATOR._stamp(
            output,
            anchor_row,
            anchor_col,
            block_height,
            block_width,
            facts["color"],
        )
    return output


def test_diagonal_mode_contract_is_bounded_and_default_is_exact_canonical():
    proto = _load_prototype()
    assert proto.DIAGONAL_MODES == ("both", "falling", "rising")
    assert proto.DEFAULT_DIAGONAL_MODE == "both"
    assert proto.PARAMETERS["diagonal_mode"]["allowed"] == proto.DIAGONAL_MODES
    assert proto.PARAMETERS["diagonal_mode"]["default"] == "both"
    canonical = proto.canonical_program(root=ROOT)
    assert proto.render_program("both", root=ROOT) == canonical
    assert canonical.count("(list 1 -1)") == 2
    falling = proto.render_program("falling", root=ROOT)
    rising = proto.render_program("rising", root=ROOT)
    assert falling.count("(list 1)") == 2
    assert "(list 1 -1)" not in falling
    assert rising.count("(list -1)") == 2
    assert "(list 1 -1)" not in rising
    assert len({canonical, falling, rising}) == 3
    assert proto.choose_parameters(0) == {"diagonal_mode": "both"}
    assert proto.choose_parameters(1) == {"diagonal_mode": "falling"}
    assert proto.choose_parameters(2) == {"diagonal_mode": "rising"}
    assert proto.choose_parameters(3) == {"diagonal_mode": "both"}


@pytest.mark.parametrize("seed", [True, False, -1, 1.5, "1", None])
def test_invalid_episode_seeds_fail_closed(seed):
    proto = _load_prototype()
    with pytest.raises(ValueError, match="seed"):
        proto.choose_parameters(seed)


@pytest.mark.parametrize("mode", [None, True, 1, "main", "BOTH"])
def test_invalid_diagonal_modes_fail_closed(mode):
    proto = _load_prototype()
    with pytest.raises(ValueError, match="diagonal_mode"):
        proto.render_program(mode, root=ROOT)


def test_parameter_independent_fixtures_are_lawful_and_separate_every_mode():
    proto = _load_prototype()
    pair_count = proto.DEFAULT_DEMO_COUNT + proto.DEFAULT_QUERY_COUNT
    grids = proto.fixture_inputs(20261023, count=pair_count, root=ROOT)
    assert grids == proto.fixture_inputs(20261023, count=pair_count, root=ROOT)
    assert len(grids) == 7
    assert len({_json_sha256(grid) for grid in grids}) == 7
    for grid in grids:
        assert GENERATOR.self_check(grid) == []
        outputs = {
            mode: proto.apply_python(grid, mode)
            for mode in proto.DIAGONAL_MODES
        }
        assert outputs["both"] == GENERATOR.rule_mirror(grid)
        assert len({_json_sha256(output) for output in outputs.values()}) == 3


def test_complete_episode_binds_one_mode_and_public_file_hides_it():
    proto = _load_prototype()
    for mode in proto.DIAGONAL_MODES:
        episode = proto.generate_episode_python(
            1234,
            diagonal_mode=mode,
            root=ROOT,
        )
        assert episode["parameters"] == {"diagonal_mode": mode}
        assert episode["parameter_draw_count"] == 1
        assert episode["demo_count"] == 3
        assert episode["query_count"] == 4
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        all_inputs = [
            pair["input"] for pair in [*episode["train"], *episode["test"]]
        ]
        assert len({_json_sha256(grid) for grid in all_inputs}) == 7
        assert set(episode["rivals"]) == set(proto.DIAGONAL_MODES) - {mode}
        for rival in episode["rivals"].values():
            assert rival["status"] == "distinguished"
            assert rival["refuting_demonstration_indices"]
            assert rival["query_differs"] is True
            assert rival["all_queries_differ"] is True
            assert rival["query_differing_indices"] == [0, 1, 2, 3]

        public = proto.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public, sort_keys=True)
        for forbidden in (
            "diagonal_mode",
            "program",
            "both",
            "falling",
            "rising",
            "rival",
        ):
            assert forbidden not in serialized


def test_demo_and_query_counts_are_independent_and_every_query_is_checked():
    """Catch hard-coded one-query slicing and first-query-only rival checks."""
    proto = _load_prototype()
    episode = proto.generate_episode_python(
        4321,
        diagonal_mode="falling",
        demo_count=2,
        query_count=5,
        root=ROOT,
    )
    assert episode["demo_count"] == 2
    assert episode["query_count"] == 5
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 5
    all_inputs = [pair["input"] for pair in [*episode["train"], *episode["test"]]]
    assert len({_json_sha256(grid) for grid in all_inputs}) == 7
    for rival in episode["rivals"].values():
        assert rival["refuting_demonstration_indices"]
        assert rival["query_differing_indices"] == [0, 1, 2, 3, 4]
        assert rival["all_queries_differ"] is True


@pytest.mark.parametrize(
    ("demo_count", "query_count"),
    [
        (0, 4),
        (3, 0),
        (True, 4),
        (3, False),
        (1.5, 4),
        (3, "4"),
        (9, 4),
        (3, 9),
    ],
)
def test_invalid_demo_and_query_counts_fail_closed(demo_count, query_count):
    """Catch booleans, non-integers, zero, and unbounded episode sizes."""
    proto = _load_prototype()
    with pytest.raises(ValueError, match="count"):
        proto.generate_episode_python(
            1234,
            demo_count=demo_count,
            query_count=query_count,
            root=ROOT,
        )


def test_public_export_id_and_bytes_ignore_private_only_fields():
    """Catch public identifiers that accidentally include hidden metadata."""
    proto = _load_prototype()
    episode = proto.generate_episode_python(
        1234,
        diagonal_mode="both",
        root=ROOT,
    )
    public_id, payload = proto.public_export(episode)
    challenge = proto.public_challenge(episode)
    assert public_id == public_challenge_id(challenge)
    assert payload == public_challenge_bytes(challenge)

    private_variant = deepcopy(episode)
    private_variant["seed"] = 999_999
    private_variant["parameters"] = {"diagonal_mode": "private-only-change"}
    private_variant["program"] = "private program text"
    private_variant["program_sha256"] = "0" * 64
    private_variant["rivals"] = {"private": {"query_answers": "changed"}}
    private_variant["label_authority"] = "private authority changed"
    private_variant["test"][0]["output"] = [[9]]

    assert proto.public_export(private_variant) == (public_id, payload)


def test_public_export_batch_sorts_ids_and_rejects_duplicate_visible_payloads():
    """Catch ordinal ordering and silent duplicate public challenges."""
    proto = _load_prototype()
    episodes = [
        proto.generate_episode_python(1234, diagonal_mode=mode, root=ROOT)
        for mode in proto.DIAGONAL_MODES
    ]
    records = proto.prepare_public_exports(list(reversed(episodes)))
    assert [record["public_id"] for record in records] == sorted(
        record["public_id"] for record in records
    )
    assert all(
        record["public_bytes"]
        == public_challenge_bytes(proto.public_challenge(record["episode"]))
        for record in records
    )

    duplicate = deepcopy(episodes[0])
    duplicate["seed"] += 1
    duplicate["parameters"] = {"diagonal_mode": "hidden duplicate"}
    with pytest.raises(ValueError, match="duplicate visible public challenge"):
        proto.prepare_public_exports([episodes[0], duplicate])


def test_materialized_evidence_executes_all_modes_with_real_racket(tmp_path: Path):
    proto = _load_prototype()
    out = tmp_path / "diagonal-mode-evidence"
    report = proto.materialize(out, base_seed=20261023)
    assert report["status"] == "prototype"
    assert report["default_program_exact_canonical"] is True
    assert report["all_labels_and_rivals_executed_in_racket"] is True
    assert report["all_episode_demonstrations_distinguish_rivals"] is True
    assert report["canonical_labels_checked"] == report["canonical_labels_passed"] == 4
    assert report["complete_episodes"] == 3
    assert report["cross_mode_witness"]["all_outputs_pairwise_distinct"] is True
    assert report["input_policy"]["demo_count"] == 3
    assert report["input_policy"]["query_count"] == 4

    rule_files = sorted((out / "private" / "rules").glob("*.rkt"))
    assert len(rule_files) == 3
    episodes = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((out / "private" / "episodes").glob("*.json"))
    ]
    assert {
        episode["parameters"]["diagonal_mode"] for episode in episodes
    } == set(proto.DIAGONAL_MODES)
    assert all(len(episode["train"]) == 3 for episode in episodes)
    assert all(len(episode["test"]) == 4 for episode in episodes)
    public_paths = sorted((out / "public").glob("*.json"))
    assert len(public_paths) == len(proto.DIAGONAL_MODES)
    assert [row["public_id"] for row in report["episodes"]] == sorted(
        row["public_id"] for row in report["episodes"]
    )
    for path in public_paths:
        public = json.loads(path.read_text(encoding="utf-8"))
        assert path.stem == public_challenge_id(public)
        assert path.read_bytes() == public_challenge_bytes(public)
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public, sort_keys=True)
        assert "diagonal_mode" not in serialized
        assert "program" not in serialized


def test_fixed_36_color_shortcut_fits_canonical_but_generated_witness_refutes_it():
    fixture = json.loads(COUNTEREXAMPLE_PATH.read_text(encoding="utf-8"))
    assert fixture["schema"] == "888fb4310749-fixed-36-color-shortcut-v1"
    assert all(
        _fixed_36_shortcut(pair["input"]) == pair["output"]
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    )

    emitted = GENERATOR.generate(
        fixture["emission"]["seed"],
        fixture["emission"]["sample_index"],
        difficulty=fixture["emission"]["difficulty"],
        **fixture["emission"]["overrides"],
    )
    assert emitted == fixture["input"]
    assert GENERATOR.self_check(emitted) == []
    assert fixture["source_color"] not in (3, 6)
    intended = GENERATOR.rule_mirror(emitted)
    rival = _fixed_36_shortcut(emitted)
    assert intended == fixture["intended_output"]
    assert rival == fixture["rival_output"]
    assert intended != rival
    assert _json_sha256(emitted) == fixture["input_sha256"]
    assert _json_sha256(intended) == fixture["intended_output_sha256"]
    assert _json_sha256(rival) == fixture["rival_output_sha256"]
