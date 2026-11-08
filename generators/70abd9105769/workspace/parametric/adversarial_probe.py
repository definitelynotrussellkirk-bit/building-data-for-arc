#!/usr/bin/env python3
"""Protected-Racket adversarial probe for the 70abd9105769 family.

Selected labels and complete wrong Racket programs are executed through the
protected backend.  The probe fails if any rival survives the minimum lesson
and retains the first concrete input/expected/rival triple for every attacked
shortcut.  Future authoring agents can extend ``racket_rivals`` without
changing the evidence format.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_70abd9105769_probe_prototype", HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

_HELPERS = r"""
   (define (nonzero-colors grid)
     (filter (lambda (color) (not (= color 0))) (grid-colors grid)))
   (define (objs-color grid color)
     (filter (lambda (obj) (= (obj-color obj) color)) (objects grid 0)))
   (define (bbox< a b)
     (cond ((not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b)))
           ((not (= (obj-c1 a) (obj-c1 b))) (< (obj-c1 a) (obj-c1 b)))
           ((not (= (obj-r2 a) (obj-r2 b))) (< (obj-r2 a) (obj-r2 b)))
           (else (< (obj-c2 a) (obj-c2 b)))))
   (define (size-desc< a b)
     (if (= (obj-size a) (obj-size b)) (bbox< a b) (> (obj-size a) (obj-size b))))
   (define (bottom-right-desc< a b)
     (cond ((not (= (obj-r2 a) (obj-r2 b))) (> (obj-r2 a) (obj-r2 b)))
           ((not (= (obj-c2 a) (obj-c2 b))) (> (obj-c2 a) (obj-c2 b)))
           ((not (= (obj-r1 a) (obj-r1 b))) (> (obj-r1 a) (obj-r1 b)))
           (else (> (obj-c1 a) (obj-c1 b)))))
   (define (center-grid grid)
     (for/fold ([out (empty-grid (rows grid) (cols grid) 0)])
               ([obj (in-list (objects grid 0))])
       (let* ([bb (obj-bbox obj)]
              [h (+ 1 (- (third bb) (first bb)))]
              [w (+ 1 (- (fourth bb) (second bb)))])
         (if (and (= h w) (= (modulo h 2) 1))
             (set-cell out
                       (+ (first bb) (quotient h 2))
                       (+ (second bb) (quotient w 2))
                       (obj-color obj))
             out))))
   (define (color-count-desc< grid a b)
     (let ([ca (length (find-color grid a))]
           [cb (length (find-color grid b))])
       (if (= ca cb) (< a b) (> ca cb))))
   (define (color-count-asc< grid a b)
     (let ([ca (length (find-color grid a))]
           [cb (length (find-color grid b))])
       (if (= ca cb) (< a b) (< ca cb))))
   (define (all-nonzero-cells grid)
     (apply append
            (map (lambda (color) (find-color grid color))
                 (nonzero-colors grid))))
   (define (frame-zero grid cells color)
     (let* ([bb (bbox-of-cells cells)]
            [r1 (first bb)] [c1 (second bb)]
            [r2 (third bb)] [c2 (fourth bb)])
       (for*/fold ([out grid])
                  ([r (in-range r1 (+ r2 1))]
                   [c (in-range c1 (+ c2 1))])
         (if (and (or (= r r1) (= r r2) (= c c1) (= c c2))
                  (= (at out r c) 0))
             (set-cell out r c color)
             out))))
   (define (frame-all grid cells color)
     (let* ([bb (bbox-of-cells cells)]
            [r1 (first bb)] [c1 (second bb)]
            [r2 (third bb)] [c2 (fourth bb)])
       (for*/fold ([out grid])
                  ([r (in-range r1 (+ r2 1))]
                   [c (in-range c1 (+ c2 1))])
         (if (or (= r r1) (= r r2) (= c c1) (= c c2))
             (set-cell out r c color)
             out))))
   (define (fill-zero grid cells color)
     (let* ([bb (bbox-of-cells cells)]
            [r1 (first bb)] [c1 (second bb)]
            [r2 (third bb)] [c2 (fourth bb)])
       (for*/fold ([out grid])
                  ([r (in-range r1 (+ r2 1))]
                   [c (in-range c1 (+ c2 1))])
         (if (= (at out r c) 0) (set-cell out r c color) out))))
   (define (corners-zero grid cells color)
     (let* ([bb (bbox-of-cells cells)]
            [r1 (first bb)] [c1 (second bb)]
            [r2 (third bb)] [c2 (fourth bb)]
            [corners (list (list r1 c1) (list r1 c2)
                           (list r2 c1) (list r2 c2))])
       (for/fold ([out grid]) ([pos (in-list corners)])
         (if (= (at out (first pos) (second pos)) 0)
             (set-cell out (first pos) (second pos) color)
             out))))
"""


def _rule(body: str) -> str:
    return "(rule!\n (let ((dummy 0))\n" + _HELPERS + "\n" + body + "))"


def _canonical_object_corner(which: str) -> str:
    assert which in {"top_left", "bottom_right"}
    row = "(obj-r1 obj)" if which == "top_left" else "(obj-r2 obj)"
    col = "(obj-c1 obj)" if which == "top_left" else "(obj-c2 obj)"
    return _rule(
        "   (for/fold ([out (empty-grid (rows g) (cols g) 0)])\n"
        "             ([obj (in-list (objects g 0))])\n"
        f"     (set-cell out {row} {col} (obj-color obj)))"
    )


def _one_component_per_color(kind: str) -> str:
    if kind == "first":
        center = (
            "(let* ([obj (first (sort (objs-color g color) bbox<))]\n"
            "              [bb (obj-bbox obj)])\n"
            "         (list (+ (first bb) (quotient (- (third bb) (first bb)) 2))\n"
            "               (+ (second bb) (quotient (- (fourth bb) (second bb)) 2))))"
        )
    elif kind == "largest":
        center = (
            "(let* ([obj (first (sort (objs-color g color) size-desc<))]\n"
            "              [bb (obj-bbox obj)])\n"
            "         (list (+ (first bb) (quotient (- (third bb) (first bb)) 2))\n"
            "               (+ (second bb) (quotient (- (fourth bb) (second bb)) 2))))"
        )
    elif kind == "combined":
        center = (
            "(let ([bb (bbox-of-cells (find-color g color))])\n"
            "         (list (quotient (+ (first bb) (third bb)) 2)\n"
            "               (quotient (+ (second bb) (fourth bb)) 2)))"
        )
    else:
        raise AssertionError(kind)
    return _rule(
        "   (for/fold ([out (empty-grid (rows g) (cols g) 0)])\n"
        "             ([color (in-list (nonzero-colors g))])\n"
        f"     (let ([pos {center}])\n"
        "       (set-cell out (first pos) (second pos) color)))"
    )


def _stage_rule(
    selector: str,
    *,
    operation: str = "frame-zero",
    frame_color: int = 9,
) -> str:
    return _rule(
        "   (let* ([stage (center-grid g)]\n"
        "          [colors (nonzero-colors stage)]\n"
        f"          [target-color {selector}])\n"
        f"     ({operation} stage (find-color stage target-color) {frame_color}))"
    )


def racket_rivals() -> dict[str, dict[str, str]]:
    canonical = {
        "blank": _rule("   (empty-grid (rows g) (cols g) 0)"),
        "identity": _rule("   g"),
        "first_component_per_color": _one_component_per_color("first"),
        "largest_component_per_color": _one_component_per_color("largest"),
        "combined_bbox_center_per_color": _one_component_per_color("combined"),
        "top_left_of_each_square": _canonical_object_corner("top_left"),
        "bottom_right_of_each_square": _canonical_object_corner("bottom_right"),
    }
    majority = {
        "canonical_only": _rule("   (center-grid g)"),
        "skip_stage_a": prototype.skip_stage_a_program(),
        "raw_pixel_majority_on_centers": _stage_rule(
            "(first (sort (nonzero-colors g) "
            "(lambda (a b) (color-count-desc< g a b))))"
        ),
        "frame_all_centers": _rule(
            "   (let ([stage (center-grid g)])\n"
            "     (frame-zero stage (all-nonzero-cells stage) 9))"
        ),
        "least_frequent_center_color": _stage_rule(
            "(first (sort colors (lambda (a b) (color-count-asc< stage a b))))"
        ),
        "second_most_frequent_center_color": _stage_rule(
            "(list-ref (sort colors (lambda (a b) (color-count-desc< stage a b))) 1)"
        ),
        "smallest_numeric_color": _stage_rule("(first (sort colors <))"),
        "largest_numeric_color": _stage_rule("(first (sort colors >))"),
        "largest_input_square_color": _stage_rule(
            "(obj-color (first (sort (objects g 0) size-desc<)))"
        ),
        "top_left_input_square_color": _stage_rule(
            "(obj-color (first (sort (objects g 0) bbox<)))"
        ),
        "bottom_right_input_square_color": _stage_rule(
            "(obj-color (first (sort (objects g 0) bottom-right-desc<)))"
        ),
        "last_top_left_anchor_color": _stage_rule(
            "(obj-color (first (sort (objects g 0) (lambda (a b) (bbox< b a)))))"
        ),
        "fill_target_bbox": _stage_rule(
            "(first (sort colors (lambda (a b) (color-count-desc< stage a b))))",
            operation="fill-zero",
        ),
        "target_bbox_corners_only": _stage_rule(
            "(first (sort colors (lambda (a b) (color-count-desc< stage a b))))",
            operation="corners-zero",
        ),
        "overwrite_target_centers": _stage_rule(
            "(first (sort colors (lambda (a b) (color-count-desc< stage a b))))",
            operation="frame-all",
        ),
        "frame_color_8": _stage_rule(
            "(first (sort colors (lambda (a b) (color-count-desc< stage a b))))",
            frame_color=8,
        ),
    }
    return {"canonical": canonical, "majority_frame": majority}


def _exact_int(value: Any, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer; bool is forbidden")
    return value


def run(
    seeds: Iterable[int] = (0, 1, 2),
    *,
    demos: int = 2,
    include_queries: bool = True,
) -> dict[str, Any]:
    seed_list = list(seeds)
    if not seed_list:
        raise ValueError("seeds must be nonempty")
    for seed in seed_list:
        _exact_int(seed, "seed")
    _exact_int(demos, "demos")
    if not 2 <= demos <= 6:
        raise ValueError("demos must be in 2..6")
    if type(include_queries) is not bool:
        raise ValueError("include_queries must be bool")

    banks = racket_rivals()
    retained: dict[str, dict[str, Any]] = {}
    survivor_counts: Counter[str] = Counter()
    evaluations = 0
    label_replays = 0
    episodes = 0
    max_shape = [0, 0]

    with prototype.RacketRunner() as execute:
        runtime = execute.identity
        for seed in seed_list:
            for setting in prototype.SETTINGS:
                mode = setting["mode"]
                episode = prototype.generate(seed, setting, demos=demos, queries=4)
                episodes += 1
                replay_pairs = episode["train"] + (
                    episode["test"] if include_queries else []
                )
                for pair_index, pair in enumerate(replay_pairs):
                    actual = execute(episode["program_solution"], pair["input"])
                    evaluations += 1
                    label_replays += 1
                    if actual != pair["output"]:
                        raise AssertionError(
                            f"selected Racket rule disagrees: {seed=} {mode=} {pair_index=}"
                        )
                    max_shape[0] = max(max_shape[0], len(pair["input"]))
                    max_shape[1] = max(max_shape[1], len(pair["input"][0]))

                for name, source in sorted(banks[mode].items()):
                    survived = True
                    for demo_index, pair in enumerate(episode["train"]):
                        rival = execute(source, pair["input"])
                        evaluations += 1
                        if rival != pair["output"]:
                            survived = False
                            key = f"{mode}:{name}"
                            retained.setdefault(
                                key,
                                {
                                    "mode": mode,
                                    "rival": name,
                                    "seed": seed,
                                    "demo_index": demo_index,
                                    "input": pair["input"],
                                    "expected": pair["output"],
                                    "rival_output": rival,
                                    "input_sha256": prototype.grid_sha256(pair["input"]),
                                    "expected_sha256": prototype.grid_sha256(pair["output"]),
                                    "rival_sha256": prototype.grid_sha256(rival),
                                    "rival_program_sha256": hashlib.sha256(
                                        source.encode()
                                    ).hexdigest(),
                                },
                            )
                            break
                    if survived:
                        survivor_counts[f"{mode}:{name}"] += 1

    attacked = sum(len(bank) for bank in banks.values())
    missing_counterexamples = sorted(
        f"{mode}:{name}"
        for mode, bank in banks.items()
        for name in bank
        if f"{mode}:{name}" not in retained
    )
    status = "pass" if not survivor_counts and not missing_counterexamples else "fail"
    return {
        "status": status,
        "task_id": prototype.TASK_ID,
        "runtime": runtime,
        "seeds": seed_list,
        "demos": demos,
        "include_queries": include_queries,
        "episodes": episodes,
        "rivals_attacked": attacked,
        "rival_names": {mode: sorted(bank) for mode, bank in sorted(banks.items())},
        "evaluations": evaluations,
        "selected_label_replays": label_replays,
        "surviving_rivals": dict(sorted(survivor_counts.items())),
        "missing_counterexamples": missing_counterexamples,
        "retained_counterexamples": [retained[key] for key in sorted(retained)],
        "max_shape": max_shape,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--no-queries", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run(args.seeds, demos=args.demos, include_queries=not args.no_queries)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
