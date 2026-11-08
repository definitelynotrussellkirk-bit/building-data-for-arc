"""Focused regression tests for the contact-cluster generator repair."""
from __future__ import annotations

import copy
from collections import deque
import hashlib
import importlib.util
import json
import random
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
TASK_ID = "366cda05b486"
GENERATOR_PATH = next(path for path in (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py",
) if path.is_file())
DATA_ROOT = canonical_path(ROOT).parent.parent
BASE_PATH = DATA_ROOT / "base/solutions/banks/3a1815be7c2e/S12_M2__366cda05b486.json"
SPEC = importlib.util.spec_from_file_location(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def _grid_literal(grid) -> str:
    return "'(" + " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid) + ")"


def _task_rule_callable(source) -> str:
    """Wrap this task's two exact let bodies without staging-only imports.

    Canonical and archival sources already use valid Racket bindings and only
    need g in scope. Strip comments before the bridge flattens newlines. The
    helpers used here do not invoke the general scripts-dependent normalizer.
    """
    body = strip_rule_wrapper(strip_line_comments(source))
    if not body.lstrip().startswith("(let "):
        raise ValueError("this task's canonical/archival rule must have a let body")
    return f"(lambda (g) {body})"


def rule_application(source, grid) -> str:
    return f"({_task_rule_callable(source)} {_grid_literal(grid)})"


def purity_body(source, first_grid, second_grid) -> str:
    """Execute A-B-A atomically, preserving bridge restart independence."""
    return (
        f"(let* ([rule {_task_rule_callable(source)}] [a {_grid_literal(first_grid)}] "
        f"[b {_grid_literal(second_grid)}] [out-a1 (rule a)] "
        "[ignored (rule b)] [out-a2 (rule a)]) (list out-a1 out-a2 a))"
    )


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _degree_signature(grid: list[list[int]]) -> tuple[int, ...]:
    analysis = MODULE._analyze_grid(grid)
    selected = analysis["clusters"][analysis["seed_cluster_index"]]
    return tuple(
        sorted(len(analysis["adjacency"][index] & set(selected)) for index in selected)
    )


def _add_isolated_foreign_object(grid: list[list[int]]) -> list[list[int]]:
    changed = copy.deepcopy(grid)
    used = {value for row in changed for value in row}
    foreign = next(color for color in range(2, 10) if color not in used)
    h, w = len(changed), len(changed[0])
    for r in range(h):
        for c in range(w):
            if changed[r][c] != 0:
                continue
            halo = [
                changed[rr][cc]
                for rr in range(max(0, r - 1), min(h, r + 2))
                for cc in range(max(0, c - 1), min(w, c + 2))
            ]
            if all(value == 0 for value in halo):
                changed[r][c] = foreign
                return changed
    raise AssertionError("no isolated zero cell available")


def test_rule_hash_and_task_local_source_roles_are_explicit() -> None:
    canonical = _canonical_row()["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = base["racket_target"]
    assert MODULE.RULE_HASH == "f50313901f96"
    assert MODULE.RULE_HASH == _normalized_hash(canonical)
    assert target["target_code"] == canonical
    assert target["raw_code"] != canonical
    assert target["canonicalization_status"] == "preserved_executable_source"


def test_all_canonical_inputs_pass_the_strict_semantic_checker() -> None:
    for pair in _canonical_pairs():
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.self_check(pair["input"], meta={"canonical": True}) == []
        assert MODULE.expected_output(pair["input"]) == pair["output"]


def test_canonical_and_archival_racket_sources_have_parity_purity_and_a_b_a() -> None:
    canonical = _canonical_row()["program_solution"]
    archival = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]["raw_code"]
    pairs = _canonical_pairs()
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            canonical_out = bridge.eval_text(rule_application(canonical, pair["input"]))
            archival_out = bridge.eval_text(rule_application(archival, pair["input"]))
            assert canonical_out == pair["output"]
            assert archival_out == canonical_out
            assert pair["input"] == before
        probe = bridge.eval_text(purity_body(canonical, pairs[0]["input"], pairs[1]["input"]))
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_and_process_global_rng_state() -> None:
    state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert MODULE.generate(901, 17, difficulty="hard") == second


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable(difficulty: str) -> None:
    cases = [
        {
            "grid_h": 9,
            "grid_w": 12,
            "cluster_components": 5,
            "distractor_components": 4,
            "seed_size": 4,
            "orientation": "rot90",
            "palette_kind": "cool",
        },
        {
            "grid_h": 18,
            "grid_w": 20,
            "cluster_components": 3,
            "distractor_components": 2,
            "seed_size": 1,
            "orientation": "anti_transpose",
            "palette_kind": "warm",
        },
    ]
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(1400 + index, 2700 + index, difficulty=difficulty, **overrides)
        assert len(grid) == overrides["grid_h"]
        assert len(grid[0]) == overrides["grid_w"]
        observed = MODULE.observe_overrides(grid)
        assert observed == {
            key: overrides[key]
            for key in ("cluster_components", "distractor_components", "seed_size")
        }
        assert MODULE.self_check(grid, difficulty=difficulty) == []


def test_sequential_schedule_exposes_path_and_fan_graphs() -> None:
    common = {
        "cluster_components": 4,
        "distractor_components": 2,
        "seed_size": 2,
        "orientation": "identity",
        "palette_kind": "default",
    }
    path = MODULE.generate(811, 20, difficulty="medium", **common)
    fan = MODULE.generate(811, 21, difficulty="medium", **common)
    assert _degree_signature(path) == (1, 1, 2, 2)
    assert _degree_signature(fan) == (1, 1, 1, 3)
    assert MODULE.self_check(path) == []
    assert MODULE.self_check(fan) == []


def test_self_check_rejects_minimal_and_structural_impostors() -> None:
    lawful = MODULE.generate(
        312,
        992,
        difficulty="medium",
        cluster_components=4,
        distractor_components=3,
        seed_size=2,
    )
    assert MODULE.self_check(lawful) == []
    assert MODULE.self_check([[0] * 8 for _ in range(8)])
    assert MODULE.self_check([[1]])
    assert MODULE.self_check([[1, 1, 1]])
    assert MODULE.self_check([[1, 1], [1, 1]])

    joined = copy.deepcopy(lawful)
    analysis = MODULE._analyze_grid(joined)
    selected = analysis["clusters"][analysis["seed_cluster_index"]]
    distractor = next(cluster for cluster in analysis["clusters"] if cluster != selected)
    selected_cells = {cell for index in selected for cell in analysis["objects"][index]["cells"]}
    distractor_cells = {cell for index in distractor for cell in analysis["objects"][index]["cells"]}
    # A repeated-color leaf can be lawful. Join the two foreground islands
    # through background instead, violating the exact two-cluster contract.
    previous = {cell: None for cell in selected_cells}
    queue = deque(sorted(selected_cells))
    endpoint = None
    while queue and endpoint is None:
        r, c = queue.popleft()
        for dr, dc in MODULE._CARDINAL:
            rr, cc = r + dr, c + dc
            cell = rr, cc
            if not (0 <= rr < len(joined) and 0 <= cc < len(joined[0])) or cell in previous:
                continue
            previous[cell] = r, c
            if cell in distractor_cells:
                endpoint = cell
                break
            if joined[rr][cc] == 0:
                queue.append(cell)
    assert endpoint is not None
    while endpoint is not None:
        r, c = endpoint
        if joined[r][c] == 0:
            joined[r][c] = 2
        endpoint = previous[endpoint]
    assert any("exactly two contact clusters" in error for error in MODULE.self_check(joined))


def test_negative_recombination_is_rejected_while_racket_executes() -> None:
    canonical = _canonical_row()["program_solution"]
    lawful = MODULE.generate(
        717,
        818,
        difficulty="hard",
        grid_h=14,
        grid_w=17,
        cluster_components=3,
        distractor_components=2,
        seed_size=1,
    )
    recombined = _add_isolated_foreign_object(lawful)
    assert any("exactly two contact clusters" in error for error in MODULE.self_check(recombined))

    bridge = RacketBridge()
    try:
        output = bridge.eval_text(rule_application(canonical, recombined))
    finally:
        bridge.shutdown()
    assert output == MODULE.expected_output(recombined)


def test_generated_inputs_match_racket_authority_across_bands() -> None:
    canonical = _canonical_row()["program_solution"]
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(8):
                grid = MODULE.generate(5000 + seed, 900 + seed + band_index * 20, difficulty=band)
                before = copy.deepcopy(grid)
                output = bridge.eval_text(rule_application(canonical, grid))
                assert output == MODULE.expected_output(grid)
                assert grid == before
    finally:
        bridge.shutdown()
