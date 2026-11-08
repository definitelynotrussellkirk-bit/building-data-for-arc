#!/usr/bin/env python3
"""Bounded self-audit for the c0bd45c81959 parametric family.

The tool checks deterministic matched-input episodes, demonstration-only finite
rivals, sequential public projection, and selected labels through protected
Racket.  It writes private source-bound evidence only; it grants no approval,
qualification, acceptance, or training admission.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "c0bd45c81959"
HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
DEMO_COUNTS = (2, 3, 6)
QUERY_COUNT = 4


def _load_adapter():
    path = HOME / "adapter.py"
    name = "_c0bd45c81959_parametric_audit_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


ADAPTER = _load_adapter()


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _bordered(interior: list[list[int]]) -> list[list[int]]:
    return [[0, 0, 0, 0, 0], [0, *interior[0], 0], [0, *interior[1], 0], [0, 0, 0, 0, 0]]


def _first_cell_modes(grid: list[list[int]]) -> list[list[int]]:
    return [[grid[1 + 4 * br][1 + 3 * bc] for bc in range(3)] for br in range(2)]


def _duplicate_bbox_total(modes: list[list[int]], *, endpoints_only: bool = False,
                          full: bool = False) -> list[list[int]]:
    counts = Counter(value for row in modes for value in row)
    repeated = [value for value, count in counts.items() if count == 2]
    if len(repeated) != 1:
        return [[0] * 5 for _ in range(4)]
    target = repeated[0]
    points = [(r, c) for r in range(2) for c in range(3) if modes[r][c] == target]
    r0, r1 = min(r for r, _ in points), max(r for r, _ in points)
    c0, c1 = min(c for _, c in points), max(c for _, c in points)
    interior = []
    for r in range(2):
        row = []
        for c in range(3):
            selected = full or ((r, c) in points if endpoints_only else r0 <= r <= r1 and c0 <= c <= c1)
            row.append(target if selected else 0)
        interior.append(row)
    return _bordered(interior)


def rival_outputs(grid: list[list[int]], operation: str) -> dict[str, list[list[int]]]:
    modes = ADAPTER.extract_modes(grid)
    if operation == "all_modes":
        return {
            "opposite_setting_duplicate_bbox": ADAPTER.solve(grid, "duplicate_bbox"),
            "first_cell_instead_of_mode": _bordered(_first_cell_modes(grid)),
            "constant_black": [[0] * 5 for _ in range(4)],
        }
    return {
        "opposite_setting_all_modes": ADAPTER.solve(grid, "all_modes"),
        "first_cell_then_bbox": _duplicate_bbox_total(_first_cell_modes(grid)),
        "duplicate_endpoints_only": _duplicate_bbox_total(modes, endpoints_only=True),
        "fixed_full_interior": _duplicate_bbox_total(modes, full=True),
        "constant_black": [[0] * 5 for _ in range(4)],
    }


def _support():
    runtime = ROOT / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    import reviewer_support
    expected = runtime / "reviewer_support.py"
    if Path(reviewer_support.__file__).resolve() != expected.resolve():
        raise RuntimeError("public projection did not use this checkout's reviewer_support")
    return reviewer_support


def _public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    visible = json.loads(_support().public_challenge_bytes(episode))
    if type(query_index) is not int or not 0 <= query_index < len(visible["test"]):
        raise ValueError("query_index must be an exact in-range integer")
    return {"train": copy.deepcopy(visible["train"]), "test": [copy.deepcopy(visible["test"][query_index])]}


def _public_checks(episode: dict[str, Any]) -> int:
    support = _support()
    raw = support.public_challenge_bytes(episode)
    visible = json.loads(raw)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert support.public_challenge_id(episode) == hashlib.sha256(raw).hexdigest()

    private = copy.deepcopy(episode)
    private.update({"seed": -1, "settings": {"operation": "PRIVATE"},
                    "program_solution": "PRIVATE", "query_total": 999})
    for pair in private["test"]:
        pair["output"] = [[9]]
        pair["private_hint"] = "PRIVATE"
    assert support.public_challenge_bytes(private) == raw

    one = {"train": copy.deepcopy(episode["train"]), "test": [copy.deepcopy(episode["test"][0])],
           "program_solution": episode["program_solution"]}
    assert _public_turn(episode, 0) == _public_turn(one, 0)
    changed_later = copy.deepcopy(episode)
    for pair in changed_later["test"][1:]:
        pair["input"] = [[9]]
    assert _public_turn(changed_later, 0) == _public_turn(episode, 0)

    for index in range(len(episode["test"])):
        turn = _public_turn(episode, index)
        assert set(turn) == {"train", "test"}
        assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}
    return len(episode["test"])


def structural_audit(seed_count: int = 16) -> dict[str, Any]:
    """Exercise finite sampler, teaching, rival, and public-export surfaces."""
    if type(seed_count) is not int or not 1 <= seed_count <= 10_000:
        raise ValueError("seed_count must be an exact integer in 1..10000")
    failures: list[dict[str, Any]] = []
    episodes = matched = certificates = turns = visible_pairs = prefix_checks = 0
    rows: list[dict[str, Any]] = []

    for seed in range(seed_count):
        for demos in DEMO_COUNTS:
            by_operation: dict[str, dict[str, Any]] = {}
            for operation in ADAPTER.OPERATIONS:
                context = {"seed": seed, "demos": demos, "operation": operation}
                try:
                    episode = ADAPTER.generate(seed, {"operation": operation}, demos, QUERY_COUNT)
                    by_operation[operation] = episode
                    episodes += 1
                    pairs = episode["train"] + episode["test"]
                    visible_pairs += len(pairs)
                    assert len(episode["train"]) == demos and len(episode["test"]) == QUERY_COUNT
                    assert episode["program_solution"] == ADAPTER.program({"operation": operation})
                    keys = [_grid_key(pair["input"]) for pair in pairs]
                    assert len(keys) == len(set(keys)), "episode contains duplicate visible inputs"
                    assert all(pair["output"] == ADAPTER.solve(pair["input"], operation) for pair in pairs)

                    minimum = ADAPTER.generate(seed, {"operation": operation}, 2, QUERY_COUNT)
                    one_query = ADAPTER.generate(seed, {"operation": operation}, demos, 1)
                    assert episode["train"][:2] == minimum["train"]
                    assert episode["test"] == minimum["test"]
                    assert one_query["train"] == episode["train"]
                    assert one_query["test"] == episode["test"][:1]
                    prefix_checks += 1
                    turns += _public_checks(episode)

                    names = sorted(rival_outputs(episode["train"][0]["input"], operation))
                    surviving: list[str] = []
                    dangerous: list[str] = []
                    for name in names:
                        demo_predictions = [rival_outputs(pair["input"], operation)[name]
                                            for pair in episode["train"]]
                        if demo_predictions == [pair["output"] for pair in episode["train"]]:
                            surviving.append(name)
                            query_predictions = [rival_outputs(pair["input"], operation)[name]
                                                 for pair in episode["test"]]
                            if query_predictions != [pair["output"] for pair in episode["test"]]:
                                dangerous.append(name)
                    if surviving:
                        raise AssertionError(f"declared rivals fit all demonstrations: {surviving}")
                    certificates += 1
                    rows.append({**context, "queries": QUERY_COUNT,
                                 "declared_rivals": names, "surviving_rivals": surviving,
                                 "dangerous_rivals": dangerous})
                except Exception as exc:
                    failures.append({**context, "error": f"{type(exc).__name__}: {exc}"})

            if set(by_operation) == set(ADAPTER.OPERATIONS):
                first = by_operation[ADAPTER.OPERATIONS[0]]
                second = by_operation[ADAPTER.OPERATIONS[1]]
                left = [pair["input"] for pair in first["train"] + first["test"]]
                right = [pair["input"] for pair in second["train"] + second["test"]]
                if left != right:
                    failures.append({"seed": seed, "demos": demos,
                                     "error": "settings did not receive matched visible inputs"})
                else:
                    matched += 1

    return {
        "schema": "arcpuzzles-c0bd45c81959-structural-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "seed_count": seed_count,
        "seed_range": [0, seed_count - 1],
        "settings": [{"operation": value} for value in ADAPTER.OPERATIONS],
        "demo_counts": list(DEMO_COUNTS),
        "queries": QUERY_COUNT,
        "episodes": episodes,
        "visible_pairs": visible_pairs,
        "matched_input_checks": matched,
        "prefix_checks": prefix_checks,
        "declared_rival_certificates": certificates,
        "public_turn_checks": turns,
        "domain_limit": ADAPTER.DOMAIN_LIMIT,
        "rows": rows,
        "failures": failures,
        "scope": (
            "Finite deterministic Python sweep over declared settings, demo prefixes, public projection, "
            "and named plausible rivals. It is not a proof of unique inference or universal correctness."
        ),
    }


def wrong_intermediate_program() -> str:
    """Counterfactual: Stage A reads each block's top-left cell, then Stage B uses it."""
    return """(rule!
 (lambda (g)
   (let ()
     (define wrong-modes
       (for*/list ((br (range 0 2))
                   (bc (range 0 3)))
         (cell-at g (+ 1 (* br 4)) (+ 1 (* bc 3)))))
     (define target (first wrong-modes))
     (define positions
       (for*/list ((br (range 0 2))
                   (bc (range 0 3))
                   #:when (= (list-ref wrong-modes (+ (* br 3) bc)) target))
         (list br bc)))
     (define r0 (apply min (map first positions)))
     (define r1 (apply max (map first positions)))
     (define c0 (apply min (map second positions)))
     (define c1 (apply max (map second positions)))
     (grid-from-fn 4 5
       (lambda (r c)
         (cond
           ((or (= r 0) (= r 3) (= c 0) (= c 4)) 0)
           ((and (<= r0 (- r 1)) (<= (- r 1) r1)
                 (<= c0 (- c 1)) (<= (- c 1) c1)) target)
           (else 0)))))))"""


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def protected_audit() -> tuple[dict[str, Any], dict[str, Any]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    selected_seeds = (0, 17)
    selected_demos = (2, 6)
    failures: list[dict[str, Any]] = []
    evaluations = 0
    source = {operation: ADAPTER.program({"operation": operation}) for operation in ADAPTER.OPERATIONS}
    counterfactual = wrong_intermediate_program()
    wrapped = {name: wrap_rule(text) for name, text in {**source, "counterfactual": counterfactual}.items()}
    causal_case = None

    with RacketBridge(max_calls_before_restart=256) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket backend required")
        for seed in selected_seeds:
            for demos in selected_demos:
                for operation in ADAPTER.OPERATIONS:
                    episode = ADAPTER.generate(seed, {"operation": operation}, demos, QUERY_COUNT)
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = bridge.eval_text(f"({wrapped[operation]} {_literal(pair['input'])})")
                            evaluations += 1
                            if actual != pair["output"]:
                                failures.append({"seed": seed, "demos": demos, "operation": operation,
                                                 "split": split, "index": index,
                                                 "error": "protected Racket label differs from adapter claim"})
                    if operation == "duplicate_bbox" and causal_case is None:
                        for split in ("test", "train"):
                            for index, pair in enumerate(episode[split]):
                                alternative = bridge.eval_text(
                                    f"({wrapped['counterfactual']} {_literal(pair['input'])})"
                                )
                                evaluations += 1
                                if alternative != pair["output"]:
                                    causal_case = {
                                        "settings": {"operation": operation},
                                        "program": source[operation],
                                        "input": pair["input"],
                                        "output": pair["output"],
                                        "counterfactual_program": counterfactual,
                                        "counterfactual_output": alternative,
                                        "intermediate_value": ADAPTER.extract_modes(pair["input"]),
                                        "counterfactual_intermediate": _first_cell_modes(pair["input"]),
                                        "ablation": "wrong_intermediate",
                                        "source_episode": {"seed": seed, "demos": demos,
                                                           "split": split, "pair_index": index},
                                    }
                                    break
                            if causal_case is not None:
                                break
        if causal_case is None:
            failures.append({"error": "no protected causal case changed the final output"})

    report = {
        "schema": "arcpuzzles-c0bd45c81959-protected-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "racket": identity,
        "seeds": list(selected_seeds),
        "demo_counts": list(selected_demos),
        "settings": [{"operation": value} for value in ADAPTER.OPERATIONS],
        "queries": QUERY_COUNT,
        "protected_racket_evaluations": evaluations,
        "causal_output_changed": causal_case is not None,
        "failures": failures,
        "scope": "Selected finite labels and one counterfactual executed through protected Racket; no owner acceptance or universal proof.",
    }
    return report, causal_case


def run(out: Path, seed_count: int = 16) -> dict[str, Any]:
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    structural = structural_audit(seed_count)
    protected, case = protected_audit()
    status = "passed" if structural["status"] == protected["status"] == "passed" else "failed"
    out.mkdir(parents=True)
    (out / "structural-audit.json").write_text(
        json.dumps(structural, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    (out / "protected-racket-audit.json").write_text(
        json.dumps(protected, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    if case is not None:
        (out / "audited-case.json").write_text(
            json.dumps(case, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
        )
    summary = {
        "status": status,
        "structural_episodes": structural["episodes"],
        "visible_pairs": structural["visible_pairs"],
        "matched_input_checks": structural["matched_input_checks"],
        "declared_rival_certificates": structural["declared_rival_certificates"],
        "public_turn_checks": structural["public_turn_checks"],
        "protected_racket_evaluations": protected["protected_racket_evaluations"],
        "causal_output_changed": protected["causal_output_changed"],
        "failures": structural["failures"] + protected["failures"],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-count", type=int, default=16)
    args = parser.parse_args()
    return 0 if run(args.out, args.seed_count)["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
