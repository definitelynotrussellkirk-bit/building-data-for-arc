"""Bounded count-only shortcut audit; run via the packet's protected runtime."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def main():
    root = find_root(__file__)
    out = Path(__file__).resolve().parent
    task = "e3bf7e173449"
    generator, path, generator_sha = load_selected_generator(task, root=root)
    sources = {row["program_solution"] for row in map(json.loads, canonical_path(root).read_text().splitlines())
               if row.get("task_id") == task}
    assert len(sources) == 1
    canonical = sources.pop()
    old = "(equal? src-sig (canonical-uvs (point-uvs (extract-local-points g (list-ref candidates i) (list 8) 4))))"
    new = "(= (length src-sig) (length (extract-local-points g (list-ref candidates i) (list 8) 4)))"
    assert canonical.count(old) == 1
    rival = canonical.replace(old, new, 1)
    programs = {"canonical": canonical, "count_only": rival}
    callables = {name: wrap_rule(source) for name, source in programs.items()}
    for name, source in programs.items():
        (out / (name + ".rkt")).write_text(source)
    report = {"schema": "arcpuzzles-bounded-learnability-audit-v1", "task_id": task,
              "status": "unchanged", "generator_path": str(path.relative_to(root)),
              "generator_sha256": generator_sha, "canonical_program_sha256": sha(canonical),
              "rival_program_sha256": sha(rival),
              "rival_meaning": "Choose the first candidate having the source motif's point count; ignore arrangement and rotation.",
              "probe_sha256": sha(Path(__file__).read_bytes()), "episodes_checked": 0,
              "racket_evaluations": 0, "errors": [],
              "limits": "At most24 seeds, two demonstrations and one query per seed, no alternative curricula search or training claim; wall budget110s."}
    start = time.monotonic()
    with RacketBridge(timeout=8) as bridge:
        report["runtime"] = bridge.runtime_identity
        assert report["runtime"]["backend"] == "racket" and report["runtime"]["protected"] is True
        for seed in range(24):
            if time.monotonic() - start > 110:
                report["stopped_at_budget"] = True
                break
            pairs = []
            failed = False
            for sample_index in range(3):
                grid = generator.generate(seed, sample_index)
                outputs = {}
                for name, function in callables.items():
                    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                    report["racket_evaluations"] += 1
                    try:
                        outputs[name] = normalize_grid(bridge.eval_text(f"({function} {literal})"))
                    except Exception as exc:
                        report["errors"].append({"seed": seed, "sample_index": sample_index,
                                                 "program": name, "error": str(exc)[:400]})
                        failed = True
                        break
                if failed:
                    break
                pairs.append({"input": grid, "output": outputs["canonical"],
                              "rival_output": outputs["count_only"], "sample_index": sample_index})
            if failed:
                continue
            report["episodes_checked"] += 1
            if all(pair["output"] == pair["rival_output"] for pair in pairs[:2]) and pairs[2]["output"] != pairs[2]["rival_output"]:
                witness = {"seed": seed, "train": pairs[:2], "test": pairs[2:],
                           "generator_sha256": generator_sha, "program_sha256": sha(canonical),
                           "rival_program_sha256": sha(rival),
                           "demo_fit": True, "query_disagreement": True}
                (out / "witness.json").write_text(json.dumps(witness, indent=2) + "\n")
                report.update(status="concrete_teaching_ambiguity", witness="witness.json", seed=seed)
                break
    report["elapsed_seconds"] = round(time.monotonic() - start, 3)
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "runtime"}, indent=2))


if __name__ == "__main__":
    main()
