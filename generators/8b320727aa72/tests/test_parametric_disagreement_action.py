from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root


TASK_ID = "8b320727aa72"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
SPEC = importlib.util.spec_from_file_location("disagreement_action_prototype", PROTOTYPE_PATH)
assert SPEC is not None and SPEC.loader is not None
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def _canonical_program() -> str:
    programs = set()
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _lawful_single_erasure_grid() -> tuple[list[list[int]], list[list[int]]]:
    consensus = [
        [2, 7, 8, 8, 8],
        [4, 8, 8, 8, 8],
        [5, 8, 6, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
    ]
    grid = [[3 for _ in range(29)] for _ in range(29)]
    for tile_index in range(25):
        tile_r, tile_c = divmod(tile_index, 5)
        row0, col0 = tile_r * 6, tile_c * 6
        for r in range(5):
            for c in range(5):
                grid[row0 + r][col0 + c] = consensus[r][c]
    grid[24][24] = 8
    return grid, consensus


def _contains_key(value, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return bool(set(value) & forbidden) or any(
            _contains_key(child, forbidden) for child in value.values()
        )
    if isinstance(value, list):
        return any(_contains_key(child, forbidden) for child in value)
    return False


def test_mark_program_is_exact_canonical_authority_and_choices_are_episode_deterministic():
    assert prototype.rule_for("mark", root=ROOT) == _canonical_program()
    assert prototype.DEFAULT_ACTION == "mark"
    assert set(prototype.ALLOWED_ACTIONS) == {"mark", "restore"}
    for seed in range(32):
        assert prototype.choose_parameters(seed) == prototype.choose_parameters(seed)
        assert prototype.choose_parameters(seed)["disagreement_action"] in {
            "mark",
            "restore",
        }
    assert {
        prototype.choose_parameters(seed)["disagreement_action"]
        for seed in range(64)
    } == {"mark", "restore"}


def test_both_exact_racket_programs_produce_hand_derived_outputs():
    grid, consensus = _lawful_single_erasure_grid()
    before = copy.deepcopy(grid)
    expected_mark = [row[:] for row in consensus]
    expected_mark[0][0] = 1

    with RacketBridge() as bridge:
        mark = prototype.execute_rule(prototype.rule_for("mark", root=ROOT), grid, bridge)
        restore = prototype.execute_rule(
            prototype.rule_for("restore", root=ROOT), grid, bridge
        )

    assert mark == expected_mark
    assert restore == consensus
    assert mark != restore
    assert grid == before


def test_complete_episode_fixes_one_action_and_demos_refute_the_other_setting():
    with RacketBridge() as bridge:
        private = prototype.materialize_episode(
            20261023,
            disagreement_action="restore",
            n_demos=2,
            n_queries=1,
            bridge=bridge,
            root=ROOT,
        )

    assert private["parameters"] == {"disagreement_action": "restore"}
    assert private["all_labels_executed_in_racket"] is True
    assert private["demonstrations_refute"] == ["mark"]
    assert len(private["train"]) == 2
    assert len(private["test"]) == 1
    assert all(pair["selected_output"] != pair["rival_output"] for pair in private["train"])

    public = prototype.public_challenge(private)
    assert len(public["train"]) == 2
    assert len(public["test"]) == 1
    assert "output" not in public["test"][0]
    assert not _contains_key(
        public,
        {
            "parameters",
            "parameter_spec",
            "program",
            "program_sha256",
            "rival_output",
            "selected_output",
            "query_answers",
            "disagreement_action",
        },
    )


def test_write_evidence_retains_two_settings_and_a_shared_differing_witness(tmp_path):
    manifest = prototype.write_evidence(
        tmp_path,
        mark_seed=10,
        restore_seed=11,
        root=ROOT,
    )
    assert manifest["status"] == "proposed prototype; not production-approved"
    assert manifest["canonical_default_unchanged"] is True
    assert {row["action"] for row in manifest["episodes"]} == {"mark", "restore"}

    witness = json.loads((tmp_path / "private" / "shared-witness.json").read_text())
    assert witness["outputs"]["mark"] != witness["outputs"]["restore"]
    for action in ("mark", "restore"):
        episode_row = next(row for row in manifest["episodes"] if row["action"] == action)
        public_path = tmp_path / episode_row["public"]
        public = json.loads(public_path.read_text())
        assert public_path.name == prototype.public_filename(public)
        assert "output" not in public["test"][0]
        assert not _contains_key(public, {"parameters", "program", "query_answers"})
        assert (tmp_path / "rules" / f"{action}.rkt").is_file()
