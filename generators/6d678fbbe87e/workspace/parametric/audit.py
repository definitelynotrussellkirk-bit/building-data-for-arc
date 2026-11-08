"""Bounded protected-Racket audit for the completion-route parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import evaluate_contract, _real_evaluator
from reviewer_support import canonical_pairs, public_challenge_bytes, public_challenge_id

TASK_ID = "6d678fbbe87e"
HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = HERE.parents[3]
RULES = ("complete_only", "route_dominant")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise AssertionError(f"expected one Racket fragment, found {source.count(old)}: {old[:80]}")
    return source.replace(old, new, 1)


def rival_programs(prototype) -> dict[str, str]:
    source = prototype._ALTERNATE
    winner = "(winner (pick-max colors (lambda (color) (count-if (lambda (item) (= (third item) color)) fills))))"
    route_all = replace_once(
        source,
        "(targets (filter (lambda (item) (= (third item) winner)) fills))",
        "(targets fills)",
    )
    aligned = "(or (= (first a) (first b)) (= (second a) (second b)))"
    route_all = replace_once(
        route_all,
        aligned,
        "(and (= (third a) (third b)) (or (= (first a) (first b)) (= (second a) (second b))))",
    )
    route_all = route_all.replace("(set-cell line r1 c winner)", "(set-cell line r1 c (third a))")
    route_all = route_all.replace("(set-cell line r c1 winner)", "(set-cell line r c1 (third a))")
    return {
        "complete_only": prototype._CANONICAL,
        "route_dominant": source,
        "route_all_completed_colors": route_all,
        "route_least_completed": replace_once(source, "(pick-max colors", "(pick-min colors"),
        "route_most_input_cells": replace_once(
            source,
            winner,
            "(winner (pick-max colors (lambda (color) (count-color g color))))",
        ),
        "route_smallest_numeric_color": replace_once(source, winner, "(winner (min-list colors))"),
        "route_largest_numeric_color": replace_once(source, winner, "(winner (max-list colors))"),
        "route_horizontal_only": replace_once(source, aligned, "(= (first a) (first b))"),
        "route_vertical_only": replace_once(source, aligned, "(= (second a) (second b))"),
    }


def finite_census(adapter) -> dict:
    checked = 0
    failed = []
    for seed in range(16):
        for split, maximum in (("train", 6), ("test", 4)):
            for index in range(maximum):
                try:
                    grid = adapter.sample_input(seed, split, index)
                    analysis = adapter.completion_analysis(grid)
                    assert sorted(analysis["counts"].values()) == [1, 2, 3]
                    assert adapter.transform(grid, {"finish_rule": "complete_only"}) != adapter.transform(
                        grid, {"finish_rule": "route_dominant"}
                    )
                    checked += 1
                except Exception as error:  # retained evidence, not silent rejection
                    failed.append({"seed": seed, "split": split, "index": index,
                                   "error": f"{type(error).__name__}: {error}"})
    return {"checked": checked, "failed": failed, "status": "pass" if not failed else "fail"}


def survivor_status(disagreements: list[dict]) -> str:
    """Classify a demo-surviving rival by whether it changes a checked query."""
    return ("survives_demos_disagrees_query" if disagreements
            else "equivalent_on_checked_pairs")


def public_views(adapter) -> tuple[dict[str, bytes], dict]:
    public: dict[str, bytes] = {}
    private = []
    for finish_rule in RULES:
        settings = {"finish_rule": finish_rule}
        episode = adapter.generate(17, settings, 3, 4)
        ordered = []
        for query_index in range(4):
            view = {"train": episode["train"], "test": [episode["test"][query_index]]}
            raw = public_challenge_bytes(view)
            identifier = public_challenge_id(view)
            assert identifier == sha(raw)
            assert identifier not in public
            public[identifier] = raw
            ordered.append(identifier)
        first = {"train": episode["train"], "test": episode["test"][:1]}
        assert public_challenge_bytes(first) == public_challenge_bytes(
            adapter.generate(17, settings, 3, 1)
        )
        private.append({"settings": settings, "seed": 17, "demos": 3,
                        "views_in_private_order": ordered})
    return public, {
        "episodes": private,
        "consumer_instruction": (
            "Reveal exactly one opaque public view per turn in this private order. "
            "Do not expose settings, programs, answers, future inputs, directory listings, or total count."
        ),
    }


def run(out: Path) -> int:
    evidence_root = (HERE / "evidence").resolve()
    if not out.resolve().is_relative_to(evidence_root):
        raise ValueError("evidence output must remain in this task's parametric/evidence directory")
    adapter = load(HERE / "adapter.py", "_audit_6d678fbbe87e_adapter")
    prototype = load(HERE / "prototype.py", "_audit_6d678fbbe87e_prototype")
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    programs = rival_programs(prototype)
    source_paths = [HOME / "generator.py", HOME / "tests/test_native_parametric.py",
                    HERE / "adapter.py", HERE / "prototype.py", HERE / "canonical.rkt",
                    HERE / "promotion.json", Path(__file__)]
    source_hashes = {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in source_paths}

    jobs = [
        {"seed": seed, "settings": {"finish_rule": finish_rule}, "demos": demos, "queries": 4}
        for seed in (0, 17)
        for finish_rule in RULES
        for demos in (2, 3, 6)
    ]
    execution = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert execution["racket"] == {**execution["racket"], "backend": "racket", "protected": True}

    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    evaluations = 0

    def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
        nonlocal evaluations
        evaluations += 1
        value = apply(program, grid)
        assert type(value) is list and len(value) == len(grid)
        assert all(type(row) is list and len(row) == len(grid[0])
                   and all(type(cell) is int and 0 <= cell <= 9 for cell in row)
                   for row in value)
        return value

    teaching = []
    unresolved = []
    boundaries = []
    canonical_checks = []
    causal_case = None
    try:
        for seed in (0, 17):
            for finish_rule in RULES:
                settings = {"finish_rule": finish_rule}
                episode = adapter.generate(seed, settings, 2, 4)
                rows = []
                for name, source in programs.items():
                    if name == finish_rule:
                        continue
                    refutation = None
                    for demo_index, pair in enumerate(episode["train"]):
                        prediction = execute(source, pair["input"])
                        if prediction != pair["output"]:
                            refutation = {"demo_index": demo_index, "input": pair["input"],
                                          "reference_output": pair["output"],
                                          "rival_output": prediction}
                            break
                    row = {"name": name, "program_sha256": sha(source.encode("utf-8"))}
                    if refutation is None:
                        disagreements = []
                        for query_index, pair in enumerate(episode["test"]):
                            prediction = execute(source, pair["input"])
                            if prediction != pair["output"]:
                                disagreements.append({"query_index": query_index,
                                                      "input": pair["input"],
                                                      "reference_output": pair["output"],
                                                      "rival_output": prediction})
                        status = survivor_status(disagreements)
                        row.update({"status": status,
                                    "query_disagreements": disagreements})
                        if disagreements:
                            unresolved.append({"seed": seed, "settings": settings,
                                               "rival": name,
                                               "query_disagreement_count": len(disagreements)})
                    else:
                        row.update({"status": "refuted_by_visible_demo", "case": refutation})
                    rows.append(row)
                teaching.append({"seed": seed, "settings": settings, "demos_used": 2,
                                 "rivals": rows})

        for height, width in ((8, 10), (8, 30), (30, 10), (30, 30)):
            grid = adapter.sample_input(17, "test", 3, height=height, width=width)
            nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
            stats = {"height": height, "width": width, "nonzero_cells": len(nonzero),
                     "row_extent": [min(r for r, _ in nonzero), max(r for r, _ in nonzero)],
                     "column_extent": [min(c for _, c in nonzero), max(c for _, c in nonzero)],
                     "occupied_quadrants": len({(r >= height / 2, c >= width / 2) for r, c in nonzero})}
            for finish_rule in RULES:
                settings = {"finish_rule": finish_rule}
                source = adapter.program(settings)
                output = execute(source, grid)
                assert output == adapter.transform(grid, settings)
                boundaries.append({**stats, "settings": settings, "input": grid, "output": output,
                                   "program_sha256": sha(source.encode("utf-8"))})

        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            output = execute(prototype._CANONICAL, pair["input"])
            assert output == pair["output"] == adapter.transform(
                pair["input"], {"finish_rule": "complete_only"}
            )
            canonical_checks.append({key: pair[key] for key in
                                     ("variant", "split", "pair_index", "input", "output")})

        episode = adapter.generate(17, {"finish_rule": "route_dominant"}, 3, 4)
        pair = episode["test"][3]
        wrong_program = programs["route_most_input_cells"]
        wrong_output = execute(wrong_program, pair["input"])
        assert wrong_output != pair["output"]
        analysis = adapter.completion_analysis(pair["input"])
        input_counts = {str(color): sum(value == color for row in pair["input"] for value in row)
                        for color in analysis["counts"]}
        causal_case = {
            "settings": {"finish_rule": "route_dominant"},
            "program": adapter.program({"finish_rule": "route_dominant"}),
            "input": pair["input"],
            "output": pair["output"],
            "counterfactual_program": wrong_program,
            "counterfactual_output": wrong_output,
            "intermediate_value": {
                "canonical_fills": [list(item) for item in analysis["fills"]],
                "fill_counts": {str(k): v for k, v in analysis["counts"].items()},
                "dominant_color": analysis["dominant_color"],
                "input_color_counts": input_counts,
            },
            "ablation": "wrong_intermediate",
        }
    finally:
        bridge.close()

    census = finite_census(adapter)
    public, private_map = public_views(adapter)
    status = "pass" if not unresolved and not census["failed"] else "needs_repair"
    summary = {
        "schema": "arcpuzzles-task-local-authoring-audit-v1",
        "task_id": TASK_ID,
        "status": status,
        "source_hashes": source_hashes,
        "racket": identity,
        "native_jobs": len(execution["episodes"]),
        "native_labels": sum(row["label_count"] for row in execution["checks"]),
        "native_racket_evaluations": execution["racket_evaluations"],
        "additional_racket_evaluations": evaluations,
        "teaching_lessons": len(teaching),
        "rival_checks": sum(len(row["rivals"]) for row in teaching),
        "refuted_rival_checks": sum(
            rival["status"] == "refuted_by_visible_demo"
            for row in teaching for rival in row["rivals"]
        ),
        "unresolved_rivals": unresolved,
        "boundary_labels": len(boundaries),
        "canonical_labels": len(canonical_checks),
        "public_views": len(public),
        "sampling": census,
        "limits": (
            "Finite rivals, seeds and shape boundaries only; not universal uniqueness. "
            "Owner exact-source acceptance and training admission remain pending."
        ),
    }
    dump(out / "execution.json", execution)
    dump(out / "teaching.json", {"source_hashes": source_hashes, "racket": identity,
                                  "lessons": teaching,
                                  "scope": "Rivals see demonstrations only; queries diagnose only full survivors."})
    dump(out / "boundary.json", {"source_hashes": source_hashes, "racket": identity,
                                  "cases": boundaries})
    dump(out / "canonical.json", {"source_hashes": source_hashes, "racket": identity,
                                   "cases": canonical_checks})
    dump(out / "causal-case.json", causal_case)
    dump(out / "private-export-map.json", private_map)
    for identifier, raw in public.items():
        path = out / "public" / f"{identifier}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    dump(out / "summary.json", summary)
    print(json.dumps({key: summary[key] for key in (
        "status", "native_jobs", "native_labels", "native_racket_evaluations",
        "additional_racket_evaluations", "rival_checks", "refuted_rival_checks",
        "unresolved_rivals", "boundary_labels", "canonical_labels", "public_views", "sampling"
    )}, sort_keys=True))
    return 0 if status == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "evidence/current")
    return run(parser.parse_args().out)


if __name__ == "__main__":
    raise SystemExit(main())
