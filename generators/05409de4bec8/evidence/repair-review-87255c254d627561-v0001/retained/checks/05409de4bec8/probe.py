#!/usr/bin/env python3
"""One bounded learnability probe: canvas-axis rectangle policy.

Search labels are Python diagnostics only. The retained witness is accepted
only after both exact programs execute through protected actual Racket.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import load_selected_generator, canonical_path
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = "05409de4bec8"
MARKER = """(> (abs (- (second col-pairs) (first col-pairs)))
                     (abs (- (second row-pairs) (first row-pairs))))"""
REPLACEMENT = "(> (length (first g)) (length g))"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def diagnostic_rival(gen, inp):
    facts = gen._analyze(inp)["facts"]
    if not facts["rectangle"]:
        return gen.rule_mirror(inp)
    wide = facts["width"] > facts["height"]
    return gen._paint_pair_lines(facts, facts["row_pairs"] if wide else (),
                                () if wide else facts["col_pairs"])


def literal(inp):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in inp) + ")"


def main():
    started = time.monotonic()
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    programs = {row["program_solution"] for line in canonical_path(ROOT).read_text().splitlines()
                if (row := json.loads(line)).get("task_id") == TASK}
    assert len(programs) == 1
    program = programs.pop()
    assert program.count(MARKER) == 2
    rival = program.replace(MARKER, REPLACEMENT)
    assert sha(" ".join(program.split()).encode()).startswith(gen.RULE_HASH)
    report = {
        "schema": "05409de4bec8-bounded-canvas-axis-rival-v1",
        "status": "running", "source_path": str(source), "source_sha256": digest,
        "rule_hash": gen.RULE_HASH, "rule_sha256": sha(program.encode()),
        "rival_sha256": sha(rival.encode()), "probe_sha256": sha(Path(__file__).read_bytes()),
        "program": program, "rival_program": rival,
        "rival": "On rectangles select orientation by canvas width > height; otherwise preserve canonical exact-pair lines.",
        "search": {"diagnostic_only": True, "seeds_budget": 32, "starts": list(range(5)),
                   "difficulty": "medium", "assembly": "3 consecutive demos + 1 consecutive query; no overrides",
                   "tried": []}, "errors": [], "racket_evaluations": 0,
        "limits": ["One rival only, at most 32 seeds, first matching 3-demo witness only.",
                   "The minimal witness has three demos; an optional preceding fourth demo is independently replayed when available.",
                   "No production rule, generator, approval, or audit-status changes; no broad battery or acceptance."]}
    found = None
    for seed in range(32):
        grids = [gen.generate(seed, i, difficulty="medium") for i in range(8)]
        for start in range(5):
            selected = grids[start:start + 4]
            agree = [diagnostic_rival(gen, inp) == gen.rule_mirror(inp) for inp in selected]
            report["search"]["tried"].append({"seed": seed, "start": start, "agreements": agree})
            if agree == [True, True, True, False]:
                found = (seed, start, selected)
                break
        if found:
            break
    (HERE / "rule.rkt").write_text(program)
    (HERE / "rival.rkt").write_text(rival)
    if found:
        seed, start, selected = found
        report.update(seed=seed, start=start, cases=[])
        bridge = None
        try:
            bridge = RacketBridge()
            report["racket"] = bridge.runtime_identity
            assert report["racket"].get("backend") == "racket"
            assert report["racket"].get("protected") is True
            for offset, inp in enumerate(selected):
                assert not gen.self_check(inp)
                outputs = []
                for code in (program, rival):
                    outputs.append(bridge.eval_text(f"({wrap_rule(code)} {literal(inp)})"))
                    report["racket_evaluations"] += 1
                assert outputs[0] == gen.rule_mirror(inp)
                assert outputs[1] == diagnostic_rival(gen, inp)
                facts = gen._analyze(inp)["facts"]
                report["cases"].append({
                    "split": "train" if offset < 3 else "test", "sample_index": start + offset,
                    "input": inp, "output": outputs[0], "rival_output": outputs[1],
                    "agree": outputs[0] == outputs[1], "self_check_errors": gen.self_check(inp),
                    "facts": {key: facts[key] for key in ("height", "width", "points", "rectangle", "row_span", "col_span")}})
            assert [row["agree"] for row in report["cases"]] == [True, True, True, False]
            if start > 0:
                inp = gen.generate(seed, start - 1, difficulty="medium")
                outputs = []
                for code in (program, rival):
                    outputs.append(bridge.eval_text(f"({wrap_rule(code)} {literal(inp)})"))
                    report["racket_evaluations"] += 1
                assert outputs[0] == gen.rule_mirror(inp)
                assert outputs[1] == diagnostic_rival(gen, inp)
                report["preceding_fourth_demo"] = {
                    "sample_index": start - 1, "input": inp, "output": outputs[0],
                    "rival_output": outputs[1], "agree": outputs[0] == outputs[1],
                    "self_check_errors": gen.self_check(inp)}
                report["four_demo_consecutive_extension_confirmed"] = outputs[0] == outputs[1]
                pairs = [{"input": row["input"], "output": row["output"]}
                         for row in [report["preceding_fourth_demo"], *report["cases"][:3]]]
                report["selected_lesson_identifiable_four_demos"] = gen.lesson_identifiable(
                    pairs, {"input": report["cases"][-1]["input"], "output": report["cases"][-1]["output"]})
            report["status"] = "confirmed_short_context_teaching_gap"
        except Exception as exc:
            report["errors"].append(f"{type(exc).__name__}: {exc}")
            report["status"] = "failed_racket_confirmation"
        finally:
            if bridge is not None:
                bridge.close()
    else:
        report["status"] = "no_witness_in_finite_search"
    report["elapsed_seconds"] = time.monotonic() - started
    (HERE / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report.get(key) for key in ("status", "seed", "start", "source_sha256", "rule_hash", "racket_evaluations", "elapsed_seconds", "errors")}))
    return bool(report["errors"])


if __name__ == "__main__":
    raise SystemExit(main())
