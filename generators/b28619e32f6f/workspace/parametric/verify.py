"""Bounded Racket-backed teaching audit and first-turn example writer.

Run through the packet's review.py wrapper. Every retained label is executed;
Python competitors are separately identified as finite authored hypotheses.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import public_challenge_bytes, load_selected_generator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
_spec = importlib.util.spec_from_file_location("_b286_verify_prototype", HERE / "prototype.py")
p = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p)


def turn_bytes(episode, query_index=0):
    """One current query only; its ID has no private or future-turn inputs."""
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index must select one current query")
    return public_challenge_bytes({"train": episode["train"],
                                   "test": [episode["test"][query_index]]})


def bbox_area(cells):
    rows, cols = zip(*cells)
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def paint(grid, components, choose):
    out = deepcopy(grid)
    for cells in components:
        color = choose(cells)
        for r, c in cells:
            out[r][c] = color
    return out


def rivals(grid, mode, canonical):
    all_regions = p.regions(grid)
    inside = [cells for cells in all_regions if p.enclosed(grid, cells)]
    maximum = max(map(len, inside))
    recolor = lambda fn, components=inside: paint(grid, components, fn)
    area = lambda cells: p.area_color(len(cells), mode, maximum)
    result = {"no_op": deepcopy(grid),
              "opposite_setting": p.mirror(grid, p.MODES[1 - p.MODES.index(mode)]),
              "bbox_numerator": recolor(lambda cells: p.area_color(bbox_area(cells), mode, maximum)),
              "fill_exterior_too": recolor(area, all_regions)}
    for color in (8, 4, 3):
        result[f"all_to_{color}"] = recolor(lambda cells, color=color: color)
    diagonal = [cells for cells in p.regions(grid, diagonal=True) if p.enclosed(grid, cells)]
    diagonal_max = max(map(len, diagonal))
    result["eight_connectivity"] = recolor(
        lambda cells: p.area_color(len(cells), mode, diagonal_max), diagonal)
    errors, analysis = canonical._analyze(grid)
    if errors:
        raise AssertionError({"invalid_generated_domain": errors})
    owners = [(frame, [region["cells"] for region in frame["regions"]]) for frame in analysis["frames"]]
    total_paint, local_max_paint = deepcopy(grid), deepcopy(grid)
    for frame, components in owners:
        total, local_max = sum(map(len, components)), max(map(len, components))
        total_paint = paint(total_paint, components, lambda cells, n=total: p.area_color(n, mode, maximum))
        local_max_paint = paint(local_max_paint, components,
                               lambda cells, m=local_max: p.area_color(len(cells), mode, m))
    result["one_color_per_frame_total"] = total_paint
    if mode == "fixed":
        for name, lower, upper in (("strict_lower", 7, 24), ("strict_upper", 8, 23),
                                    ("strict_both", 7, 23), ("upper_off_by_one", 8, 25)):
            result[name] = recolor(lambda cells, a=lower, b=upper: 8 if len(cells) <= a else 4 if len(cells) <= b else 3)
        result["exact_8_24_only"] = recolor(lambda cells: 8 if len(cells) == 8 else 4 if len(cells) == 24 else 3)
    else:
        result["per_frame_maximum"] = local_max_paint
        for name, value in (("bbox_denominator", max(map(bbox_area, inside))),
                            ("total_denominator", sum(map(len, inside))),
                            ("minimum_denominator", min(map(len, inside))),
                            ("include_exterior_maximum", max(map(len, all_regions))),
                            ("fixed_maximum_32", 32), ("fixed_maximum_51", 51)):
            result[name] = recolor(lambda cells, m=value: p.area_color(len(cells), mode, m))
        result["bbox_both"] = recolor(lambda cells: p.area_color(bbox_area(cells), mode, max(map(bbox_area, inside))))
        for name, strict_lower, strict_upper in (("strict_lower", True, False),
                                                ("strict_upper", False, True), ("strict_both", True, True)):
            def choose(cells, low=strict_lower, high=strict_upper):
                n = len(cells)
                return 8 if 4*n < maximum + (not low) else 4 if 2*n < maximum + (not high) else 3
            result[name] = recolor(choose)
        result["ceil_thresholds"] = recolor(lambda cells: 8 if 4*len(cells) <= maximum+3 else 4 if 2*len(cells) <= maximum+1 else 3)
        result["nearest_thresholds"] = recolor(lambda cells: 8 if 4*len(cells) <= maximum+2 else 4 if 2*len(cells) <= maximum+1 else 3)
    return result


def racket_rivals(mode):
    source = p.program({"threshold_mode": mode})
    if mode == "fixed":
        return {"strict_both": source.replace("(<= size 8)", "(< size 8)").replace("(<= size 24)", "(< size 24)"),
                "exact_8_24_only": source.replace("(<= size 8)", "(= size 8)").replace("(<= size 24)", "(= size 24)")}
    return {
        "strict_both": source.replace("(<= (* 4 size) largest)", "(< (* 4 size) largest)").replace("(<= (* 2 size) largest)", "(< (* 2 size) largest)"),
        "ceil_thresholds": source.replace("(<= (* 4 size) largest)", "(<= (* 4 size) (+ largest 3))").replace("(<= (* 2 size) largest)", "(<= (* 2 size) (+ largest 1))"),
        "fixed_maximum_32": source.replace("(reduce (lambda (best region) (max best (length region))) 1 regions)", "32"),
    }


def diff_cells(a, b):
    return sum(x != y for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def verify(out):
    from arcpuzzles.parametric_worker import _real_evaluator
    out = Path(out)
    if out.exists():
        raise FileExistsError("Choose a new verification output directory")
    canonical, canonical_path, canonical_hash = load_selected_generator("b28619e32f6f", root=ROOT)
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    checks, episodes, evaluations = [], [], 0
    cache = {}
    def execute(program, grid):
        nonlocal evaluations
        key = (program, json.dumps(grid))
        if key not in cache:
            cache[key] = apply(program, grid)
            evaluations += 1
        return deepcopy(cache[key])
    try:
        for seed in (0, 17):
            for mode in p.MODES:
                for demos in (2, 6):
                    episode = p.generate(seed, {"threshold_mode": mode}, demos, 4)
                    for pair in episode["train"] + episode["test"]:
                        assert not canonical.self_check(pair["input"])
                        actual = execute(episode["program_solution"], pair["input"])
                        assert actual == pair["output"], (seed, mode, demos, "label")
                        pair["output"] = actual
                    # Restrict the teaching check to the first TWO demos even at count6.
                    demo_rivals = [rivals(pair["input"], mode, canonical) for pair in episode["train"][:2]]
                    query_rivals = [rivals(pair["input"], mode, canonical) for pair in episode["test"]]
                    witnesses, survivors, harmful = {}, [], []
                    for name in demo_rivals[0]:
                        rejected = [i for i, predictions in enumerate(demo_rivals)
                                    if predictions[name] != episode["train"][i]["output"]]
                        if rejected:
                            witnesses[name] = rejected[0]
                        else:
                            survivors.append(name)
                            if any(predictions[name] != pair["output"] for predictions, pair in zip(query_rivals, episode["test"])):
                                harmful.append(name)
                    assert not harmful, {"seed": seed, "mode": mode, "harmful_survivors": harmful}
                    racket_checks = {}
                    for name, code in racket_rivals(mode).items():
                        outputs = [execute(code, pair["input"]) for pair in episode["train"][:2]]
                        assert outputs == [r[name] for r in demo_rivals], (name, "rival Python/Racket mismatch")
                        assert any(y != pair["output"] for y, pair in zip(outputs, episode["train"][:2]))
                        racket_checks[name] = {"program_sha256": hashlib.sha256(code.encode()).hexdigest(),
                                               "rejected_by_demo": next(i for i, y in enumerate(outputs) if y != episode["train"][i]["output"])}
                    checks.append({"seed": seed, "settings": {"threshold_mode": mode}, "demos": demos,
                                   "queries": 4, "labels": demos+4, "rivals": len(demo_rivals[0]),
                                   "demo_witnesses": witnesses, "survivors": survivors,
                                   "harmful_query_survivors": harmful, "racket_rivals": racket_checks})
                    if demos == 2:
                        episodes.append({**episode, "seed": seed, "settings": {"threshold_mode": mode}})
        # Retain the provisional even-maximum teaching hole and its repaired demo.
        rng = p._rng(0, "legacy_design", 0)
        old_grid = p._stack([p._frame([[11, 12, 13]], rng), p._frame([[23, 24, 25]], rng),
                             p._frame([[47, 48]], rng)], rng)
        fixed_episode = p.generate(0, {"threshold_mode": "relative_to_largest"}, 2, 4)
        gold = fixed_episode["program_solution"]
        wrong = racket_rivals("relative_to_largest")["ceil_thresholds"]
        old_inputs = [fixed_episode["train"][0]["input"], old_grid]
        old_demos = [{"input": grid, "output": execute(gold, grid)} for grid in old_inputs]
        assert all(execute(wrong, pair["input"]) == pair["output"] for pair in old_demos)
        witness_grid = fixed_episode["train"][1]["input"]
        correct, alternate = execute(gold, witness_grid), execute(wrong, witness_grid)
        assert correct != alternate
        repair = {"status": "repaired_in_first_two_demonstrations", "scope": "provisional even-M curriculum, not an inherited released source",
                  "program": gold, "rival_program": wrong, "old_demos": old_demos,
                  "distinguishing_demo": {"input": witness_grid, "output": correct, "rival_output": alternate},
                  "different_cells": diff_cells(correct, alternate), "racket": identity}
    finally:
        bridge.close()
    out.mkdir(parents=True)
    (out / "public").mkdir()
    mapping = []
    for episode in episodes:
        raw = turn_bytes(episode, 0)
        name = hashlib.sha256(raw).hexdigest() + ".json"
        (out / "public" / name).write_bytes(raw)
        mapping.append({"seed": episode["seed"], "settings": episode["settings"], "first_turn_public": "public/"+name})
        # The first-turn bytes cannot depend on the future input or any private answer.
        altered = deepcopy(episode)
        altered["program_solution"] = "private_changed"
        altered["settings"] = {"private": "changed"}
        altered["test"][0]["output"] = [[9]]
        altered["test"][1:] = [{"input": [[9]], "output": [[9]]}]
        assert turn_bytes(altered, 0) == raw
    sources = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in HERE.iterdir()
               if path.is_file() and path.suffix in (".py", ".rkt", ".json")}
    summary = {"status": "passed", "scope": "bounded native prototype self-audit", "task_id": "b28619e32f6f",
               "canonical_generator_sha256": canonical_hash, "prototype_sources": sources, "racket": identity,
               "attempted_episodes": len(checks), "successful_episodes": len(checks), "failed_episodes": 0,
               "racket_evaluations": evaluations, "verified_label_occurrences": sum(row["labels"] for row in checks),
               "checks": checks, "public_query_count": 1, "controller_query_count": 4,
               "limits": "Finite rivals and seeds only. Python rivals are authored hypotheses; five named variants also replayed in Racket. Owner acceptance and training admission are pending."}
    for name, value in (("summary.json", summary), ("episodes.private.json", episodes),
                        ("mapping.private.json", mapping), ("teaching-repair.private.json", repair)):
        (out / name).write_text(json.dumps(value, indent=2, sort_keys=True)+"\n")
    print(json.dumps({key: summary[key] for key in ("status", "attempted_episodes", "successful_episodes",
                                                 "racket_evaluations", "verified_label_occurrences")}))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    verify(parser.parse_args().out)
