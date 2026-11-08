"""Bounded protected-Racket audit and visible-byte export; grants no acceptance."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
PARAMETRIC_HOME = Path(__file__).resolve().parent
ROOT = PARAMETRIC_HOME.parents[3]
TASK = "5d9c166a8c3b"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arc_repl.racket_bridge import RacketBridge
from arcpuzzles.runtime import validate_grid
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False) + "\n")


def sources():
    paths = [PARAMETRIC_HOME / name for name in ("audit.py", "adapter.py", "prototype.py",
                                     "canonical.rkt", "promotion.json")]
    paths += [ROOT / name for name in (f"generators/{TASK}/generator.py",
        "shared/runtime/reviewer_support.py", "shared/runtime/puzzle_generators/rule_wrap.py",
        "shared/tools/comment_solutions.py", "src/arcpuzzles/runtime.py")]
    return {path.relative_to(ROOT).as_posix(): sha(path.read_bytes()) for path in paths}


def boxes(prototype, grid, grouping):
    return sorted([{"bbox": list(prototype.gen._bbox(group)), "area": prototype._area(group)}
                   for group in prototype.groups(grid, grouping)], key=lambda item: item["bbox"])


def statistics(prototype, grid, output):
    h, w = len(grid), len(grid[0])
    nonzero = sum(cell != 0 for row in grid for cell in row)
    edges = [grid[0], grid[-1], [row[0] for row in grid], [row[-1] for row in grid]]
    return {"shape": [h, w], "nonzero_input_cells": nonzero, "input_density": nonzero / (h * w),
            "input_colors": sorted({cell for row in grid for cell in row}),
            "initial_components": len(prototype.groups(grid, "original")),
            "final_boxes": boxes(prototype, grid, "fixed"),
            "boundary_contacts": [name for name, edge in zip(("top", "bottom", "left", "right"), edges)
                                  if any(cell != 0 for cell in edge)],
            "filled_cells": sum(a == 0 and b == 2 for x, y in zip(grid, output) for a, b in zip(x, y))}


def public_export(out, episode, adapter, prototype):
    public = public_challenge_bytes(episode)
    first = prototype.first_turn_bytes(episode)
    altered = copy.deepcopy(episode)
    altered.update(seed="private", settings={"private": True}, program_solution="private",
                   program="private", provenance={"private": True}, query_count=999)
    altered["train"][0]["private"] = "changed"
    for pair in altered["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(altered) == public
    assert prototype.first_turn_bytes(altered) == first
    altered["test"][1:] = [{"input": [[9]], "output": [[8]]}]
    assert prototype.first_turn_bytes(altered) == first
    one = adapter.generate(episode["seed"], episode["settings"], len(episode["train"]), 1)
    assert one["train"] == episode["train"] and one["test"] == episode["test"][:1]
    assert prototype.first_turn_bytes(one) == first
    paths = {}
    for folder, payload in (("public", public), ("first_turn", first)):
        path = out / folder / (sha(payload) + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(payload)
        paths[folder] = path.relative_to(out).as_posix()
    return {**paths, "private_invariance": True, "future_query_invariance": True,
            "single_query_prefix": True, "prefix_sampling": one["sampling"]}


def manual_cases():
    small, large = [[0] * 10 for _ in range(8)], [[0] * 30 for _ in range(30)]
    for r, c in ((0, 0), (0, 4), (3, 2), (6, 9)):
        small[r][c] = 4
    for grid, rectangles in ((small, [(6, 7, 6, 7)]), (large,
            [(0, 7, 0, 2), (2, 6, 10, 12), (10, 13, 6, 7), (17, 29, 17, 19), (22, 26, 27, 29)])):
        for r0, r1, c0, c1 in rectangles:
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    grid[r][c] = 4
    return [("small8x10", small), ("large30x30", large)]


def run(out, seed):
    out.mkdir(parents=True, exist_ok=False)
    report = {"schema": "bbox-parametric-audit-v1", "task_id": TASK, "seed": seed,
              "status": "running", "source_sha256": sources(), "jobs": [], "failures": [],
              "accepted": False, "training_admitted": False,
              "scope": "Bounded sampled labels and declared finite rivals; no universal identifiability or training gain."}
    episodes, causal, executions, programs, matched = [], [], [], {}, {}
    bridge, context, current, labels_checked = None, "startup", None, 0
    try:
        spec = importlib.util.spec_from_file_location("_bbox_audit_adapter", PARAMETRIC_HOME / "adapter.py")
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        prototype = adapter.prototype
        bridge = RacketBridge()
        report["runtime"] = bridge.runtime_identity
        assert report["runtime"]["backend"] == "racket" and report["runtime"]["protected"] is True
        wrapped = {}

        def evaluate(program, grid):
            validate_grid(grid)
            digest = sha(program.encode())
            programs[digest] = program
            if digest not in wrapped:
                wrapped[digest] = wrap_rule(program)
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            event = {"context": context, "program_sha256": digest, "input": grid}
            executions.append(event)
            try:
                event["output"] = validate_grid(bridge.eval_text(f"({wrapped[digest]} {literal})"))
                return event["output"]
            except Exception as error:
                event["error"] = {"type": type(error).__name__, "message": str(error)}
                raise

        cases = [("ordinary", 3, None, None), ("7x7", 2, 7, 7), ("7x30", 3, 7, 30),
                 ("30x7", 6, 30, 7), ("30x30", 2, 30, 30)]
        for offset, (name, demos, height, width) in enumerate(cases):
            for scope in prototype.SCOPES:
                settings = {"fill_scope": scope}
                context = f"{name}:{scope}"
                current = {"case": name, "settings": settings, "seed": seed + offset,
                           "demos": demos, "queries": 4, "status": "attempted"}
                report["jobs"].append(current)
                episode = (adapter.generate(seed + offset, settings, demos, 4) if height is None else
                           prototype.generate(seed + offset, settings, demos, 4, height=height, width=width))
                current["sampling"] = episode["sampling"]
                assert episode["program_solution"] == adapter.program(settings)
                inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
                assert inputs == matched.setdefault(name, inputs), "Setting-dependent input sampler"
                assert len({json.dumps(grid) for grid in inputs}) == len(inputs), "Duplicate inputs"
                assert len(episode["train"]) == demos and len(episode["test"]) == 4
                if height is not None:
                    assert all((len(grid), len(grid[0])) == (height, width) for grid in inputs)
                stats = []
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        context = f"{name}:{scope}:{split}:{index}"
                        actual = evaluate(episode["program_solution"], pair["input"])
                        validate_grid(pair["output"])
                        assert actual == pair["output"], "Python/Racket label mismatch: " + context
                        pair["output"] = actual
                        labels_checked += 1
                        stats.append({"split": split, "index": index,
                                      **statistics(prototype, pair["input"], actual)})
                record = {"case": name, "episode": episode, "statistics": stats,
                          "program_sha256": sha(episode["program_solution"].encode()), "mirror_parity": True}
                if name in ("ordinary", "7x7"):
                    context = f"{name}:{scope}:teaching"
                    teaching = prototype.teaching_check(episode, scope, evaluate=evaluate)
                    record["teaching"] = teaching
                    current["teaching"] = teaching
                    assert set(teaching["rivals"]) == set(prototype.rival_specs(scope))
                    assert teaching["ambiguous_queries"] == [], "Live query-changing finite rival"
                    record["sampled_harmless_survivors"] = [key for key, value in teaching["rivals"].items()
                                                            if value["fits_demonstrations"]]
                if name == "ordinary":
                    record["public_checks"] = public_export(out, episode, adapter, prototype)
                episodes.append(record)
                current["status"] = "passed"
        current = None
        settings = {"fill_scope": "largest_bbox"}
        correct = adapter.program(settings)
        counterfactual = prototype.rule_program("largest_bbox", grouping="static_graph")
        for name, grid in manual_cases():
            context = f"causal:{name}:correct"
            output = evaluate(correct, grid)
            context = f"causal:{name}:static_graph"
            wrong = evaluate(counterfactual, grid)
            assert output == prototype.solve(grid, "largest_bbox")
            assert wrong == prototype.solve(grid, "largest_bbox", grouping="static_graph")
            assert output != wrong, "Counterfactual did not change the witnessed output"
            causal.append({"case": name, "input": grid, "settings": settings,
                "intermediate_value": {"final": boxes(prototype, grid, "fixed"),
                    "static": boxes(prototype, grid, "static_graph"), "source": "prototype.groups Python mirror"},
                "program": correct, "program_sha256": sha(correct.encode()), "output": output,
                "counterfactual_program": counterfactual,
                "counterfactual_program_sha256": sha(counterfactual.encode()),
                "counterfactual_output": wrong, "ablation": "wrong_intermediate", "mirror_parity": True})
        assert sources() == report["source_sha256"], "Source changed during the audit"
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        if current is not None:
            current["status"] = "failed"
        report["failures"].append({"context": context, "type": type(error).__name__, "message": str(error)})
    finally:
        if bridge is not None:
            bridge.close()
    report.update(completed_jobs=len(episodes), episode_labels_checked=labels_checked,
                  racket_evaluation_attempts=len(executions),
                  racket_evaluation_failures=sum("error" in event for event in executions),
                  sampler_attempts=sum(job.get("sampling", {}).get("attempts", 0) for job in report["jobs"]),
                  prefix_sampler_attempts=sum(record.get("public_checks", {}).get("prefix_sampling", {}).get("attempts", 0)
                                              for record in episodes),
                  program_sha256=sorted(programs), causal_cases=len(causal))
    for name, value in (("episodes", episodes), ("causal_cases", causal), ("executions", executions),
                        ("programs", programs), ("audit", report)):
        save(out / "private" / f"{name}.json", value)
    inventory = {path.relative_to(out).as_posix(): sha(path.read_bytes())
                 for path in sorted(out.rglob("*")) if path.is_file()}
    summary = {key: report[key] for key in ("schema", "task_id", "status", "seed", "source_sha256",
        "completed_jobs", "episode_labels_checked", "racket_evaluation_attempts", "racket_evaluation_failures",
        "sampler_attempts", "prefix_sampler_attempts", "program_sha256", "causal_cases", "failures", "scope", "accepted", "training_admitted")}
    summary.update(evidence_root_from_repo=os.path.relpath(out, ROOT), files_sha256=inventory,
                   runtime_identity_file="private/audit.json", native_qualification="not_performed_by_this_command")
    save(PARAMETRIC_HOME / "evidence/current/audit.json", summary)
    print(json.dumps({"status": report["status"], "out": str(out), "completed_jobs": len(episodes),
                      "episode_labels_checked": labels_checked, "racket_evaluations": len(executions),
                      "failures": report["failures"]}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=41)
    args = parser.parse_args()
    if not __debug__:
        parser.error("Run without Python optimization so audit assertions remain enabled")
    if args.seed < 0:
        parser.error("--seed must be nonnegative")
    if args.out.exists() or args.out.is_symlink():
        parser.error("--out must not already exist")
    return run(args.out.resolve(), args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
