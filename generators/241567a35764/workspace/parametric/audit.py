#!/usr/bin/env python3
"""Bounded self-audit for the 241567a35764 parametric family.

Checks matched-input deterministic episodes, finite demonstration-only shortcut
rivals, sequential public projection, meaningful 30x30 coverage, and selected
labels/counterfactuals through protected Racket.  The retained evidence is
private authoring evidence and grants no approval, acceptance, or training use.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "241567a35764"
HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
DEMO_COUNTS = (2, 3, 6)
QUERY_COUNT = 4


def _load_adapter():
    path = HOME / "adapter.py"
    name = "_241567a35764_parametric_audit_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
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


def _rotation_only_template(grid: list[list[int]]) -> list[tuple[int, int]]:
    shape = ADAPTER.raw_template(grid)
    flat = [value for row in grid for value in row]
    controls = [color for color in (2, 3, 4) if color in flat]
    if len(controls) != 1:
        raise ValueError("expected one control")
    for _ in range({2: 0, 3: 1, 4: 2}[controls[0]]):
        shape = ADAPTER._rotate(shape)
    return shape


def _backward_only(grid: list[list[int]], shape: list[tuple[int, int]]) -> list[list[int]]:
    start, _nxt, delta = ADAPTER._markers(grid)
    anchors = [start] + ADAPTER._anchors(shape, start, delta, len(grid), len(grid[0]), -1)
    return ADAPTER._paint(shape, anchors, len(grid), len(grid[0]))


def rival_outputs(grid: list[list[int]], mode: str) -> dict[str, list[list[int]]]:
    shape = ADAPTER.transformed_template(grid)
    other = "bidirectional" if mode == "forward" else "forward"
    return {
        "opposite_direction": ADAPTER.solve(grid, other),
        "untransformed_template": ADAPTER.solve_with_shape(grid, mode, ADAPTER.raw_template(grid)),
        "ignore_flip_control": ADAPTER.solve_with_shape(grid, mode, _rotation_only_template(grid)),
        "stamp_once": ADAPTER.stamp_once(grid, shape),
        "backward_only": _backward_only(grid, shape),
        "constant_black": [[0 for _ in row] for row in grid],
    }


def _support():
    runtime = ROOT / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    import reviewer_support
    if Path(reviewer_support.__file__).resolve() != (runtime / "reviewer_support.py").resolve():
        raise RuntimeError("public projection did not use this checkout's reviewer_support")
    return reviewer_support


def _public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    visible = json.loads(_support().public_challenge_bytes(episode))
    if type(query_index) is not int or not 0 <= query_index < len(visible["test"]):
        raise ValueError("query_index must be an exact in-range integer")
    return {"train": copy.deepcopy(visible["train"]),
            "test": [copy.deepcopy(visible["test"][query_index])]}


def _public_checks(episode: dict[str, Any]) -> int:
    support = _support()
    raw = support.public_challenge_bytes(episode)
    visible = json.loads(raw)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert support.public_challenge_id(episode) == hashlib.sha256(raw).hexdigest()

    private = copy.deepcopy(episode)
    private.update({"seed": -1, "settings": {"path_mode": "PRIVATE"},
                    "program_solution": "PRIVATE", "query_total": 999})
    for pair in private["test"]:
        pair["output"] = [[9]]
        pair["private_hint"] = "PRIVATE"
    assert support.public_challenge_bytes(private) == raw

    single = {"train": copy.deepcopy(episode["train"]),
              "test": [copy.deepcopy(episode["test"][0])],
              "program_solution": episode["program_solution"]}
    assert _public_turn(episode, 0) == _public_turn(single, 0)
    changed_later = copy.deepcopy(episode)
    for pair in changed_later["test"][1:]:
        pair["input"] = [[9]]
    assert _public_turn(changed_later, 0) == _public_turn(episode, 0)

    for index in range(len(episode["test"])):
        turn = _public_turn(episode, index)
        assert set(turn) == {"train", "test"}
        assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}
    return len(episode["test"])


def _stress_check(pair: dict[str, Any]) -> None:
    grid, output = pair["input"], pair["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert (len(output), len(output[0])) == (30, 30)
    cells = [(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == 9]
    assert len(cells) >= 24
    assert max(r for r, _ in cells) - min(r for r, _ in cells) >= 14
    assert max(c for _, c in cells) - min(c for _, c in cells) >= 14
    assert len({(r >= 15, c >= 15) for r, c in cells}) >= 3


def structural_audit(seed_count: int = 16) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 10_000:
        raise ValueError("seed_count must be an exact integer in 1..10000")
    failures: list[dict[str, Any]] = []
    episodes = visible_pairs = matched = prefix = certificates = turns = stress = 0
    rows: list[dict[str, Any]] = []

    for seed in range(seed_count):
        for demos in DEMO_COUNTS:
            by_mode: dict[str, dict[str, Any]] = {}
            for mode in ADAPTER.PATH_MODES:
                context = {"seed": seed, "demos": demos, "path_mode": mode}
                try:
                    episode = ADAPTER.generate(seed, {"path_mode": mode}, demos, QUERY_COUNT)
                    by_mode[mode] = episode
                    episodes += 1
                    pairs = episode["train"] + episode["test"]
                    visible_pairs += len(pairs)
                    assert len(episode["train"]) == demos and len(episode["test"]) == QUERY_COUNT
                    assert episode["program_solution"] == ADAPTER.program({"path_mode": mode})
                    keys = [_grid_key(pair["input"]) for pair in pairs]
                    assert len(keys) == len(set(keys)), "duplicate visible input"
                    assert all(pair["output"] == ADAPTER.solve(pair["input"], mode) for pair in pairs)
                    assert all(ADAPTER.forward_stamp_count(pair["input"]) >= 2 for pair in pairs)
                    assert all(ADAPTER.backward_stamp_count(pair["input"]) >= 1 for pair in pairs)

                    minimum = ADAPTER.generate(seed, {"path_mode": mode}, 2, QUERY_COUNT)
                    one = ADAPTER.generate(seed, {"path_mode": mode}, demos, 1)
                    assert episode["train"][:2] == minimum["train"]
                    assert episode["test"] == minimum["test"]
                    assert one["train"] == episode["train"]
                    assert one["test"] == episode["test"][:1]
                    prefix += 1
                    turns += _public_checks(episode)
                    _stress_check(episode["test"][3])
                    stress += 1

                    names = sorted(rival_outputs(episode["train"][0]["input"], mode))
                    surviving: list[str] = []
                    dangerous: list[str] = []
                    for name in names:
                        demo_predictions = [rival_outputs(pair["input"], mode)[name]
                                            for pair in episode["train"]]
                        if demo_predictions == [pair["output"] for pair in episode["train"]]:
                            surviving.append(name)
                            query_predictions = [rival_outputs(pair["input"], mode)[name]
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

            if set(by_mode) == set(ADAPTER.PATH_MODES):
                first = by_mode[ADAPTER.PATH_MODES[0]]
                second = by_mode[ADAPTER.PATH_MODES[1]]
                left = [pair["input"] for pair in first["train"] + first["test"]]
                right = [pair["input"] for pair in second["train"] + second["test"]]
                if left != right:
                    failures.append({"seed": seed, "demos": demos,
                                     "error": "settings did not receive matched visible inputs"})
                else:
                    matched += 1

    return {
        "schema": "arcpuzzles-241567a35764-structural-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "seed_count": seed_count,
        "seed_range": [0, seed_count - 1],
        "settings": [{"path_mode": value} for value in ADAPTER.PATH_MODES],
        "demo_counts": list(DEMO_COUNTS),
        "queries": QUERY_COUNT,
        "episodes": episodes,
        "visible_pairs": visible_pairs,
        "matched_input_checks": matched,
        "prefix_checks": prefix,
        "declared_rival_certificates": certificates,
        "public_turn_checks": turns,
        "stress_30x30_checks": stress,
        "rows": rows,
        "failures": failures,
        "scope": (
            "Finite deterministic Python sweep over declared settings, demo prefixes, public projection, "
            "30x30 path stress, and named plausible rivals. It is not universal uniqueness evidence."
        ),
    }


def wrong_intermediate_program() -> str:
    """Counterfactual: skip control-derived transform, then stamp raw shape both ways."""
    return """(rule!
 (lambda (g)
   (let ()
     (define (cell<? a b)
       (or (< (first a) (first b))
           (and (= (first a) (first b)) (< (second a) (second b)))))
     (define (norm cells) (sort (normalize-cells cells) cell<?))
     (define wrong-shape (norm (find-color g 1)))
     (define start (first (find-color g 7)))
     (define nxt (first (find-color g 8)))
     (define dr (- (first nxt) (first start)))
     (define dc (- (second nxt) (second start)))
     (define (stamp-direction out ar ac step-r step-c)
       (let loop ((ar ar) (ac ac) (out out))
         (let ((placed (map (lambda (p) (list (+ ar (first p)) (+ ac (second p)))) wrong-shape)))
           (if (all? (lambda (p) (pos-in-bounds? p (rows g) (cols g))) placed)
               (loop (+ ar step-r) (+ ac step-c) (paint-cells out placed 9))
               out))))
     (define forward
       (stamp-direction (empty-grid (rows g) (cols g) 0)
                        (first start) (second start) dr dc))
     (stamp-direction forward
                      (- (first start) dr) (- (second start) dc)
                      (- dr) (- dc)))))"""


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def protected_audit() -> tuple[dict[str, Any], dict[str, Any] | None]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    selected_seeds = (0, 17)
    selected_demos = (2, 6)
    failures: list[dict[str, Any]] = []
    evaluations = 0
    sources = {mode: ADAPTER.program({"path_mode": mode}) for mode in ADAPTER.PATH_MODES}
    counterfactual = wrong_intermediate_program()
    wrapped = {name: wrap_rule(source) for name, source in {**sources, "counterfactual": counterfactual}.items()}
    causal_case = None

    with RacketBridge(max_calls_before_restart=256) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket backend required")
        for seed in selected_seeds:
            for demos in selected_demos:
                for mode in ADAPTER.PATH_MODES:
                    episode = ADAPTER.generate(seed, {"path_mode": mode}, demos, QUERY_COUNT)
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = bridge.eval_text(f"({wrapped[mode]} {_literal(pair['input'])})")
                            evaluations += 1
                            if actual != pair["output"]:
                                failures.append({"seed": seed, "demos": demos, "path_mode": mode,
                                                 "split": split, "index": index,
                                                 "error": "protected Racket label differs from adapter claim"})
                    if mode == "bidirectional" and causal_case is None:
                        for split in ("test", "train"):
                            for index, pair in enumerate(episode[split]):
                                alternative = bridge.eval_text(
                                    f"({wrapped['counterfactual']} {_literal(pair['input'])})"
                                )
                                evaluations += 1
                                if alternative != pair["output"]:
                                    causal_case = {
                                        "settings": {"path_mode": mode},
                                        "program": sources[mode],
                                        "input": pair["input"],
                                        "output": pair["output"],
                                        "counterfactual_program": counterfactual,
                                        "counterfactual_output": alternative,
                                        "intermediate_value": ADAPTER.transformed_template(pair["input"]),
                                        "counterfactual_intermediate": ADAPTER.raw_template(pair["input"]),
                                        "ablation": "skip_a",
                                        "source_episode": {"seed": seed, "demos": demos,
                                                           "split": split, "pair_index": index},
                                    }
                                    break
                            if causal_case is not None:
                                break
        if causal_case is None:
            failures.append({"error": "no protected causal case changed the final output"})

    report = {
        "schema": "arcpuzzles-241567a35764-protected-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "racket": identity,
        "seeds": list(selected_seeds),
        "demo_counts": list(selected_demos),
        "settings": [{"path_mode": value} for value in ADAPTER.PATH_MODES],
        "queries": QUERY_COUNT,
        "protected_racket_evaluations": evaluations,
        "causal_output_changed": causal_case is not None,
        "failures": failures,
        "scope": "Selected finite labels and one skip-transform counterfactual executed through protected Racket; no owner acceptance.",
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
    for filename, value in (("structural-audit.json", structural),
                            ("protected-racket-audit.json", protected)):
        (out / filename).write_text(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
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
        "stress_30x30_checks": structural["stress_30x30_checks"],
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
