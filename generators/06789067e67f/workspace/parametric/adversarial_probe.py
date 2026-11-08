#!/usr/bin/env python3
"""Protected-Racket falsification probe for the 06789067e67f family.

The bank attacks the actual component sort, packing geometry, and sequential
rank stage.  Every wrong executable program must be rejected by the minimum
visible lesson; one concrete disagreement is retained for future regressions.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "06789067e67f"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_06789067e67f", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _comparator(mode: str) -> str | None:
    comparisons = {
        "canonical": """(lambda (a b)
          (cond [(not (= (first a) (first b))) (> (first a) (first b))]
                [(not (= (second a) (second b))) (< (second a) (second b))]
                [else (< (third a) (third b))]))""",
        "holes_only": """(lambda (a b)
          (cond [(not (= (first a) (first b))) (> (first a) (first b))]
                [(not (= (list-ref a 5) (list-ref b 5)))
                 (< (list-ref a 5) (list-ref b 5))]
                [else (< (list-ref a 4) (list-ref b 4))]))""",
        "holes_scan": "(lambda (a b) (> (first a) (first b)))",
        "area_only": """(lambda (a b)
          (cond [(not (= (second a) (second b))) (< (second a) (second b))]
                [(not (= (list-ref a 5) (list-ref b 5)))
                 (< (list-ref a 5) (list-ref b 5))]
                [else (< (list-ref a 4) (list-ref b 4))]))""",
        "area_scan": "(lambda (a b) (< (second a) (second b)))",
        "holes_area_scan": """(lambda (a b)
          (cond [(not (= (first a) (first b))) (> (first a) (first b))]
                [else (< (second a) (second b))]))""",
        "color_only": "(lambda (a b) (< (third a) (third b)))",
        "bbox_zeros": """(lambda (a b)
          (let ((ka (- (* (rows (fourth a)) (cols (fourth a))) (- 0 (second a))))
                (kb (- (* (rows (fourth b)) (cols (fourth b))) (- 0 (second b)))))
            (cond [(not (= ka kb)) (> ka kb)]
                  [(not (= (second a) (second b))) (< (second a) (second b))]
                  [else (< (third a) (third b))])))""",
        "reverse_holes": """(lambda (a b)
          (cond [(not (= (first a) (first b))) (< (first a) (first b))]
                [(not (= (second a) (second b))) (< (second a) (second b))]
                [else (< (third a) (third b))]))""",
        "wrong_color_tie": """(lambda (a b)
          (cond [(not (= (first a) (first b))) (> (first a) (first b))]
                [(not (= (second a) (second b))) (< (second a) (second b))]
                [else (> (third a) (third b))]))""",
        "wrong_area_tie": """(lambda (a b)
          (cond [(not (= (first a) (first b))) (> (first a) (first b))]
                [(not (= (second a) (second b))) (> (second a) (second b))]
                [else (< (third a) (third b))]))""",
        "bbox_area": """(lambda (a b)
          (let ((ka (* (rows (fourth a)) (cols (fourth a))))
                (kb (* (rows (fourth b)) (cols (fourth b)))))
            (cond [(not (= ka kb)) (> ka kb)]
                  [(not (= (second a) (second b))) (< (second a) (second b))]
                  [else (< (third a) (third b))])))""",
        "height_only": """(lambda (a b)
          (cond [(not (= (rows (fourth a)) (rows (fourth b))))
                 (> (rows (fourth a)) (rows (fourth b)))]
                [(not (= (second a) (second b))) (< (second a) (second b))]
                [else (< (third a) (third b))]))""",
        "width_only": """(lambda (a b)
          (cond [(not (= (cols (fourth a)) (cols (fourth b))))
                 (> (cols (fourth a)) (cols (fourth b)))]
                [(not (= (second a) (second b))) (< (second a) (second b))]
                [else (< (third a) (third b))]))""",
        "source_top": """(lambda (a b)
          (cond [(not (= (list-ref a 4) (list-ref b 4)))
                 (< (list-ref a 4) (list-ref b 4))]
                [else (< (list-ref a 5) (list-ref b 5))]))""",
        "input_position": """(lambda (a b)
          (cond [(not (= (list-ref a 5) (list-ref b 5)))
                 (< (list-ref a 5) (list-ref b 5))]
                [else (< (list-ref a 4) (list-ref b 4))]))""",
    }
    if mode == "source_order":
        return None
    try:
        return comparisons[mode]
    except KeyError as exc:
        raise KeyError(f"unknown Racket sort mode {mode}") from exc


def _program(
    *,
    sort_mode: str = "canonical",
    finish: str = "original",
    gap: int = 1,
    bottom: bool = False,
    fill_bbox: bool = False,
    rank_order: str = "left",
    rank_value: str = "rank",
    rank_bbox: bool = False,
    partial: bool = False,
    skip_pack: bool = False,
) -> str:
    if gap not in (0, 1, 2):
        raise ValueError(gap)
    comparator = _comparator(sort_mode)
    ordered = "enriched0" if comparator is None else f"(sort enriched0 {comparator})"
    crop_body = (
        "(obj-color obj)"
        if fill_bbox
        else "(if (member? (list rr cc) (obj-cells obj)) (at g rr cc) 0)"
    )
    local_row = "(- r (- H (rows crop)))" if bottom else "r"
    rank_comparators = {
        "left": """(lambda (a b)
          (cond [(not (= (obj-c1 a) (obj-c1 b))) (< (obj-c1 a) (obj-c1 b))]
                [else (< (obj-r1 a) (obj-r1 b))]))""",
        "right": """(lambda (a b)
          (cond [(not (= (obj-c2 a) (obj-c2 b))) (> (obj-c2 a) (obj-c2 b))]
                [else (< (obj-r1 a) (obj-r1 b))]))""",
        "color": "(lambda (a b) (< (obj-color a) (obj-color b)))",
        "top": """(lambda (a b)
          (cond [(not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b))]
                [else (< (obj-c1 a) (obj-c1 b))]))""",
    }
    value_expr = {
        "rank": "rank",
        "reverse": "(- (+ (length ranked) 1) rank)",
        "one": "1",
    }[rank_value]
    paint_body = (
        "(draw-rect-filled acc (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj) value)"
        if rank_bbox
        else "(reduce (lambda (a p) (set-cell a (first p) (second p) value)) acc (obj-cells obj))"
    )
    finish_body = "packed"
    if finish == "rank":
        next_body = "(paint-object acc (first remaining) value)" if partial else (
            "(loop (rest remaining) (+ rank 1) "
            "(paint-object acc (first remaining) value))"
        )
        finish_body = f"""(let* ((ranked (sort (objects packed 0) {rank_comparators[rank_order]})))
      (define (paint-object acc obj value) {paint_body})
      (let loop ([remaining ranked] [rank 1] [acc packed])
        (if (empty? remaining)
            acc
            (let ((value {value_expr})) {next_body}))))"""
    elif finish != "original":
        raise KeyError(finish)

    packed_definition = "(define packed g)" if skip_pack else f"""(define packed
      (grid-from-fn H W
        (lambda (r c)
          (let loop ([remaining crops] [offset 0])
            (cond [(empty? remaining) 0]
                  [(and (>= c offset) (< c (+ offset (cols (first remaining)))))
                   (let* ((crop (first remaining))
                          (local-r {local_row}))
                     (if (and (>= local-r 0) (< local-r (rows crop)))
                         (at crop local-r (- c offset))
                         0))]
                  [else (loop (rest remaining) (+ offset (cols (first remaining)) {gap}))])))))"""

    return f"""(rule!
  (let ((dummy 0))
    (define (crop-object obj)
      (grid-from-fn (obj-h obj) (obj-w obj)
        (lambda (r c)
          (let ((rr (+ (obj-r1 obj) r)) (cc (+ (obj-c1 obj) c)))
            {crop_body}))))
    (define (hole-count crop)
      (define seen (make-hash))
      (define holes 0)
      (for* ([r (in-range (rows crop))] [c (in-range (cols crop))])
        (when (and (= (at crop r c) 0) (not (hash-has-key? seen (cons r c))))
          (define queue (list (cons r c)))
          (define touches #f)
          (hash-set! seen (first queue) #t)
          (let bfs ([fuel 0])
            (unless (empty? queue)
              (let ((cur (first queue)))
                (set! queue (rest queue))
                (when (or (= (car cur) 0) (= (cdr cur) 0)
                          (= (car cur) (- (rows crop) 1))
                          (= (cdr cur) (- (cols crop) 1)))
                  (set! touches #t))
                (for ([d (in-list cardinal-deltas)])
                  (let ((nr (+ (car cur) (first d)))
                        (nc (+ (cdr cur) (second d))))
                    (when (and (in-bounds? nr nc (rows crop) (cols crop))
                               (= (at crop nr nc) 0)
                               (not (hash-has-key? seen (cons nr nc))))
                      (hash-set! seen (cons nr nc) #t)
                      (set! queue (append queue (list (cons nr nc))))))))
              (bfs (+ fuel 1))))
          (unless touches (set! holes (+ holes 1)))))
      holes)
    (define enriched0
      (map (lambda (obj)
             (let ((crop (crop-object obj)))
               (list (hole-count crop) (- 0 (obj-size obj)) (obj-color obj)
                     crop (obj-r1 obj) (obj-c1 obj))))
           (objects g 0)))
    (define enriched {ordered})
    (define crops (map fourth enriched))
    (define H (apply max (map rows crops)))
    (define W (+ (apply + (map cols crops)) (* {gap} (- (length crops) 1))))
    {packed_definition}
    {finish_body}))"""


def candidate_sources(proto) -> dict[str, dict[str, str]]:
    sort_modes = (
        "source_order",
        "input_position",
        "holes_only",
        "holes_scan",
        "area_only",
        "area_scan",
        "holes_area_scan",
        "color_only",
        "bbox_zeros",
        "reverse_holes",
        "wrong_color_tie",
        "wrong_area_tie",
        "bbox_area",
        "height_only",
        "width_only",
        "source_top",
    )
    original = {
        "expected_original": proto.program({"output_colors": "original"}),
        "rank_setting": proto.program({"output_colors": "rank"}),
        "identity": "(rule! (lambda (g) g))",
        "all_zero": "(rule! (lambda (g) (empty-grid (rows g) (cols g) 0)))",
        **{mode: _program(sort_mode=mode) for mode in sort_modes},
        "gap0": _program(gap=0),
        "gap2": _program(gap=2),
        "bottom_align": _program(bottom=True),
        "filled_bbox": _program(fill_bbox=True),
    }
    rank = {
        "expected_rank": proto.program({"output_colors": "rank"}),
        "original_setting": proto.program({"output_colors": "original"}),
        "identity": "(rule! (lambda (g) g))",
        "all_zero": "(rule! (lambda (g) (empty-grid (rows g) (cols g) 0)))",
        **{mode: _program(sort_mode=mode, finish="rank") for mode in sort_modes},
        "gap0": _program(finish="rank", gap=0),
        "gap2": _program(finish="rank", gap=2),
        "bottom_align": _program(finish="rank", bottom=True),
        "filled_bbox": _program(finish="rank", fill_bbox=True),
        "skip_pack_rank": _program(finish="rank", skip_pack=True),
        "reverse_rank": _program(finish="rank", rank_value="reverse"),
        "color_rank": _program(finish="rank", rank_order="color"),
        "right_to_left_rank": _program(finish="rank", rank_order="right"),
        "bbox_rank": _program(finish="rank", rank_bbox=True),
        "all_one_rank": _program(finish="rank", rank_value="one"),
        "partial_rank_first": _program(finish="rank", partial=True),
    }
    return {"original": original, "rank": rank}


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _expect_error(fn, label: str) -> str:
    try:
        fn()
    except (TypeError, ValueError) as exc:
        return f"{label}: {type(exc).__name__}: {exc}"
    raise AssertionError(f"{label} unexpectedly succeeded")


def build_report(seeds=(0, 7, 17, 41, 91)) -> dict[str, Any]:
    if not seeds or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("seeds must be nonempty nonnegative exact integers")
    proto = _load_prototype()
    banks = candidate_sources(proto)
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    runtime = ROOT / "shared" / "runtime"
    checks = []
    regressions: dict[str, dict[str, Any]] = {}
    evaluations = 0
    max_demo_checks = []
    stress_rows = []

    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for setting in proto.SETTINGS:
                mode = setting["output_colors"]
                bank = banks[mode]
                expected_name = "expected_original" if mode == "original" else "expected_rank"
                for seed in seeds:
                    episode = proto.generate(seed, setting, demos=2, queries=4)
                    expected_train = [pair["output"] for pair in episode["train"]]
                    survivors = []
                    for name, source in bank.items():
                        actual = [apply(source, pair["input"]) for pair in episode["train"]]
                        evaluations += len(actual)
                        if actual == expected_train:
                            survivors.append(name)
                    if survivors != [expected_name]:
                        raise ValueError(f"survivors for {mode} seed {seed}: {survivors}")

                    expected_source = bank[expected_name]
                    for index, pair in enumerate(episode["test"]):
                        if apply(expected_source, pair["input"]) != pair["output"]:
                            raise ValueError(f"protected query label mismatch for {mode} seed {seed} query {index}")
                        evaluations += 1

                    for name, source in bank.items():
                        if name == expected_name:
                            continue
                        key = f"{mode}:{name}"
                        if key in regressions:
                            continue
                        for split in ("train", "test"):
                            found = False
                            for index, pair in enumerate(episode[split]):
                                actual = apply(source, pair["input"])
                                evaluations += 1
                                if actual != pair["output"]:
                                    regressions[key] = {
                                        "settings": setting,
                                        "rival": name,
                                        "split": split,
                                        "index": index,
                                        "input": pair["input"],
                                        "expected": pair["output"],
                                        "rival_output": actual,
                                    }
                                    found = True
                                    break
                            if found:
                                break
                    checks.append({
                        "settings": setting,
                        "seed": seed,
                        "survivors": survivors,
                        "demo_input_sha256": [_digest(pair["input"]) for pair in episode["train"]],
                        "query_input_sha256": [_digest(pair["input"]) for pair in episode["test"]],
                    })

                maximum = proto.generate(10_000 + seeds[0], setting, demos=6, queries=4)
                for pair in maximum["train"] + maximum["test"]:
                    if apply(bank[expected_name], pair["input"]) != pair["output"]:
                        raise ValueError(f"maximum-count protected label mismatch for {mode}")
                    evaluations += 1
                max_demo_checks.append({
                    "settings": setting,
                    "demos": len(maximum["train"]),
                    "queries": len(maximum["test"]),
                    "distinct_inputs": len({proto.digest(pair["input"]) for pair in maximum["train"] + maximum["test"]}),
                })

                stress = maximum["test"][3]
                profile = proto.analyze_input(stress["input"])
                stress_rows.append({
                    "settings": setting,
                    "input_sha256": _digest(stress["input"]),
                    "output_sha256": _digest(stress["output"]),
                    **profile,
                    "skip_pack_changes_output": (
                        mode != "rank" or proto.skip_pack_counterfactual(stress["input"]) != stress["output"]
                    ),
                })
        finally:
            bridge.close()

    expected_regressions = sum(len(bank) - 1 for bank in banks.values())
    if len(regressions) != expected_regressions:
        missing = []
        for mode, bank in banks.items():
            expected_name = "expected_original" if mode == "original" else "expected_rank"
            for name in bank:
                if name != expected_name and f"{mode}:{name}" not in regressions:
                    missing.append(f"{mode}:{name}")
        raise ValueError(f"missing concrete regressions: {missing}")

    sample = proto.generate(31337, {"output_colors": "rank"}, demos=2, queries=4)
    visible = proto.public_turn(sample, 0)
    private = copy.deepcopy(sample)
    private["settings"] = {"output_colors": "original"}
    private["program_solution"] = "private mutation"
    private["certificate"] = {"forged": True}
    private["test"][0]["output"] = [[9]]
    private["test"][1]["input"] = [[9]]
    if proto.public_turn(private, 0) != visible:
        raise ValueError("private or future-query mutation changed first public turn")
    visible_change = copy.deepcopy(sample)
    visible_change["train"][0]["output"] = [[9]]
    if proto.public_turn(visible_change, 0) == visible:
        raise ValueError("visible mutation failed positive control")

    corrupt = copy.deepcopy(sample)
    corrupt["program_solution"] = "(rule! (lambda (g) g))"
    duplicate = copy.deepcopy(sample)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    rejections = [
        _expect_error(lambda: proto.generate(0, proto.DEFAULT_SETTINGS, demos=True, queries=4), "boolean demos"),
        _expect_error(lambda: proto.generate(0, proto.DEFAULT_SETTINGS, demos=2, queries=3), "wrong query count"),
        _expect_error(lambda: proto.generate(0, {"output_colors": "rank", "extra": 1}, 2, 4), "extra setting"),
        _expect_error(lambda: proto.certify(corrupt), "stale program"),
        _expect_error(lambda: proto.certify(duplicate), "duplicate input"),
        _expect_error(lambda: proto.canonical_transform([[True]]), "boolean grid"),
    ]

    return {
        "schema": "arcpuzzles-parametric-adversarial-self-review-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "seeds": list(seeds),
        "minimum_demos": 2,
        "queries": 4,
        "candidate_program_sha256": {
            mode: {name: hashlib.sha256(source.encode()).hexdigest() for name, source in bank.items()}
            for mode, bank in banks.items()
        },
        "candidate_counts": {mode: len(bank) for mode, bank in banks.items()},
        "checks": checks,
        "maximum_count_checks": max_demo_checks,
        "regressions": list(regressions.values()),
        "regression_count": len(regressions),
        "stress_30x30": stress_rows,
        "contract_rejections": rejections,
        "public_private_checks": {
            "private_and_future_invariant": True,
            "visible_positive_control": True,
        },
        "racket": identity,
        "racket_evaluations": evaluations,
        "source_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in (
                "prototype.py",
                "adapter.py",
                "promotion.json",
                "canonical.rkt",
                "rank.rkt",
                "skip_pack.rkt",
                "semantic_sweep.py",
                "adversarial_probe.py",
            )
        },
        "limits": (
            "Finite protected-Racket falsification over the declared settings, candidate bank, "
            "five seeds, and authored count/stress boundaries; not a universal uniqueness proof."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "candidate_counts": report["candidate_counts"],
        "racket_evaluations": report["racket_evaluations"],
        "regression_count": report["regression_count"],
        "stress_30x30": report["stress_30x30"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
