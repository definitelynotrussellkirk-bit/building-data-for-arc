#!/usr/bin/env python3
"""Bounded protected-Racket teaching audit for the half-fill relay family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_ID = "1a92a12bac06"
ROOT = HERE.parents[3]
SETTINGS = ({"mode": "half_only"}, {"mode": "largest_relay"})


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_audit_half_relay_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _top_program(canonical: str, *, ceil: bool = False) -> str:
    source = canonical
    if ceil:
        source = source.replace(
            "(half-h (quotient bar-h 2))",
            "(half-h (quotient (+ bar-h 1) 2))",
        )
    return source.replace(
        "(cyan-start (- r2 (- half-h 1))))",
        "(cyan-end (+ r1 (- half-h 1))))",
    ).replace(
        "(if (>= r cyan-start) (set-cell gr r c 8) gr)",
        "(if (<= r cyan-end) (set-cell gr r c 8) gr)",
    )


def _ceil_program(canonical: str) -> str:
    return canonical.replace(
        "(half-h (quotient bar-h 2))",
        "(half-h (quotient (+ bar-h 1) 2))",
    )


def _canvas_bottom_program(canonical: str) -> str:
    return canonical.replace(
        "(cyan-start (- r2 (- half-h 1))))",
        "(cyan-start (- h half-h)))",
    )


def _all_cyan_program(canonical: str) -> str:
    return canonical.replace(
        "(if (>= r cyan-start) (set-cell gr r c 8) gr)",
        "(set-cell gr r c 8)",
    )


def _relay_variant(base_program: str, *, selector: str = "largest",
                   all_red: bool = False, pixels_only: bool = False) -> str:
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped = wrap_rule(base_program)
    selectors = {
        "largest": "(pick-max cyan obj-size)",
        "smallest": "(pick-min cyan obj-size)",
        "leftmost": "(pick-min cyan (lambda (o) (min-list (map second (obj-cells o)))))",
        "rightmost": "(pick-max cyan (lambda (o) (max-list (map second (obj-cells o)))))",
    }
    chosen = selectors[selector]
    targets = "reds" if all_red else "(filter (lambda (o) (adjacent? o winner)) reds)"
    painter = "(paint-cells out (obj-cells o) 4)"
    if pixels_only:
        painter = "(paint-cells out (filter (lambda (p) (cell-touches? p winner)) (obj-cells o)) 4)"
    return f"""(rule! (lambda (g)
  (define (cell-touches? p b)
    (any? (lambda (d)
      (member (list (+ (first p) (first d)) (+ (second p) (second d)))
              (obj-cells b)))
      cardinal-deltas))
  (define (adjacent? a b)
    (any? (lambda (p) (cell-touches? p b)) (obj-cells a)))
  (define half ({wrapped} g))
  (define cyan (filter (lambda (o) (= (obj-color o) 8)) (objects half 0)))
  (if (null? cyan)
      half
      (let* ((winner {chosen})
             (reds (filter (lambda (o) (= (obj-color o) 2)) (objects half 0)))
             (targets {targets}))
        (reduce (lambda (out o) {painter}) half targets)))))"""


def _original_relay_variant(canonical: str, *, selector: str) -> str:
    """Choose a relay from the original scene, then follow it through step A."""
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped = wrap_rule(canonical)
    if selector == "smallest_relay":
        chosen = "(pick-min relay-candidates obj-size)"
    elif selector == "largest_red_mass":
        chosen = "(pick-max relay-candidates red-mass)"
    else:
        raise ValueError("unknown original-relay selector")
    return f"""(rule! (lambda (g)
  (define (cell-touches? p b)
    (any? (lambda (d)
      (member (list (+ (first p) (first d)) (+ (second p) (second d)))
              (obj-cells b)))
      cardinal-deltas))
  (define (adjacent? a b)
    (any? (lambda (p) (cell-touches? p b)) (obj-cells a)))
  (define original-reds
    (filter (lambda (o) (= (obj-color o) 2)) (objects g 0)))
  (define original-cyan
    (filter (lambda (o) (= (obj-color o) 8)) (objects g 0)))
  (define relay-candidates
    (filter (lambda (c)
      (any? (lambda (r) (adjacent? r c)) original-reds))
      original-cyan))
  (define (red-mass c)
    (reduce (lambda (total r) (+ total (obj-size r)))
            0
            (filter (lambda (r) (adjacent? r c)) original-reds)))
  (define half ({wrapped} g))
  (define post-cyan
    (filter (lambda (o) (= (obj-color o) 8)) (objects half 0)))
  (if (null? relay-candidates)
      half
      (let* ((chosen-original {chosen})
             (matches (filter
               (lambda (o)
                 (all? (lambda (p) (member p (obj-cells o)))
                       (obj-cells chosen-original)))
               post-cyan)))
        (if (null? matches)
            half
            (let* ((winner (first matches))
                   (reds (filter (lambda (o) (= (obj-color o) 2)) (objects half 0)))
                   (targets (filter (lambda (o) (adjacent? o winner)) reds)))
              (reduce (lambda (out o) (paint-cells out (obj-cells o) 4))
                      half
                      targets)))))))"""


def rival_programs(adapter, mode: str) -> dict[str, str]:
    if mode not in ("half_only", "largest_relay"):
        raise ValueError("unknown mode")
    canonical = adapter.program({"mode": "half_only"})
    top_floor = _top_program(canonical)
    bottom_ceil = _ceil_program(canonical)
    top_ceil = _top_program(canonical, ceil=True)
    if mode == "half_only":
        return {
            "other_setting": adapter.program({"mode": "largest_relay"}),
            "identity": "(rule! (lambda (g) g))",
            "top_floor": top_floor,
            "bottom_ceil": bottom_ceil,
            "top_ceil": top_ceil,
            "canvas_bottom": _canvas_bottom_program(canonical),
            "entire_red_bars": _all_cyan_program(canonical),
        }
    return {
        "other_setting": canonical,
        "wrong_intermediate": adapter.counterfactual_program(),
        "largest_original_red_mass": _original_relay_variant(
            canonical, selector="largest_red_mass"
        ),
        "smallest_original_relay": _original_relay_variant(
            canonical, selector="smallest_relay"
        ),
        "all_remaining_red": _relay_variant(canonical, all_red=True),
        "smallest_post_network": _relay_variant(canonical, selector="smallest"),
        "leftmost_post_network": _relay_variant(canonical, selector="leftmost"),
        "rightmost_post_network": _relay_variant(canonical, selector="rightmost"),
        "touching_pixels_only": _relay_variant(canonical, pixels_only=True),
        "top_half_then_rank": _relay_variant(top_floor),
        "ceil_half_then_rank": _relay_variant(bottom_ceil),
    }


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def run(out: Path) -> dict[str, Any]:
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"choose a fresh audit directory: {out}")
    out.mkdir(parents=True)
    adapter = _load_adapter()
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))

    from arcpuzzles.parametric_worker import evaluate_contract
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import public_challenge_bytes, public_challenge_id

    jobs = [
        {"seed": seed, "settings": deepcopy(setting), "demos": demos, "queries": 4}
        for setting in SETTINGS
        for seed in (0, 17)
        for demos in (2, 3, 6)
    ]
    execution = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    _write(out / "execution.private.json", execution)

    wrapped: dict[str, str] = {}
    evaluations = 0
    unresolved = []
    teaching = []
    identity = None

    with RacketBridge(max_calls_before_restart=256) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket backend required")

        def execute(source: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            evaluations += 1
            rule = wrapped.setdefault(source, wrap_rule(source))
            return bridge.eval_text(f"({rule} {_literal(grid)})")

        for episode_index, episode in enumerate(execution["episodes"]):
            mode = episode["settings"]["mode"]
            rows = []
            for name, source in rival_programs(adapter, mode).items():
                refutation = None
                for demo_index, pair in enumerate(episode["train"]):
                    rival = execute(source, pair["input"])
                    if rival != pair["output"]:
                        refutation = {
                            "demo_index": demo_index,
                            "input": pair["input"],
                            "reference_output": pair["output"],
                            "rival_output": rival,
                        }
                        break
                row = {
                    "name": name,
                    "program_sha256": _sha(source.encode()),
                    "status": "refuted_by_visible_demo" if refutation else "survives_demonstrations",
                }
                if refutation:
                    row["case"] = refutation
                else:
                    disagreements = []
                    for query_index, pair in enumerate(episode["test"]):
                        rival = execute(source, pair["input"])
                        if rival != pair["output"]:
                            disagreements.append(query_index)
                    row["query_disagreements"] = disagreements
                    unresolved.append({
                        "episode_index": episode_index,
                        "seed": episode["seed"],
                        "settings": episode["settings"],
                        "demos": len(episode["train"]),
                        "rival": name,
                        "query_disagreements": disagreements,
                    })
                rows.append(row)
            teaching.append({
                "episode_index": episode_index,
                "seed": episode["seed"],
                "settings": episode["settings"],
                "demos": len(episode["train"]),
                "rivals": rows,
            })

        causal_episode_index = next(
            i for i, episode in enumerate(execution["episodes"])
            if episode["settings"] == {"mode": "largest_relay"}
            and episode["seed"] == 0
            and len(episode["train"]) == 3
        )
        causal_episode = execution["episodes"][causal_episode_index]
        causal_pair = causal_episode["train"][0]
        counterfactual = adapter.counterfactual_program()
        counterfactual_output = execute(counterfactual, causal_pair["input"])
        state = adapter.relay_state(causal_pair["input"])
        if counterfactual_output == causal_pair["output"]:
            raise AssertionError("wrong-intermediate causal case did not change final output")
        counterfactual_record = {
            "episode_index": causal_episode_index,
            "split": "train",
            "pair_index": 0,
            "settings": causal_episode["settings"],
            "program": causal_episode["program"],
            "counterfactual_program": counterfactual,
            "input": causal_pair["input"],
            "intermediate_value": {
                "grid": state["intermediate"],
                "pre_largest_cells": state["pre_largest_cells"],
                "post_largest_cells": state["post_largest_cells"],
                "post_largest_size": state["post_largest_size"],
                "post_second_size": state["post_second_size"],
            },
            "output": causal_pair["output"],
            "counterfactual_output": counterfactual_output,
            "ablation": "wrong_intermediate",
        }
        _write(out / "counterfactual.private.json", counterfactual_record)

    _write(out / "teaching.private.json", teaching)

    public_dir = out / "public"
    public_dir.mkdir()
    export_map = []
    for episode_index, episode in enumerate(execution["episodes"]):
        if len(episode["train"]) != 3:
            continue
        turns = []
        for query_index in range(len(episode["test"])):
            view = adapter.public_turn(episode, query_index)
            raw = public_challenge_bytes(view)
            identifier = public_challenge_id(view)
            if identifier != _sha(raw):
                raise AssertionError("public identifier is not exact visible-byte SHA256")
            parsed = json.loads(raw)
            if (set(parsed) != {"train", "test"}
                    or len(parsed["test"]) != 1
                    or set(parsed["test"][0]) != {"input"}
                    or any(set(pair) != {"input", "output"} for pair in parsed["train"])):
                raise AssertionError("public turn contains private fields or count hints")

            altered = deepcopy(episode)
            altered["settings"] = {"private": "changed"}
            altered["program"] = "changed"
            for pair in altered["test"]:
                pair["output"] = [[9]]
            for pair in altered["test"][query_index + 1:]:
                pair["input"] = [[9]]
            if public_challenge_bytes(adapter.public_turn(altered, query_index)) != raw:
                raise AssertionError("public turn depends on private or future query data")

            relative = f"public/{identifier}.json"
            destination = out / relative
            if destination.exists():
                raise AssertionError("duplicate visible public turn")
            destination.write_bytes(raw)
            turns.append({
                "query_index": query_index,
                "public_file": relative,
                "public_id": identifier,
            })

        short = adapter.generate(episode["seed"], episode["settings"], 3, 1)
        if (public_challenge_bytes(adapter.public_turn(short, 0))
                != public_challenge_bytes(adapter.public_turn(episode, 0))):
            raise AssertionError("first turn differs between one-query and four-query generation")
        export_map.append({
            "episode_index": episode_index,
            "seed": episode["seed"],
            "settings": episode["settings"],
            "public_turns": turns,
            "checks": {
                "one_query_per_turn": True,
                "future_queries_invariant": True,
                "first_turn_single_vs_four_exact_bytes": True,
                "ids_hash_exact_visible_bytes": True,
            },
        })
    _write(out / "index.private.json", export_map)

    boundary = []
    for height, width in ((13, 14), (13, 30), (30, 14), (30, 30)):
        grid = adapter.sample_input(17, "test", 3, height=height, width=width)
        state = adapter.relay_state(grid)
        boundary.append({
            "height": height,
            "width": width,
            "nonzero_cells": sum(value != 0 for row in grid for value in row),
            "post_largest_size": state["post_largest_size"],
            "post_second_size": state["post_second_size"],
            "target_count": len(state["target_red_components"]),
        })
    _write(out / "boundary.private.json", boundary)

    summary = {
        "schema": "1a92a12bac06-half-relay-audit-v1",
        "status": "passed" if not unresolved else "failed",
        "task_id": TASK_ID,
        "jobs": len(jobs),
        "episodes": len(execution["episodes"]),
        "native_racket_evaluations": execution["racket_evaluations"],
        "extra_racket_evaluations": evaluations,
        "racket": identity,
        "rival_attempts": sum(len(row["rivals"]) for row in teaching),
        "unresolved": unresolved,
        "public_challenges": sum(len(row["public_turns"]) for row in export_map),
        "boundary": boundary,
        "source_sha256": {
            name: _sha((HERE / name).read_bytes())
            for name in ("adapter.py", "family.py", "canonical.rkt", "promotion.json", "audit.py")
        },
        "limits": (
            "Finite declared rivals and sampled seeds/counts only; no proof of universal "
            "uniqueness, learning benefit, owner acceptance, or training admission."
        ),
    }
    _write(out / "summary.private.json", summary)
    if unresolved:
        raise AssertionError(f"{len(unresolved)} finite rivals survived visible demonstrations")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = run(args.out)
    except Exception as exc:
        print(f"audit: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": summary["status"],
        "jobs": summary["jobs"],
        "rival_attempts": summary["rival_attempts"],
        "extra_racket_evaluations": summary["extra_racket_evaluations"],
        "public_challenges": summary["public_challenges"],
        "summary": str(args.out / "summary.private.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
