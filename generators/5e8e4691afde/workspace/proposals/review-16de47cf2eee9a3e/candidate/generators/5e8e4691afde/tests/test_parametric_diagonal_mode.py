"""Focused contract tests for the proposed diagonal-mode prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "5e8e4691afde"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("parametric_5e8e4691afde", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.append(row["program_solution"])
    assert len(programs) == 1
    return programs[0]


def _frozen(grid):
    return tuple(map(tuple, grid))


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=96) as instance:
        yield instance


@pytest.fixture(scope="module")
def evidence(prototype, bridge):
    return prototype.build_evidence(
        bridge,
        seed=20261023,
        demo_count=2,
        query_count=4,
    )


def test_parameter_contract_and_default_program_are_exact(prototype):
    assert prototype.ALLOWED_DIAGONAL_MODES == ("both", "falling", "rising")
    assert prototype.DEFAULT_DIAGONAL_MODE == "both"
    assert prototype.PARAMETERS["diagonal_mode"]["allowed"] == prototype.ALLOWED_DIAGONAL_MODES
    assert prototype.PARAMETERS["diagonal_mode"]["default"] == "both"

    canonical = _canonical_program()
    assert prototype.racket_program("both") == canonical
    falling = prototype.racket_program("falling")
    rising = prototype.racket_program("rising")
    assert len({canonical, falling, rising}) == 3
    assert "(or (= (- r c) (- nr nc)) (= (+ r c) (+ nr nc)))" not in falling
    assert "(or (= (- r c) (- nr nc)) (= (+ r c) (+ nr nc)))" not in rising
    assert "(= (- r c) (- nr nc))" in falling
    assert "(= (+ r c) (+ nr nc))" in rising
    assert prototype.racket_sha256("both") == hashlib.sha256(canonical.encode()).hexdigest()


def test_invalid_parameters_seeds_and_counts_fail_closed(prototype, bridge):
    for bad in (None, True, 1, "BOTH", "diagonal"):
        with pytest.raises((TypeError, ValueError), match="diagonal_mode"):
            prototype.racket_program(bad)
    for bad_seed in (True, 1.5, "17", None):
        with pytest.raises(TypeError, match="seed"):
            prototype.choose_diagonal_mode(bad_seed)
        with pytest.raises(TypeError, match="seed"):
            prototype.build_episode(bridge, bad_seed)
    for bad_count in (True, 0, -1, 17, 1.5, "4"):
        with pytest.raises((TypeError, ValueError), match="count"):
            prototype.build_episode(bridge, 17, demo_count=bad_count)
        with pytest.raises((TypeError, ValueError), match="count"):
            prototype.build_episode(bridge, 17, query_count=bad_count)


def test_each_setting_has_two_demos_four_distinct_queries_and_racket_rivals(
    prototype, bridge, evidence
):
    assert evidence["status"] == "prototype"
    assert set(evidence["settings"]) == set(prototype.ALLOWED_DIAGONAL_MODES)
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)

    for mode, record in evidence["settings"].items():
        episode = record["episode"]
        assert episode["parameter"] == {"diagonal_mode": mode}
        assert episode["parameter_draw_count"] == 1
        assert episode["demo_count"] == 2
        assert episode["query_count"] == 4
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        assert len({_frozen(pair["input"]) for pair in pairs}) == 6
        assert episode["analysis"]["all_inputs_distinct"] is True
        assert episode["analysis"]["demonstrations_distinguish_all_rivals"] is True
        assert episode["analysis"]["every_query_differs_from_all_rivals"] is True
        assert episode["analysis"]["status"] == "no_ambiguity_found"

        for pair in pairs:
            assert pair["output"] == prototype.run_racket(bridge, mode, pair["input"])
            if mode == "both":
                assert pair["output"] == generator.rule_mirror(pair["input"])

        assert set(episode["rivals"]) == set(prototype.ALLOWED_DIAGONAL_MODES) - {mode}
        for rival in episode["rivals"].values():
            assert rival["status"] == "distinguished"
            assert rival["refuting_demonstration_indices"]
            assert rival["query_differences"] == [True, True, True, True]


def test_public_projection_and_identifier_depend_only_on_visible_content(prototype, evidence):
    episode = evidence["settings"]["both"]["episode"]
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 2
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    identifier = prototype.public_identifier(episode)
    assert identifier == public_challenge_id(public)
    assert hashlib.sha256(public_challenge_bytes(public)).hexdigest() == identifier

    hidden_changed = deepcopy(episode)
    hidden_changed["parameter"]["diagonal_mode"] = "falling"
    hidden_changed["test"][0]["output"][0][0] = (hidden_changed["test"][0]["output"][0][0] + 1) % 10
    assert prototype.public_challenge(hidden_changed) == public
    assert prototype.public_identifier(hidden_changed) == identifier

    visible_changed = deepcopy(episode)
    visible_changed["train"][0]["output"][0][0] = (visible_changed["train"][0]["output"][0][0] + 1) % 10
    assert prototype.public_identifier(visible_changed) != identifier


def test_evidence_covers_canonical_default_and_same_input_witness(prototype, evidence):
    assert evidence["canonical_default"]["checked"] == 5
    assert evidence["canonical_default"]["passed"] == 5
    assert evidence["canonical_default"]["all_passed"] is True
    witness = evidence["distinguishing_witness"]
    assert witness["all_outputs_pairwise_distinct"] is True
    assert set(witness["outputs"]) == set(prototype.ALLOWED_DIAGONAL_MODES)
    assert len(set(witness["output_sha256"].values())) == 3


def test_materialized_public_files_are_exact_visible_bytes_and_sorted(
    prototype, evidence, tmp_path: Path
):
    out = tmp_path / "diagonal-mode-evidence"
    summary = prototype.materialize(out, evidence)
    assert summary["status"] == "prototype"
    assert summary["public_file_count"] == 3
    assert summary["private_episode_count"] == 3

    public_files = sorted((out / "public").glob("*.json"))
    assert [path.stem for path in public_files] == sorted(path.stem for path in public_files)
    assert len(public_files) == 3
    for path in public_files:
        body = path.read_bytes()
        assert hashlib.sha256(body).hexdigest() == path.stem
        challenge = json.loads(body)
        assert body == public_challenge_bytes(challenge)
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        text = body.decode("utf-8")
        for forbidden in ("diagonal_mode", "both", "falling", "rising", "program", "seed", "output_sha256"):
            assert forbidden not in text

    setting_map = json.loads((out / "private" / "setting-map.json").read_text())
    assert set(row["diagonal_mode"] for row in setting_map["episodes"]) == set(
        prototype.ALLOWED_DIAGONAL_MODES
    )
    assert [row["public_id"] for row in setting_map["episodes"]] == sorted(
        row["public_id"] for row in setting_map["episodes"]
    )
    assert len(list((out / "private" / "rules").glob("*.rkt"))) == 3
    assert (out / "manifest.json").is_file()
