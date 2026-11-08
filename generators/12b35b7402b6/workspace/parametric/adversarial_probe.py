#!/usr/bin/env python3
"""Protected-Racket adversarial probe for the 12b35b7402b6 family.

The probe replays selected labels and executes a bank of complete but wrong
Racket rules against the minimum two demonstrations.  It fails if any wrong
rule survives an episode and retains exact input/expected/rival grids for the
first counterexample to every attacked rival.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_12b35b7402b6_probe_prototype", HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

_HELPERS = r"""
   (define (objs-color grid color)
     (filter (lambda (obj) (= (obj-color obj) color)) (objects grid 0)))
   (define (objs8-color grid color)
     (filter (lambda (obj) (= (obj-color obj) color)) (objects-8 grid 0)))
   (define (paint-obj grid obj color)
     (paint-cells grid (obj-cells obj) color))
   (define (bbox< a b)
     (cond ((not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b)))
           ((not (= (obj-c1 a) (obj-c1 b))) (< (obj-c1 a) (obj-c1 b)))
           ((not (= (obj-r2 a) (obj-r2 b))) (< (obj-r2 a) (obj-r2 b)))
           (else (< (obj-c2 a) (obj-c2 b)))))
   (define (bbox-desc< a b) (bbox< b a))
   (define (size-desc< a b)
     (if (= (obj-size a) (obj-size b)) (bbox< a b) (> (obj-size a) (obj-size b))))
   (define (size-asc< a b)
     (if (= (obj-size a) (obj-size b)) (bbox< a b) (< (obj-size a) (obj-size b))))
   (define (bbox-distance2 obj ref-r2 ref-c2)
     (let ((dr (- (+ (obj-r1 obj) (obj-r2 obj)) ref-r2))
           (dc (- (+ (obj-c1 obj) (obj-c2 obj)) ref-c2)))
       (+ (* dr dr) (* dc dc))))
"""


def _rule(body: str) -> str:
    return "(rule!\n (let ((dummy 0))\n" + _HELPERS + "\n" + body + "))"


def _blue_rule(target_expression: str) -> str:
    return _rule(
        "   (let* ((blues (objs-color g 1))\n"
        f"          (target {target_expression}))\n"
        "     (paint-obj g target 2))"
    )


def _stage_prefix() -> str:
    return r"""   (let* ((count5 (length (find-color g 5)))
          (blue-target
           (first (sort (filter (lambda (obj) (= (obj-size obj) count5))
                                (objs-color g 1)) bbox<)))
          (stage-a (paint-obj g blue-target 2))
"""


def _payload_by_size_rule(size_expression: str, *, red8: bool = False) -> str:
    # ``red8`` is used only to compute the key; payload objects remain ordinary
    # 4-connected monochrome objects, exactly as in the intended rule.
    red_source = "(objs8-color stage-a 2)" if red8 else "(objs-color stage-a 2)"
    body = _stage_prefix()
    body += f"          (reds {red_source})\n"
    body += f"          (key-size {size_expression})\n"
    body += r"""          (matches
           (sort (filter (lambda (obj) (= (obj-size obj) key-size))
                         (objs-color stage-a 8)) bbox<)))
     (if (= (length matches) 1)
         (paint-obj stage-a (first matches) 4)
         stage-a))"""
    return _rule(body)


def _payload_rank_rule(sorter: str, index_expression: str) -> str:
    body = _stage_prefix()
    body += (
        f"          (payload (list-ref (sort (objs-color stage-a 8) {sorter}) "
        f"{index_expression})))\n"
        "     (paint-obj stage-a payload 4))"
    )
    return _rule(body)


def _payload_marker_distance_rule(*, farthest: bool) -> str:
    comparison = ">" if farthest else "<"
    body = (
        "   (define marker-c2 (+ (min-of second (find-color g 5)) "
        "(max-of second (find-color g 5))))\n"
        "   (define (distance< a b)\n"
        "     (let ((da (bbox-distance2 a 0 marker-c2))\n"
        "           (db (bbox-distance2 b 0 marker-c2)))\n"
        f"       (if (= da db) (bbox< a b) ({comparison} da db))))\n"
    )
    body += _stage_prefix()
    body += (
        "          (payload (first (sort (objs-color stage-a 8) distance<))))\n"
        "     (paint-obj stage-a payload 4))"
    )
    return _rule(body)


def racket_rivals() -> dict[str, dict[str, str]]:
    canonical = {
        "gray_horizontal_span": _rule(
            r"""   (let* ((markers (find-color g 5))
          (span (+ 1 (- (max-of second markers) (min-of second markers))))
          (target (first (sort (filter (lambda (obj) (= (obj-size obj) span))
                                       (objs-color g 1)) bbox<))))
     (paint-obj g target 2))"""
        ),
        "largest_blue": _blue_rule("(first (sort blues size-desc<))"),
        "smallest_blue": _blue_rule("(first (sort blues size-asc<))"),
        "top_left_blue": _blue_rule("(first (sort blues bbox<))"),
        "bottom_right_blue": _blue_rule("(first (sort blues bbox-desc<))"),
    }
    linked = {
        "skip_stage_a": prototype.skip_stage_a_program(),
        "pre_stage_red_size": _payload_by_size_rule(
            "(obj-size (first (sort (objs-color g 2) size-desc<)))"
        ),
        "pre_stage_red_plus_one": _payload_by_size_rule(
            "(+ 1 (obj-size (first (sort (objs-color g 2) size-desc<))))"
        ),
        "pre_stage_red_plus_two": _payload_by_size_rule(
            "(+ 2 (obj-size (first (sort (objs-color g 2) size-desc<))))"
        ),
        "marker_plus_largest_touching_red": _payload_by_size_rule(
            "(+ count5 (obj-size (first (sort "
            "(filter (lambda (obj) (objects-touching? obj blue-target)) "
            "(objs-color g 2)) size-desc<))))"
        ),
        "marker_count_payload": _payload_by_size_rule("count5"),
        "marker_span_payload": _payload_by_size_rule(
            "(+ 1 (- (max-of second (find-color g 5)) (min-of second (find-color g 5))))"
        ),
        "eight_connectivity": _payload_by_size_rule(
            "(obj-size (first (sort reds size-desc<)))", red8=True
        ),
        "eight_connectivity_minus_one": _payload_by_size_rule(
            "(- (obj-size (first (sort reds size-desc<))) 1)", red8=True
        ),
        "target_bbox_area": _payload_by_size_rule(
            "(* (+ 1 (- (obj-r2 blue-target) (obj-r1 blue-target))) "
            "(+ 1 (- (obj-c2 blue-target) (obj-c1 blue-target))))"
        ),
        "global_red_count": _payload_by_size_rule(
            "(length (find-color stage-a 2))"
        ),
        "largest_azure": _payload_rank_rule("size-desc<", "0"),
        "smallest_azure": _payload_rank_rule("size-asc<", "0"),
        "second_largest_azure": _payload_rank_rule("size-desc<", "1"),
        "top_left_azure": _payload_rank_rule("bbox<", "0"),
        "bottom_right_azure": _payload_rank_rule("bbox-desc<", "0"),
        "nearest_marker_bbox_center": _payload_marker_distance_rule(farthest=False),
        "farthest_marker_bbox_center": _payload_marker_distance_rule(farthest=True),
    }
    return {"canonical": canonical, "linked_payload": linked}


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
                                    "rival_program_sha256": prototype.hashlib.sha256(
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
    status = (
        "pass"
        if not survivor_counts and not missing_counterexamples
        else "fail"
    )
    return {
        "status": status,
        "task_id": prototype.TASK_ID,
        "runtime": runtime,
        "seeds": seed_list,
        "demos": demos,
        "include_queries": include_queries,
        "episodes": episodes,
        "rivals_attacked": attacked,
        "rival_names": {
            mode: sorted(bank) for mode, bank in sorted(banks.items())
        },
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
    report = run(
        args.seeds, demos=args.demos, include_queries=not args.no_queries
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
