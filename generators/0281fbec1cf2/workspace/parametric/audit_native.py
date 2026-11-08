"""Protected-Racket teaching audit and causal witness for 0281fbec1cf2."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import normalize_grid

TASK_ID = "0281fbec1cf2"
SCHEMA = "arcpuzzles-parametric-self-audit-v1"
_HOME = Path(__file__).resolve().parent

_TARGET_PICK = "(target (pick-max enclosed length))"
_TARGET_COLOR = "(paint-color (at g5 (fst marker) (snd marker)))"
_FINAL = "(recolor-cells g5 target paint-color))))"

_SKIP_A = r'''(rule! (lambda (g)
  (let* ((markers (filter (lambda (p) (let ((v (at g (fst p) (snd p)))) (and (not (zero? v)) (!= v 2)))) (grid-positions g)))
         (regions (find-0-regions g 0))
         (enclosed (filter (lambda (region)
                             (not (any? (lambda (p)
                                          (or (= (fst p) 0) (= (fst p) (- h 1))
                                              (= (snd p) 0) (= (snd p) (- w 1))))
                                        region)))
                           regions)))
    (if (null? enclosed)
        g
        (let* ((target (pick-max enclosed length))
               (marker (find-first (lambda (m)
                                     (any? (lambda (d)
                                             (member (list (+ (fst m) (fst d))
                                                           (+ (snd m) (snd d)))
                                                     target))
                                           cardinal-deltas))
                                   markers))
               (paint-color (at g (fst marker) (snd marker))))
          (recolor-cells g target paint-color))))))'''


def _load_adjacent(filename: str) -> ModuleType:
    path = (_HOME / filename).resolve()
    if path.parent != _HOME or not path.is_file():
        raise ValueError(f"missing adjacent audit resource: {filename}")
    name = "_audit_0281fbec1cf2_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent audit resource: {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_ADAPTER = _load_adjacent("adapter.py")
_FAMILY = _load_adjacent("native_family.py")


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"cannot materialize {label}: expected one replacement site")
    changed = source.replace(old, new, 1)
    if changed == source:
        raise AssertionError(f"{label} did not change the source")
    return changed


def _rivals(finish: str) -> dict[str, str]:
    canonical = _ADAPTER.program({"finish": "rays_only"})
    alternate = _ADAPTER.program({"finish": "largest_pocket"})
    chosen = canonical if finish == "rays_only" else alternate
    opposite = alternate if finish == "rays_only" else canonical
    smallest = _replace_once(alternate, _TARGET_PICK,
                             "(target (pick-min enclosed length))", "smallest pocket")
    first = _replace_once(alternate, _TARGET_PICK,
                          "(target (first enclosed))", "first pocket")
    fixed = _replace_once(alternate, _TARGET_COLOR,
                          "(paint-color 4)", "fixed color")
    all_pockets = _replace_once(
        alternate,
        _FINAL,
        "(reduce (lambda (out region) (recolor-cells out region paint-color)) g5 enclosed))))",
        "fill every pocket",
    )
    return {
        "opposite_finish": opposite,
        "smallest_pocket": smallest,
        "first_enclosed_pocket": first,
        "largest_fixed_color_4": fixed,
        "fill_all_pockets": all_pockets,
    }


def _literal(grid: Any) -> str:
    value = normalize_grid(grid)
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in value) + ")"


def _execute(bridge: RacketBridge, cache: dict[str, str], program: str,
             grid: Any) -> list[list[int]]:
    callable_source = cache.setdefault(program, wrap_rule(program))
    return normalize_grid(bridge.eval_text(f"({callable_source} {_literal(grid)})"))


def _counterexample(pairs: list[dict[str, Any]], chosen: list[Any], rival: list[Any],
                    demos: int) -> dict[str, Any]:
    for index, (pair, expected, actual) in enumerate(zip(pairs, chosen, rival, strict=True)):
        if expected != actual:
            return {
                "split": "train" if index < demos else "test",
                "index": index if index < demos else index - demos,
                "input": deepcopy(pair["input"]),
                "chosen_output": deepcopy(expected),
                "rival_output": deepcopy(actual),
            }
    raise AssertionError("rival had no counterexample")


def audit(seed: int = 0) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer; bool is forbidden")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    demos, queries = 2, 4
    rows: list[dict[str, Any]] = []
    evaluations = 0
    with RacketBridge() as bridge:
        identity = deepcopy(bridge.runtime_identity)
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("self-audit requires protected Racket")
        cache: dict[str, str] = {}
        for finish in _FAMILY.FINISHES:
            settings = {"finish": finish}
            episode = _ADAPTER.generate(seed, settings, demos, queries)
            pairs = [*episode["train"], *episode["test"]]
            chosen_program = _ADAPTER.program(settings)
            chosen_outputs = [_execute(bridge, cache, chosen_program, pair["input"])
                              for pair in pairs]
            evaluations += len(pairs)
            chosen_matches = all(output == pair["output"]
                                 for output, pair in zip(chosen_outputs, pairs, strict=True))
            rival_rows: dict[str, Any] = {}
            for name, rival_program in _rivals(finish).items():
                rival_outputs = [_execute(bridge, cache, rival_program, pair["input"])
                                 for pair in pairs]
                evaluations += len(pairs)
                demo_matches = [output == chosen_outputs[index]
                                for index, output in enumerate(rival_outputs[:demos])]
                query_matches = [output == chosen_outputs[demos + index]
                                 for index, output in enumerate(rival_outputs[demos:])]
                rival_rows[name] = {
                    "program_sha256": hashlib.sha256(rival_program.encode()).hexdigest(),
                    "demo_matches": demo_matches,
                    "query_matches": query_matches,
                    "fits_demonstrations": all(demo_matches),
                    "query_differs": not all(query_matches),
                    "counterexample": _counterexample(pairs, chosen_outputs, rival_outputs, demos),
                }
            rows.append({
                "settings": settings,
                "chosen_program_sha256": hashlib.sha256(chosen_program.encode()).hexdigest(),
                "chosen_labels_match_racket": chosen_matches,
                "rivals": rival_rows,
            })
    passed = all(
        row["chosen_labels_match_racket"]
        and all(not rival["fits_demonstrations"] and rival["query_differs"]
                for rival in row["rivals"].values())
        for row in rows
    )
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "status": "pass" if passed else "fail",
        "scope": {
            "seed": seed,
            "demos": demos,
            "queries": queries,
            "settings": len(rows),
            "rivals_per_setting": 5,
        },
        "racket": identity,
        "racket_evaluations": evaluations,
        "settings": rows,
        "limitation": "Finite audit of five named rivals on one matched-input seed; not a proof of universal uniqueness.",
    }


def causal_witness(seed: int = 0) -> dict[str, Any]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative plain integer")
    settings = {"finish": "largest_pocket"}
    episode = _ADAPTER.generate(seed, settings, 2, 4)
    grid = episode["test"][0]["input"]
    chosen_program = _ADAPTER.program(settings)
    with RacketBridge() as bridge:
        identity = deepcopy(bridge.runtime_identity)
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("causal witness requires protected Racket")
        cache: dict[str, str] = {}
        chosen_output = _execute(bridge, cache, chosen_program, grid)
        counterfactual_output = _execute(bridge, cache, _SKIP_A, grid)
    facts = _FAMILY.analyze_scene(grid)
    if chosen_output == counterfactual_output:
        raise AssertionError("skip-A counterfactual did not change the final output")
    return {
        "schema": "arcpuzzles-parametric-causal-witness-v1",
        "task_id": TASK_ID,
        "status": "reviewer_replayed",
        "setting": settings,
        "seed": seed,
        "query_index": 0,
        "step_a": "canonical blocker-aware red-ray expansion",
        "intermediate": "expanded grid whose red walls create enclosed zero pockets",
        "step_b": "select the unique largest enclosed zero pocket and fill it with its adjacent marker color",
        "why_b_depends_on_a": "The target zero component is not enclosed in the input; Stage A paints the red side walls that make it a bounded component for Stage B.",
        "ablation": "skip Stage A and run the same pocket-selection/fill logic directly on the original input, returning the input when no enclosed pocket exists",
        "input": deepcopy(grid),
        "stage_a_output": facts["stage_a"],
        "target_pocket": facts["target_pocket"],
        "target_marker": facts["target_marker"],
        "chosen_program": chosen_program,
        "chosen_program_sha256": hashlib.sha256(chosen_program.encode()).hexdigest(),
        "counterfactual_program": _SKIP_A,
        "counterfactual_program_sha256": hashlib.sha256(_SKIP_A.encode()).hexdigest(),
        "chosen_output": chosen_output,
        "counterfactual_output": counterfactual_output,
        "racket": identity,
    }


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report = audit(args.seed)
    witness = causal_witness(args.seed)
    _write(args.out_dir / "self-audit.json", report)
    _write(args.out_dir / "causal-witness.json", witness)
    print(json.dumps({
        "status": report["status"],
        "audit": str(args.out_dir / "self-audit.json"),
        "witness": str(args.out_dir / "causal-witness.json"),
        "racket_evaluations": report["racket_evaluations"] + 2,
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
